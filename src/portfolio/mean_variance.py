"""
Mean-Variance Portfolio Model (paper §7, Equation 47)
======================================================
  Max  U(w) = E[r_portfolio(T)] − (1/2) * A * Var[r_portfolio(T)]

Computes μ, Σ, E[r], Var[r], and utility for any weight vector w.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class PortfolioStats:
    weights: np.ndarray
    instrument_names: List[str]
    expected_return: float
    variance: float
    std_dev: float
    utility: float
    risk_aversion: float
    instrument_expected_returns: np.ndarray
    instrument_variances: np.ndarray
    covariance_matrix: np.ndarray

    def summary(self) -> dict:
        d = {
            "expected_return": self.expected_return,
            "variance": self.variance,
            "std_dev": self.std_dev,
            "utility (A={:.1f})".format(self.risk_aversion): self.utility,
            "risk_aversion": self.risk_aversion,
        }
        for i, name in enumerate(self.instrument_names):
            d[f"w_{name}"] = float(self.weights[i])
        return d

    def __str__(self) -> str:
        lines = ["Portfolio Statistics", "=" * 40]
        lines.append(f"  Risk aversion A   : {self.risk_aversion:.2f}")
        lines.append(f"  E[return]         : {self.expected_return:+.4f}")
        lines.append(f"  Std dev           : {self.std_dev:.4f}")
        lines.append(f"  Variance          : {self.variance:.6f}")
        lines.append(f"  Utility U         : {self.utility:+.4f}")
        lines.append("  Weights:")
        for name, w in zip(self.instrument_names, self.weights):
            lines.append(f"    {name:<20s}: {w:.4f}  ({w:.1%})")
        return "\n".join(lines)


class MeanVariancePortfolio:
    """
    Mean-variance utility calculator.

    Given return matrix R (n_scenarios × n_instruments) and probs p:
      μ_i   = p @ R[:, i]
      Σ     = weighted covariance (n_inst × n_inst)
      μ_p   = w @ μ
      var_p = w @ Σ @ w
      U     = μ_p − 0.5 * A * var_p
    """

    def __init__(
        self,
        instrument_names: List[str],
        scenario_probs: Optional[np.ndarray] = None,
    ) -> None:
        self.instrument_names = list(instrument_names)
        self.n_instruments = len(instrument_names)
        self._probs = scenario_probs
        self._returns = None
        self._mu = None
        self._sigma = None

    def fit(
        self,
        return_matrix: np.ndarray,
        scenario_probs: Optional[np.ndarray] = None,
    ) -> "MeanVariancePortfolio":
        R = np.asarray(return_matrix, dtype=float)
        if R.ndim != 2:
            raise ValueError(f"return_matrix must be 2-D, got shape {R.shape}")
        n_scen, n_inst = R.shape
        if n_inst != self.n_instruments:
            raise ValueError(f"return_matrix has {n_inst} cols but {self.n_instruments} defined")

        if scenario_probs is not None:
            self._probs = np.asarray(scenario_probs, dtype=float)
        if self._probs is None:
            self._probs = np.full(n_scen, 1.0 / n_scen)

        p = self._probs / self._probs.sum()
        self._mu = p @ R
        diffs = R - self._mu[np.newaxis, :]
        self._sigma = (diffs * p[:, np.newaxis]).T @ diffs
        self._returns = R
        return self

    def _check_fitted(self) -> None:
        if self._mu is None:
            raise RuntimeError("Call fit() before computing statistics.")

    def expected_return(self, weights: np.ndarray) -> float:
        self._check_fitted()
        return float(np.asarray(weights, dtype=float) @ self._mu)

    def variance(self, weights: np.ndarray) -> float:
        self._check_fitted()
        w = np.asarray(weights, dtype=float)
        return float(w @ self._sigma @ w)

    def utility(self, weights: np.ndarray, risk_aversion: float) -> float:
        """U = E[r] − 0.5 * A * Var[r]"""
        return self.expected_return(weights) - 0.5 * risk_aversion * self.variance(weights)

    def stats(self, weights: np.ndarray, risk_aversion: float) -> PortfolioStats:
        self._check_fitted()
        w = np.asarray(weights, dtype=float)
        mu_p = self.expected_return(w)
        var_p = self.variance(w)
        return PortfolioStats(
            weights=w, instrument_names=self.instrument_names,
            expected_return=mu_p, variance=var_p,
            std_dev=float(np.sqrt(max(var_p, 0))),
            utility=mu_p - 0.5 * risk_aversion * var_p,
            risk_aversion=risk_aversion,
            instrument_expected_returns=self._mu.copy(),
            instrument_variances=np.diag(self._sigma).copy(),
            covariance_matrix=self._sigma.copy(),
        )

    @property
    def mu(self) -> np.ndarray:
        self._check_fitted()
        return self._mu.copy()

    @property
    def sigma(self) -> np.ndarray:
        self._check_fitted()
        return self._sigma.copy()

    @property
    def correlation_matrix(self) -> np.ndarray:
        self._check_fitted()
        std = np.sqrt(np.diag(self._sigma))
        outer = np.outer(std, std)
        outer[outer == 0] = 1e-12
        return self._sigma / outer

    def __repr__(self) -> str:
        fitted = "fitted" if self._mu is not None else "not fitted"
        return (
            f"MeanVariancePortfolio({self.n_instruments} instruments, {fitted})\n"
            f"  Instruments: {self.instrument_names}"
        )
