"""Load the raw files and build the instrument panel and the factor data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from . import instruments as ins

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
AQR_DIR = ROOT / "data" / "aqr"

# EIA reports heating oil contract 1 on about 70% of trading days before 2006 and contract 2
# (from 1994) on fewer, too sparse to place rolls reliably; the series starts in 2007.
FUTURES_START = {"HO": "2007-01-01"}

ASSET_CLASS = {"EQ": "Equity indices", "FI": "Bonds", "FX": "Currencies", "CM": "Commodities"}


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / name, index_col=0, parse_dates=True)


def daily_excess_returns() -> tuple[dict[str, pd.Series], dict[str, str]]:
    """Daily excess returns of every instrument and its asset class."""
    rets: dict[str, pd.Series] = {}
    cls: dict[str, str] = {}

    eq = _read("equity_market_excess_daily_pct.csv.xz") / 100.0
    for name in eq.columns:
        rets[name] = eq[name].dropna()  # already an excess return (total return minus T-bill)
        cls[name] = "EQ"

    us = _read("us_treasury_yields_daily.csv.xz")
    # financed at the 3 month bill (published from September 1981; 1 year yield before)
    us_short = us["us_3m"].combine_first(us["us_1y"])
    for m in (2, 5, 10):
        rets[f"US {m}y note"] = ins.bond_excess_returns(us[f"us_{m}y"], us_short, m)
        cls[f"US {m}y note"] = "FI"
    dj = _read("de_jp_yields_daily.csv.xz")
    for m, label in ((2, "Schatz"), (5, "Bobl"), (10, "Bund")):
        rets[f"DE {m}y {label}"] = ins.bond_excess_returns(dj[f"de_{m}y"], dj["de_1y"], m)
        cls[f"DE {m}y {label}"] = "FI"
    rets["JP 10y JGB"] = ins.bond_excess_returns(dj["jp_10y"], dj["jp_1y"], 10)
    cls["JP 10y JGB"] = "FI"

    fx = _read("fx_usd_per_unit_daily.csv.xz")
    eur = fx["EUR"].copy()
    dem_as_eur = fx["DEM"] * 1.95583  # irrevocable conversion rate, DEM per EUR
    eur = eur.combine_first(dem_as_eur[dem_as_eur.index < "1999-01-01"])
    for ccy in ("AUD", "CAD", "JPY", "NZD", "NOK", "SEK", "CHF", "GBP"):
        rets[f"{ccy}/USD"] = ins.price_returns(fx[ccy])
        cls[f"{ccy}/USD"] = "FX"
    rets["EUR/USD"] = ins.price_returns(eur)
    cls["EUR/USD"] = "FX"

    en = _read("eia_energy_futures_daily.csv.xz")
    for code, label in (("CL", "Crude oil"), ("HO", "Heating oil"), ("NG", "Natural gas")):
        e = en.loc[FUTURES_START.get(code, None):]
        rets[label] = ins.rolled_futures_returns(e[f"{code}1"], e[f"{code}2"], code)
        cls[label] = "CM"
    return rets, cls


def factors() -> pd.DataFrame:
    """Monthly Fama-French factors (decimals). MKT, the US market excess return, stands in
    for the paper's MSCI World excess return (MSCI history before 1997 is not public)."""
    ff = pd.read_csv(RAW / "ff_factors_monthly.csv", index_col=0)
    ff.index = pd.PeriodIndex(ff.index, freq="M")
    ff["MKT"] = ff["Mkt-RF"]
    return ff


def _aqr(name: str) -> pd.DataFrame:
    sheet = pd.read_excel(AQR_DIR / name, sheet_name=0, header=None, engine="calamine")
    start = sheet.index[sheet.iloc[:, 1].astype(str).str.strip() == "TSMOM"][0]
    table = sheet.iloc[start + 1 :, :6].dropna(subset=[1])
    table.columns = ["date", "TSMOM", *[str(c) for c in sheet.iloc[start, 2:6]]]
    table["date"] = pd.to_datetime(table["date"].astype(str).str[:10], errors="coerce")
    table = table.dropna(subset=["date"])
    out = table.set_index(table["date"].dt.to_period("M")).drop(columns="date").astype(float)
    out.index.name = "month"
    return out


def aqr_original() -> pd.DataFrame:
    """TSMOM factors used in the paper, 1985 to 2009 (AQR data set)."""
    return _aqr("aqr_tsmom_original.xlsx")


def aqr_updated() -> pd.DataFrame:
    """Updated and extended TSMOM factors (AQR data set, rebuilt by AQR at each update)."""
    return _aqr("aqr_tsmom_updated.xlsx")


def aqr_checksums() -> dict[str, str]:
    """SHA256 of the AQR files now on disk."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(AQR_DIR.glob("*.xlsx"))}


def aqr_recorded_checksums() -> dict[str, str]:
    path = ROOT / "output" / "aqr_checksums_used.json"
    return json.loads(path.read_text()) if path.exists() else {}
