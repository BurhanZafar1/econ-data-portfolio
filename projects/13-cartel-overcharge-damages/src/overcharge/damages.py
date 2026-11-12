"""Turn an overcharge estimate into dollar damages.

Overcharge damages to direct purchasers are the sum over affected weeks of
(actual price - but for price) * quantity bought (ABA Section of Antitrust
Law 2017; European Commission 2013). The volume effect, the shipments buyers
gave up because of the higher price, is a separate head of harm and is
reported apart from the overcharge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from overcharge.data import LBS_PER_TON, PRICE_UNIT_LBS

CWT_PER_TON = LBS_PER_TON / PRICE_UNIT_LBS  # 20 hundredweights in a ton


def overcharge_damages(cartel_weeks: pd.DataFrame, but_for_price: pd.Series) -> float:
    """Dollars overpaid in the cartel weeks, given a but for price per week."""
    gap = cartel_weeks["price"] - but_for_price
    return float((gap * cartel_weeks["quantity"] * CWT_PER_TON).sum())


def damages_from_log_overcharge(cartel_weeks: pd.DataFrame, b: float) -> float:
    """Damages when the but for price is P * exp(-b) in every cartel week.

    This equals affected commerce times the overcharge as a share of the
    actual price, 1 - exp(-b).
    """
    return float(cartel_weeks["revenue"].sum() * (1 - np.exp(-b)))


@dataclass(frozen=True)
class VolumeEffect:
    """Shipments lost to the higher price and the associated deadweight loss."""

    lost_tons: float
    lost_pct: float
    deadweight_loss: float


def volume_effect(cartel_weeks: pd.DataFrame, b: float, elasticity: float) -> VolumeEffect:
    """Constant elasticity demand: Q_but_for = Q * (P_but_for / P) ** elasticity.

    The deadweight loss uses the triangle approximation
    0.5 * (P - P_but_for) * (Q_but_for - Q) for each week.
    """
    price_ratio = np.exp(-b)  # P_but_for / P
    quantity = cartel_weeks["quantity"]
    but_for_quantity = quantity * price_ratio**elasticity
    lost = but_for_quantity - quantity
    gap = cartel_weeks["price"] * (1 - price_ratio)
    dwl = 0.5 * gap * lost * CWT_PER_TON
    return VolumeEffect(
        lost_tons=float(lost.sum()),
        lost_pct=float(lost.sum() / quantity.sum()),
        deadweight_loss=float(dwl.sum()),
    )
