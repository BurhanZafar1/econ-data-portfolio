"""State self reported hypertension by age group from the CDC BRFSS prevalence data.

Source: "Behavioral Risk Factor Surveillance System (BRFSS) Prevalence Data
(2011 to present)", data.cdc.gov dataset dttw-5yxu, topic "High Blood
Pressure", question "Adults who have been told they have high blood pressure".
BRFSS asks this in odd years. CDC publishes weighted crude prevalence with a
95% confidence interval for each state and age group.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Sequence

import numpy as np
import pandas as pd

API = "https://data.cdc.gov/resource/dttw-5yxu.json"
YEARS: tuple[int, ...] = (2011, 2013, 2015, 2017)  # within the NHANES 1999-2018 span
# 50 states plus DC; territories and the "US" median row are excluded.
STATES: tuple[str, ...] = (
    "AK AL AR AZ CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE "
    "NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY"
).split()


def fetch(years: Sequence[int] = YEARS) -> pd.DataFrame:
    """Download state by age group rows (response Yes) from the CDC Socrata API."""
    year_list = ",".join(f"'{y}'" for y in years)
    query = {
        "$select": "year,locationabbr,break_out,data_value,confidence_limit_low,confidence_limit_high,sample_size",
        "$where": (
            "topic='High Blood Pressure' AND response='Yes' AND break_out_category='Age Group' "
            f"AND data_value_type='Crude Prevalence' AND year in({year_list})"
        ),
        "$limit": "50000",
    }
    url = f"{API}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url, headers={"User-Agent": "htn-crosswalk/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        rows = json.loads(response.read())
    frame = pd.DataFrame(rows).rename(
        columns={
            "locationabbr": "state",
            "break_out": "age_group",
            "data_value": "prevalence_pct",
            "confidence_limit_low": "lower_pct",
            "confidence_limit_high": "upper_pct",
            "sample_size": "n_yes",
        }
    )
    frame = frame[frame["state"].isin(STATES)]
    for col in ("year", "n_yes"):
        frame[col] = frame[col].astype(int)
    for col in ("prevalence_pct", "lower_pct", "upper_pct"):
        frame[col] = frame[col].astype(float)
    return frame.sort_values(["year", "state", "age_group"]).reset_index(drop=True)


def to_proportions(frame: pd.DataFrame) -> pd.DataFrame:
    """Proportion and standard error, recovered from the published symmetric 95% interval."""
    out = frame.copy()
    out["p_self"] = out["prevalence_pct"] / 100
    out["se_self"] = (out["upper_pct"] - out["lower_pct"]) / 100 / (2 * 1.96)
    out["mid_year"] = out["year"] + 0.5
    return out


def time_matched_cycles(year: int, cycle_labels: Sequence[str], window: int | None) -> list[str]:
    """NHANES cycles that start in or before the BRFSS year: the latest `window`, or all if None."""
    eligible = sorted(c for c in cycle_labels if int(c[:4]) <= year)
    keep = len(eligible) if window is None else window
    if not eligible or len(eligible) < keep:
        raise ValueError(f"Not enough NHANES cycles before {year}")
    return eligible[-keep:]


def plausible(frame: pd.DataFrame) -> np.ndarray:
    """Rows whose published interval contains the estimate and is not degenerate."""
    return (
        (frame["lower_pct"] <= frame["prevalence_pct"])
        & (frame["prevalence_pct"] <= frame["upper_pct"])
        & (frame["upper_pct"] > frame["lower_pct"])
        & (frame["prevalence_pct"] > 0)
        & (frame["prevalence_pct"] < 100)
    ).to_numpy()
