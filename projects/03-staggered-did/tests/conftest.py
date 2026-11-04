"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from staggered_did.group_time import GroupTimeResult, estimate_group_time
from staggered_did.panel import Panel, load_minimum_wage

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def panel() -> Panel:
    return load_minimum_wage(DATA / "mpdta.csv")


@pytest.fixture(scope="session")
def result(panel: Panel) -> GroupTimeResult:
    return estimate_group_time(panel)
