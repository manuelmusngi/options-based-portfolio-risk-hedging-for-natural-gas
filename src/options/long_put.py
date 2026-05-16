"""
Long Put Option Model
=====================
The gas generator acts as **option buyer** of a put option.

Mechanics (paper §4)
--------------------
Three-zone payoff structure:

  Zone 1 — S < C_gen (deep ITM):
      Generator transfers the put to a third party, earning a transfer fee.
      payoff = transfer_factor * (K − S) − premium

  Zone 2 — C_gen ≤ S < K (in-the-money / near-the-money):
      Generator exercises but cannot profitably generate.
      payoff = −premium

  Zone 3 — S ≥ K (OTM):
      Option not exercised.
      payoff = −premium

Risk profile
------------
- Downside: limited to premium paid (maximum loss = premium).
- Upside: bounded by transfer fee when S collapses below generation cost.
- Preferred by generators with HIGH risk aversion.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class LongPutResult:
    spot_prices: np.ndarray
    payoffs: np.ndarray
    zones: np.ndarray              # 1=transfer, 2=exercise no-transfer, 3=no-exercise
    transfer_revenues: np.ndarray
    premiums_paid: np.ndarray
    expected_payoff: float
    payoff_variance: float
    zone1_probability: float
    zone2_probability: float
    zone3_probability: float

    def summary(self) -> dict:
        return {
            "expected_payoff": self.expected_payoff,
            "payoff_variance": self.payoff_variance,
            "payoff_std": np.sqrt(self.payoff_variance),
            "zone1_prob (transfer)": self.zone1_probability,
            "zone2_prob (premium loss)": self.zone2_probability,
            "zone3_prob (no exercise)": self.zone3_probability,
            "min_payoff": float(self.payoffs.min()),
            "max_payoff": float(self.payoffs.max()),
        }


class LongPut:
    """
    Long Put option instrument for gas generator hedging.

    Parameters
    ----------
    strike : float              Strike price K [$/MWh].
    premium : float             Premium paid by generator [$/MWh].
    generation_cost : float     Generator marginal cost C_gen [$/MWh]. Default 70.
    transfer_price_factor : float  Transfer fee = factor*(K−S) in Zone 1. Default 0.80.
    volume_mwh : float          Contracted volume [MWh]. Default 1.
    """

    instrument_type: str = "long_put"

    def __init__(
        self,
        strike: float,
        premium: float,
        generation_cost: float = 70.0,
        transfer_price_factor: float = 0.80,
        volume_mwh: float = 1.0,
        name: str = "LongPut",
    ) -> None:
        if strike <= 0:
            raise ValueError(f"Strike must be positive, got {strike}")
        if premium < 0:
            raise ValueError(f"Premium must be non-negative, got {premium}")
        if generation_cost <= 0:
            raise ValueError(f"Generation cost must be positive, got {generation_cost}")
        if not 0 < transfer_price_factor <= 1:
            raise ValueError(f"Transfer factor must be in (0,1], got {transfer_price_factor}")
        if volume_mwh <= 0:
            raise ValueError(f"Volume must be positive, got {volume_mwh}")

        self.strike = float(strike)
        self.premium = float(premium)
        self.generation_cost = float(generation_cost)
        self.transfer_price_factor = float(transfer_price_factor)
        self.volume_mwh = float(volume_mwh)
        self.name = name

    def zone(self, spot_prices: np.ndarray) -> np.ndarray:
        """Classify prices: 1=Zone1, 2=Zone2, 3=Zone3."""
        S = np.asarray(spot_prices, dtype=float)
        z = np.full_like(S, 3, dtype=int)
        z = np.where(S < self.strike, 2, z)
        z = np.where(S < self.generation_cost, 1, z)
        return z

    def transfer_fee(self, spot_prices: np.ndarray) -> np.ndarray:
        S = np.asarray(spot_prices, dtype=float)
        in_zone1 = S < self.generation_cost
        fee = np.where(
            in_zone1,
            self.transfer_price_factor * np.maximum(self.strike - S, 0.0),
            0.0,
        )
        return fee * self.volume_mwh

    def premium_cost(self, spot_prices: np.ndarray) -> np.ndarray:
        S = np.asarray(spot_prices, dtype=float)
        return np.full_like(S, -self.premium * self.volume_mwh)

    def payoff(self, spot_prices: np.ndarray) -> np.ndarray:
        """Net payoff = transfer_fee + premium_cost."""
        S = np.asarray(spot_prices, dtype=float)
        return self.transfer_fee(S) + self.premium_cost(S)

    def is_exercised(self, spot_prices: np.ndarray) -> np.ndarray:
        S = np.asarray(spot_prices, dtype=float)
        return S < self.strike

    def evaluate(
        self,
        spot_prices: np.ndarray,
        scenario_probs: Optional[np.ndarray] = None,
    ) -> LongPutResult:
        S = np.asarray(spot_prices, dtype=float)
        flat = S.ndim == 1
        if not flat:
            payoffs_raw = self.payoff(S).sum(axis=1)
            tf_arr = self.transfer_fee(S).sum(axis=1)
            pc_arr = self.premium_cost(S).sum(axis=1)
            zones_arr = self.zone(S[:, 0])
        else:
            payoffs_raw = self.payoff(S)
            tf_arr = self.transfer_fee(S)
            pc_arr = self.premium_cost(S)
            zones_arr = self.zone(S)

        n = len(payoffs_raw)
        probs = (
            np.asarray(scenario_probs, dtype=float)
            if scenario_probs is not None
            else np.full(n, 1.0 / n)
        )
        probs = probs / probs.sum()
        exp_payoff = float(np.dot(probs, payoffs_raw))
        var_payoff = float(np.dot(probs, (payoffs_raw - exp_payoff) ** 2))
        z1_prob = float(np.dot(probs, (zones_arr == 1).astype(float)))
        z2_prob = float(np.dot(probs, (zones_arr == 2).astype(float)))

        return LongPutResult(
            spot_prices=S, payoffs=payoffs_raw, zones=zones_arr,
            transfer_revenues=tf_arr, premiums_paid=pc_arr,
            expected_payoff=exp_payoff, payoff_variance=var_payoff,
            zone1_probability=z1_prob, zone2_probability=z2_prob,
            zone3_probability=1.0 - z1_prob - z2_prob,
        )

    def transfer_breakdown(self, spot_prices: np.ndarray) -> dict:
        S = np.asarray(spot_prices, dtype=float)
        z = self.zone(S)
        return {
            "n_total": len(S),
            "n_zone1_transfer": int((z == 1).sum()),
            "n_zone2_premium_only": int((z == 2).sum()),
            "n_zone3_no_exercise": int((z == 3).sum()),
            "avg_transfer_fee": float(self.transfer_fee(S).mean()),
            "avg_premium_cost": float(abs(self.premium_cost(S).mean())),
            "avg_net_payoff": float(self.payoff(S).mean()),
        }

    def __repr__(self) -> str:
        return (
            f"LongPut(strike={self.strike}, premium={self.premium}, "
            f"gen_cost={self.generation_cost}, volume={self.volume_mwh} MWh)"
        )
