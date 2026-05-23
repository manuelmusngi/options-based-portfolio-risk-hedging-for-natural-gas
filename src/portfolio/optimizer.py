"""
Mean-Variance Portfolio Optimizer (paper §7, Eq. 47)
=====================================================
Solves QP:  Max  w @ μ − (1/2)*A * w @ Σ @ w
            s.t. sum(w) = 1,  w ≥ 0

Uses cvxpy (OSQP/SCS) when available, falls back to scipy SLSQP.

CLI: python -m portfolio.optimiser --risk-aversion 3 --scenarios 1000
     python -m portfolio.optimiser --sweep --a-min 0 --a-max 10 --steps 21
"""

from __future__ import annotations

import sys, json, warnings
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .mean_variance import MeanVariancePortfolio, PortfolioStats

try:
    import cvxpy as cp
    _CVXPY_AVAILABLE = True
except ImportError:
    _CVXPY_AVAILABLE = False
    warnings.warn(
        "cvxpy not found. Falling back to scipy SLSQP. "
        "Install cvxpy>=1.3 for better performance.",
        ImportWarning, stacklevel=2,
    )


@dataclass
class OptimizationResult:
    weights: np.ndarray
    instrument_names: List[str]
    expected_return: float
    variance: float
    utility: float
    risk_aversion: float
    solver_status: str = "optimal"
    solver_backend: str = "cvxpy"
    n_scenarios: int = 0

    def weight_dict(self) -> Dict[str, float]:
        return {n: float(w) for n, w in zip(self.instrument_names, self.weights)}

    def __str__(self) -> str:
        lines = [
            "OptimizationResult", "=" * 42,
            f"  Risk aversion A  : {self.risk_aversion:.2f}",
            f"  E[return]        : {self.expected_return:+.6f}",
            f"  Std dev          : {np.sqrt(max(self.variance, 0)):.6f}",
            f"  Utility U        : {self.utility:+.6f}",
            f"  Solver           : {self.solver_backend} [{self.solver_status}]",
            f"  Scenarios        : {self.n_scenarios}",
            "  Optimal Weights:",
        ]
        for name, w in zip(self.instrument_names, self.weights):
            bar = "█" * int(round(w * 20))
            lines.append(f"    {name:<22s}: {w:6.4f}  {w:5.1%}  {bar}")
        return "\n".join(lines)


