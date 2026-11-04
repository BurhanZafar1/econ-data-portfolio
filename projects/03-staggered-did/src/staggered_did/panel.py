"""Balanced panel container used by every estimator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Panel:
    """A balanced panel stored as arrays.

    y: outcomes, units in rows and years in columns.
    cohort: first treated year per unit, 0 if never treated in the sample.
    clusters: the level at which treatment was assigned (state here).
    covariates: optional time-invariant covariates, one column each.
    """

    y: np.ndarray
    years: np.ndarray
    cohort: np.ndarray
    units: np.ndarray
    clusters: np.ndarray
    covariates: np.ndarray | None = None

    @property
    def n_units(self) -> int:
        return self.y.shape[0]

    @property
    def groups(self) -> np.ndarray:
        """Treated cohorts, ascending."""
        return np.unique(self.cohort[self.cohort > 0])

    @property
    def treated(self) -> np.ndarray:
        """Unit by year treatment dummy."""
        is_treated = self.cohort > 0
        return (is_treated[:, None] & (self.years[None, :] >= self.cohort[:, None])).astype(float)


def _keep_units(panel: Panel, keep: np.ndarray) -> Panel:
    return replace(
        panel,
        y=panel.y[keep],
        cohort=panel.cohort[keep],
        units=panel.units[keep],
        clusters=panel.clusters[keep],
        covariates=None if panel.covariates is None else panel.covariates[keep],
    )


def drop_cohort(panel: Panel, cohort: int) -> Panel:
    """Remove every unit in one treatment cohort."""
    return _keep_units(panel, panel.cohort != cohort)


def drop_cluster(panel: Panel, cluster: int) -> Panel:
    """Remove every unit in one cluster."""
    return _keep_units(panel, panel.clusters != cluster)


def build_panel(
    frame: pd.DataFrame,
    unit: str,
    time: str,
    outcome: str,
    cohort: str,
    cluster: str,
    covariates: tuple[str, ...] = (),
) -> Panel:
    """Convert a long table to a Panel, refusing unbalanced or inconsistent input."""
    wide = frame.pivot(index=unit, columns=time, values=outcome).sort_index()
    if wide.isna().any().any():
        raise ValueError("panel is not balanced: at least one unit year is missing")
    by_unit = frame.groupby(unit)[[cohort, cluster, *covariates]]
    if (by_unit.nunique() > 1).any().any():
        raise ValueError("cohort, cluster and covariates must not vary within a unit")
    units = by_unit.first().sort_index()
    return Panel(
        y=wide.to_numpy(dtype=float),
        years=wide.columns.to_numpy(dtype=int),
        cohort=units[cohort].to_numpy(dtype=int),
        units=wide.index.to_numpy(),
        clusters=units[cluster].to_numpy(),
        covariates=units[list(covariates)].to_numpy(dtype=float) if covariates else None,
    )


def load_minimum_wage(path: Path, covariates: tuple[str, ...] = ()) -> Panel:
    """Load mpdta. The state is the leading digits of the county FIPS code."""
    frame = pd.read_csv(path)
    frame["state"] = (frame["countyreal"] // 1000).astype(int)
    return build_panel(
        frame, "countyreal", "year", "lemp", "first.treat", "state", covariates
    )
