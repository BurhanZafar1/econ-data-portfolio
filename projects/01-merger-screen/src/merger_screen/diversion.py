"""Diversion ratios and upward pricing pressure (Farrell and Shapiro, 2010).

Notation: the merger joins product 1 and product 2. D12 is the share of the unit
sales product 1 loses after a price rise that go to product 2. M2 is product 2's
percentage margin, (P2 - C2) / P2.
"""

from __future__ import annotations


def proportional_diversion(share_from: float, share_to: float, aggregate_diversion: float = 1.0) -> float:
    """Diversion ratio from one product to another, assuming diversion follows market shares.

    D12 = A * s2 / (100 - s1), where A is the aggregate diversion ratio: the fraction of
    lost sales that stay inside the market (A = 1 means no customer leaves the market).
    Shares are in percentage points; the result is a fraction between 0 and 1.
    """
    if not 0.0 <= aggregate_diversion <= 1.0:
        raise ValueError("aggregate_diversion must be between 0 and 1")
    if not 0.0 <= share_from < 100.0:
        raise ValueError("share_from must be in [0, 100)")
    return aggregate_diversion * share_to / (100.0 - share_from)


def guppi(diversion_12: float, margin_2: float, price_ratio_2_to_1: float = 1.0) -> float:
    """Gross upward pricing pressure index for product 1: D12 * M2 * (P2 / P1).

    It is the value of sales diverted to product 2, per dollar of revenue product 1
    loses, and is the ratio the 2023 Guidelines (Section 4.2.B) describe in words.
    """
    return diversion_12 * margin_2 * price_ratio_2_to_1


def net_upp_per_dollar(
    diversion_12: float,
    margin_1: float,
    margin_2: float,
    efficiency_credit: float = 0.10,
    price_ratio_2_to_1: float = 1.0,
) -> float:
    """Net upward pricing pressure on product 1 per dollar of its price.

    Farrell and Shapiro's test is D12 (P2 - C2) > E * C1. Dividing by P1 and using
    C1 / P1 = 1 - M1 gives GUPPI_1 - E * (1 - M1). A positive value flags pressure
    to raise price after crediting a standard marginal cost saving of E.
    """
    return guppi(diversion_12, margin_2, price_ratio_2_to_1) - efficiency_credit * (1.0 - margin_1)


def breakeven_margin(diversion_12: float, efficiency_credit: float = 0.10) -> float:
    """Common margin M at which net UPP is exactly zero, with equal margins and prices.

    Solving D12 * M - E * (1 - M) = 0 gives M = E / (D12 + E). Above this margin the
    merger creates net upward pricing pressure on product 1.
    """
    return efficiency_credit / (diversion_12 + efficiency_credit)
