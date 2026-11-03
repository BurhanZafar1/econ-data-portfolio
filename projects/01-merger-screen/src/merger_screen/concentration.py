"""Concentration measures and the structural presumption of the 2023 Merger Guidelines.

All market shares are in percentage points (0 to 100), so the HHI runs from
near 0 (atomistic market) to 10,000 (monopoly), the scale the Guidelines use.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Thresholds from Guideline 1 (Section 2.1) of the 2023 Merger Guidelines.
HIGHLY_CONCENTRATED_HHI = 1800.0
SIGNIFICANT_HHI_INCREASE = 100.0
MERGED_SHARE_THRESHOLD = 30.0


def hhi(shares: Iterable[float]) -> float:
    """Herfindahl-Hirschman Index: the sum of squared market shares (in points)."""
    return float(sum(s * s for s in shares))


def delta_hhi(share_a: float, share_b: float) -> float:
    """Change in HHI when firms with shares a and b combine: (a + b)^2 - a^2 - b^2 = 2ab."""
    return 2.0 * share_a * share_b


def delta_hhi_rounding_range(share_a: float, share_b: float, precision: float = 0.1) -> tuple[float, float]:
    """Smallest and largest change in HHI consistent with shares rounded to `precision`.

    Court opinions print shares to one decimal, so a true share of 15.6 could be
    anything from 15.55 to 15.65. This shows whether a result near 100 is robust.
    """
    half = precision / 2.0
    low = delta_hhi(max(0.0, share_a - half), max(0.0, share_b - half))
    return low, delta_hhi(share_a + half, share_b + half)


def fringe_share(named_shares: Iterable[float]) -> float:
    """Share not assigned to any named firm (100 minus the named shares, never negative)."""
    return max(0.0, 100.0 - float(sum(named_shares)))


def hhi_bounds(named_shares: Iterable[float]) -> tuple[float, float]:
    """Lower and upper bound on the HHI when some share is held by unnamed fringe firms.

    Lower bound: the fringe is split among many tiny firms, so it adds almost nothing.
    Upper bound: the whole fringe is one firm, so it adds fringe squared.
    """
    shares = list(named_shares)
    lower = hhi(shares)
    return lower, lower + fringe_share(shares) ** 2


@dataclass(frozen=True)
class PresumptionResult:
    """Which of the two structural tests in Guideline 1 a merger trips."""

    post_hhi: float
    delta_hhi: float
    merged_share: float
    highly_concentrated: bool
    significant_increase: bool
    hhi_test: bool
    share_test: bool

    @property
    def presumed_illegal(self) -> bool:
        """True when either structural test is met (the presumption is rebuttable)."""
        return self.hhi_test or self.share_test


def structural_presumption(post_hhi: float, change_in_hhi: float, merged_share: float) -> PresumptionResult:
    """Apply the 2023 Merger Guidelines structural presumption.

    Test 1: post merger HHI greater than 1,800 AND change in HHI greater than 100.
    Test 2: merged firm share greater than 30 percent AND change in HHI greater than 100.
    Both thresholds are strict inequalities, as in the Guidelines text.
    """
    highly_concentrated = post_hhi > HIGHLY_CONCENTRATED_HHI
    significant_increase = change_in_hhi > SIGNIFICANT_HHI_INCREASE
    return PresumptionResult(
        post_hhi=post_hhi,
        delta_hhi=change_in_hhi,
        merged_share=merged_share,
        highly_concentrated=highly_concentrated,
        significant_increase=significant_increase,
        hhi_test=highly_concentrated and significant_increase,
        share_test=merged_share > MERGED_SHARE_THRESHOLD and significant_increase,
    )
