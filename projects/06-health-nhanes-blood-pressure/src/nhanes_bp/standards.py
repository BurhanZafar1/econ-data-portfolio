"""Standard populations for direct age standardization.

WHO World Standard (2000-2025 average world population), Table 4 of
Ahmad OB, Boschi-Pinto C, Lopez AD, Murray CJL, Lozano R, Inoue M (2001).
Age standardization of rates: a new WHO standard. GPE Discussion Paper 31.
Percent of population in each five year group; the published column is
rounded and adds to 100.035.

US 2000 projected population (thousands), Table 1 of Klein RJ, Schoenborn CA
(2001). Age adjustment using the 2000 projected U.S. population. Healthy
People 2010 Statistical Notes 20. Used by NCHS for NHANES data briefs.
"""

from __future__ import annotations

import math

import pandas as pd

# (lower age, upper age inclusive) -> percent. 100+ is stored as (100, 200).
WHO_2000_2025: dict[tuple[int, int], float] = {
    (0, 4): 8.86, (5, 9): 8.69, (10, 14): 8.60, (15, 19): 8.47,
    (20, 24): 8.22, (25, 29): 7.93, (30, 34): 7.61, (35, 39): 7.15,
    (40, 44): 6.59, (45, 49): 6.04, (50, 54): 5.37, (55, 59): 4.55,
    (60, 64): 3.72, (65, 69): 2.96, (70, 74): 2.21, (75, 79): 1.52,
    (80, 84): 0.91, (85, 89): 0.44, (90, 94): 0.15, (95, 99): 0.04,
    (100, 200): 0.005,
}

# Adult rows of the NCHS master list, population in thousands.
US_2000_ADULT: dict[tuple[int, int], int] = {
    (18, 19): 8_001, (20, 24): 18_257, (25, 29): 17_722, (30, 34): 19_511,
    (35, 39): 22_180, (40, 44): 22_479, (45, 49): 19_806, (50, 54): 17_224,
    (55, 59): 13_307, (60, 64): 10_654, (65, 69): 9_410, (70, 74): 8_726,
    (75, 79): 7_415, (80, 84): 4_900, (85, 200): 4_259,
}


def aggregate_weights(table: dict[tuple[int, int], float], groups: list[tuple[int, int]]) -> pd.Series:
    """Collapse a fine standard into analysis age groups and rescale to sum to 1.

    Every fine band must fall wholly inside one analysis group or wholly
    outside all of them, so no band is split by assumption.
    """
    totals = {g: 0.0 for g in groups}
    for (lo, hi), value in table.items():
        hits = [g for g in groups if g[0] <= lo and hi <= g[1]]
        partial = [g for g in groups if not (hi < g[0] or lo > g[1])]
        if len(partial) > len(hits):
            raise ValueError(f"Standard band {lo}-{hi} straddles an analysis group boundary")
        if hits:
            totals[hits[0]] += value
    weights = pd.Series(totals, dtype=float)
    weights.index = [group_label(g) for g in groups]
    weights = weights / weights.sum()
    assert math.isclose(weights.sum(), 1.0)
    return weights


def group_label(group: tuple[int, int]) -> str:
    lo, hi = group
    return f"{lo}+" if hi >= 120 else f"{lo}-{hi}"


def assign_age_group(age: pd.Series, groups: list[tuple[int, int]]) -> pd.Series:
    """Label each age with its analysis group (empty string if outside every group)."""
    out = pd.Series("", index=age.index, dtype="object")
    for g in groups:
        out[(age >= g[0]) & (age <= g[1])] = group_label(g)
    return out


# Analysis groupings used in this project.
WHO_ADULT_GROUPS: list[tuple[int, int]] = [
    (20, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 200),
]
NCHS_GROUPS: list[tuple[int, int]] = [(18, 39), (40, 59), (60, 200)]