class MeanVarianceOptimizer:
    """
    Portfolio optimizer for the gas generator hedging problem.

    Parameters
    ----------
    instruments : list
        Instrument objects (ShortPut, LongPut, ShortCall, PowerToGas, Battery).
        Each must expose a .payoff(spot_prices) method.
    risk_aversion : float   Default A. Default 3.0.
    n_scenarios : int       Monte Carlo scenarios. Default 1000.
    random_seed : int       Reproducibility seed. Default 42.
    spot_prices : ndarray   Pre-generated (n_scenarios, n_slots) prices. Optional.
    scenario_probs : ndarray Scenario probabilities. Default: uniform.
    slot_hours : float      Slot duration [h]. Default 0.5.
    """

    def __init__(
        self,
        instruments: List[Any],
        risk_aversion: float = 3.0,
        n_scenarios: int = 1000,
        random_seed: int = 42,
        scenario_generator: Optional[Any] = None,
        spot_prices: Optional[np.ndarray] = None,
        scenario_probs: Optional[np.ndarray] = None,
        slot_hours: float = 0.5,
    ) -> None:
        self.instruments = instruments
        self.instrument_names = [inst.name for inst in instruments]
        self.n_instruments = len(instruments)
        self.default_risk_aversion = float(risk_aversion)
        self.n_scenarios = n_scenarios
        self.random_seed = random_seed
        self.slot_hours = slot_hours
        self._spot_prices = spot_prices
        self._scenario_probs = scenario_probs
        self._sg = scenario_generator
        self._return_matrix = None
        self._mv = None
        self._is_built = False

    def _generate_scenarios(self) -> np.ndarray:
        if self._spot_prices is not None:
            return self._spot_prices
        if self._sg is not None:
            scenarios = self._sg.generate(n_scenarios=self.n_scenarios, seed=self.random_seed)
            return scenarios.prices
        # Fallback: log-normal
        rng = np.random.default_rng(self.random_seed)
        mu_ln = np.log(80.0) - 0.5 * (20.0 / 80.0) ** 2
        sigma_ln = 20.0 / 80.0
        prices = rng.lognormal(mean=mu_ln, sigma=sigma_ln, size=(self.n_scenarios, 48))
        return np.clip(prices, 10.0, 250.0)

    def _compute_instrument_returns(self, spot_prices: np.ndarray) -> np.ndarray:
        n_scen = spot_prices.shape[0]
        R = np.zeros((n_scen, self.n_instruments))
        for j, inst in enumerate(self.instruments):
            inst_type = getattr(inst, "instrument_type", "unknown")
            if inst_type in ("short_put", "long_put", "short_call"):
                raw = inst.payoff(spot_prices)
                R[:, j] = raw.sum(axis=1)
            elif inst_type == "p2g":
                gas_price_proxy = 0.60 * spot_prices
                excess = np.maximum(
                    inst.strike if hasattr(inst, "strike") else 80.0 - spot_prices, 0.0
                )
                absorbed = np.minimum(excess, inst.max_charge_rate_mw * self.slot_hours)
                R[:, j] = (absorbed * inst.efficiency * gas_price_proxy).sum(axis=1) * 0.01
            elif inst_type == "battery":
                prices_sorted = np.sort(spot_prices, axis=1)
                n_slots = spot_prices.shape[1]
                low_idx = n_slots // 4
                high_idx = 3 * n_slots // 4
                spread = np.maximum(
                    prices_sorted[:, high_idx:].mean(axis=1)
                    - prices_sorted[:, :low_idx].mean(axis=1), 0.0
                )
                R[:, j] = spread * 1.0 * inst.capacity_mwh * inst.round_trip_efficiency * 0.01
            else:
                try:
                    raw = inst.payoff(spot_prices)
                    R[:, j] = raw.sum(axis=1) if raw.ndim == 2 else raw
                except Exception:
                    R[:, j] = 0.0
        return R

    def build(self) -> "MeanVarianceOptimiser":
        spot_prices = self._generate_scenarios()
        R = self._compute_instrument_returns(spot_prices)
        self._return_matrix = R
        probs = (
            self._scenario_probs
            if self._scenario_probs is not None
            else np.full(R.shape[0], 1.0 / R.shape[0])
        )
        self._mv = MeanVariancePortfolio(
            instrument_names=self.instrument_names, scenario_probs=probs
        )
        self._mv.fit(R, probs)
        self._is_built = True
        return self

    def _solve_cvxpy(self, A: float) -> OptimizationResult:
        mu = self._mv.mu
        sigma = self._mv.sigma
        n = self.n_instruments
        w = cp.Variable(n, nonneg=True)
        utility = mu @ w - 0.5 * A * cp.quad_form(w, sigma)
        prob = cp.Problem(cp.Maximize(utility), [cp.sum(w) == 1])
        try:
            prob.solve(solver=cp.OSQP, warm_start=True, eps_abs=1e-6, eps_rel=1e-6)
            if prob.status not in ("optimal", "optimal_inaccurate"):
                prob.solve(solver=cp.SCS)
            status = prob.status or "unknown"
            weights = np.array(w.value) if w.value is not None else np.ones(n) / n
        except Exception as e:
            warnings.warn(f"cvxpy failed: {e}. Using equal weights.")
            weights = np.ones(n) / n
            status = "failed"

        weights = np.clip(weights, 0.0, 1.0)
        weights /= weights.sum()
        stats = self._mv.stats(weights, A)
        return OptimizationResult(
            weights=weights, instrument_names=self.instrument_names,
            expected_return=stats.expected_return, variance=stats.variance,
            utility=stats.utility, risk_aversion=A,
            solver_status=status, solver_backend="cvxpy",
            n_scenarios=self._return_matrix.shape[0],
        )

    def _solve_scipy(self, A: float) -> OptimizationResult:
        from scipy.optimize import minimize
        mu = self._mv.mu
        sigma = self._mv.sigma
        n = self.n_instruments

        def neg_utility(w): return -(w @ mu - 0.5 * A * w @ sigma @ w)
        def neg_utility_grad(w): return -(mu - A * sigma @ w)

        try:
            res = minimize(
                neg_utility, np.ones(n) / n, jac=neg_utility_grad,
                method="SLSQP",
                bounds=[(0.0, 1.0)] * n,
                constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                options={"ftol": 1e-9, "maxiter": 1000},
            )
            weights = res.x
            status = "optimal" if res.success else "suboptimal"
        except Exception as e:
            warnings.warn(f"scipy SLSQP failed: {e}. Using equal weights.")
            weights = np.ones(n) / n
            status = "failed"

        weights = np.clip(weights, 0.0, 1.0)
        weights /= weights.sum()
        stats = self._mv.stats(weights, A)
        return OptimizationResult(
            weights=weights, instrument_names=self.instrument_names,
            expected_return=stats.expected_return, variance=stats.variance,
            utility=stats.utility, risk_aversion=A,
            solver_status=status, solver_backend="scipy",
            n_scenarios=self._return_matrix.shape[0],
        )

    def solve(
        self,
        risk_aversion: Optional[float] = None,
        instruments: Optional[List[Any]] = None,
        rebuild: bool = False,
    ) -> OptimisationResult:
        A = self.default_risk_aversion if risk_aversion is None else float(risk_aversion)
        if instruments is not None:
            sub = MeanVarianceOptimiser(
                instruments=instruments, risk_aversion=A,
                n_scenarios=self.n_scenarios, random_seed=self.random_seed,
                spot_prices=self._spot_prices, scenario_probs=self._scenario_probs,
                slot_hours=self.slot_hours,
            )
            return sub.solve()
        if not self._is_built or rebuild:
            self.build()
        return self._solve_cvxpy(A) if _CVXPY_AVAILABLE else self._solve_scipy(A)

    def sweep(self, a_min=0.0, a_max=10.0, steps=21) -> List[OptimizationResult]:
        if not self._is_built:
            self.build()
        return [self.solve(risk_aversion=float(a)) for a in np.linspace(a_min, a_max, steps)]

    @property
    def mv_model(self) -> MeanVariancePortfolio:
        if not self._is_built:
            self.build()
        return self._mv

    @property
    def return_matrix(self) -> np.ndarray:
        if not self._is_built:
            self.build()
        return self._return_matrix
