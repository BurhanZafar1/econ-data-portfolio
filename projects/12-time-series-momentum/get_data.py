"""Download every input used by run.py.

Public sources, no login:
  * AQR Capital Management data sets (copyright Moskowitz, Ooi and Pedersen):
    "Time Series Momentum: Original Paper Data" (the factor returns used in the paper,
    1985 to 2009) and "Time Series Momentum: Factors, Monthly" (updated and extended).
    These two files are NOT redistributed in this repository; they are downloaded to
    data/aqr (git ignored) and their SHA256 checksums are printed and stored in
    data/aqr/checksums.json.
  * Federal Reserve Board: H.15 Treasury constant maturity yields (Data Download
    Program) and H.10 historical noon buying rates in New York (daily, from 1971).
  * Deutsche Bundesbank: 1 and 10 year yields on listed Federal securities (Svensson).
  * Ministry of Finance Japan: JGB constant maturity yields.
  * US Energy Information Administration: NYMEX futures, contracts 1 and 2 (crude oil,
    heating oil, natural gas). EIA stopped publishing these in April 2024.
  * Kenneth R. French Data Library: daily market excess returns for the US (CRSP) and
    for Europe, Japan and Asia Pacific ex Japan (Bloomberg based, in US dollars), and
    monthly Fama-French factors and momentum (UMD).

Run:  python get_data.py aqr      (only the AQR files; the other raw files are committed)
      python get_data.py          (everything; public sources revise history, so numbers can move)
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
AQR_DIR = ROOT / "data" / "aqr"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
START = "1975-01-01"  # first day kept; leaves room for 48 month look backs before 1985
END = "2026-10-31"  # last day used from every daily source

AQR = {
    "aqr_tsmom_original.xlsx": "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Original-Paper-Data.xlsx",
    "aqr_tsmom_updated.xlsx": "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx",
}
# Daily market excess returns used as equity index futures substitutes (French library).
EQUITY = {
    "US equity market": "F-F_Research_Data_Factors_daily",
    "Europe equity market": "Europe_3_Factors_Daily",
    "Japan equity market": "Japan_3_Factors_Daily",
    "Asia Pacific ex Japan equity market": "Asia_Pacific_ex_Japan_3_Factors_Daily",
}
H15 = (
    "https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78"
    "&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn"
)
H10 = "https://www.federalreserve.gov/releases/h10/hist/dat{era}_{code}.htm"
# H.10 codes; "usd_per" means the rate is quoted in US dollars per unit of the currency.
FX = {
    "AUD": ("al", True),
    "CAD": ("ca", False),
    "EUR": ("eu", True),
    "DEM": ("ge", False),
    "JPY": ("ja", False),
    "NZD": ("nz", True),
    "NOK": ("no", False),
    "SEK": ("sd", False),
    "CHF": ("sz", False),
    "GBP": ("uk", True),
}
BUNDESBANK = "https://api.statistiken.bundesbank.de/rest/download/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.{m}.R.A.A._Z._Z.A?format=csv&lang=en"
MOF = [
    "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv",
    "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv",
]
EIA = {
    "CL1": "https://www.eia.gov/dnav/pet/hist_xls/RCLC1d.xls",
    "CL2": "https://www.eia.gov/dnav/pet/hist_xls/RCLC2d.xls",
    "HO1": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2F_PE1_Y35NY_DPGd.xls",
    "HO2": "https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2F_PE2_Y35NY_DPGd.xls",
    "NG1": "https://www.eia.gov/dnav/ng/hist_xls/RNGC1d.xls",
    "NG2": "https://www.eia.gov/dnav/ng/hist_xls/RNGC2d.xls",
}
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"


def _get(url: str, tries: int = 6) -> bytes:
    for k in range(tries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=180) as response:
                body = response.read()
            if body:
                return body
        except Exception:  # network hiccups and rate limits: wait and retry
            if k == tries - 1:
                raise
        time.sleep(5 * (k + 1))
    raise RuntimeError(f"empty response from {url}")


def aqr() -> None:
    AQR_DIR.mkdir(parents=True, exist_ok=True)
    sums = {}
    for name, url in AQR.items():
        body = _get(url)
        (AQR_DIR / name).write_bytes(body)
        sums[name] = hashlib.sha256(body).hexdigest()
        print(f"{name}: sha256 {sums[name]}")
    (AQR_DIR / "checksums.json").write_text(json.dumps(sums, indent=2) + "\n")


def equities() -> None:
    cols = {}
    for name, file in EQUITY.items():
        frame = _french_table(_french(file), date_len=8)
        s = frame["Mkt-RF"].where(frame["Mkt-RF"] > -99.0)  # -99.99 marks missing data
        s.index = pd.to_datetime(s.index, format="%Y%m%d")
        cols[name] = s
    frame = pd.DataFrame(cols).loc[START:END]
    frame.index.name = "date"
    frame.to_csv(RAW / "equity_market_excess_daily_pct.csv.xz")


def treasuries() -> None:
    text = _get(H15).decode("utf-8")
    frame = pd.read_csv(io.StringIO(text), skiprows=5)
    frame.columns = ["date"] + list(frame.columns[1:])
    keep = {
        "RIFLGFCM03_N.B": "us_3m",
        "RIFLGFCY01_N.B": "us_1y",
        "RIFLGFCY02_N.B": "us_2y",
        "RIFLGFCY05_N.B": "us_5y",
        "RIFLGFCY10_N.B": "us_10y",
    }
    frame = frame[["date"] + list(keep)].rename(columns=keep)
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.set_index("date").apply(pd.to_numeric, errors="coerce").dropna(how="all")
    frame.loc[START:END].to_csv(RAW / "us_treasury_yields_daily.csv.xz")


def _h10_page(code: str, era: str) -> pd.Series:
    html = _get(H10.format(era=era, code=code)).decode("latin-1")
    rows = re.findall(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", html, flags=re.S)
    out = {}
    for d, v in rows:
        d = re.sub(r"<[^>]+>|&nbsp;", "", d).strip()
        v = re.sub(r"<[^>]+>|&nbsp;", "", v).strip()
        try:
            out[pd.to_datetime(d, format="%d-%b-%y")] = float(v)
        except ValueError:
            continue  # "ND" (no data) rows
    s = pd.Series(out, dtype=float).sort_index()
    if s.empty:
        raise RuntimeError(f"no rows parsed from H.10 page {code} {era}")
    time.sleep(1)
    return s


def fx() -> None:
    cols = {}
    for ccy, (code, usd_per) in FX.items():
        eras = ["89", "96", "00"] if ccy not in ("EUR", "DEM") else (["96", "00"] if ccy == "EUR" else ["89", "96"])
        s = pd.concat([_h10_page(code, e) for e in eras]).sort_index()
        s = s[~s.index.duplicated(keep="last")]
        cols[ccy] = s if usd_per else 1.0 / s  # store everything as USD per unit of currency
    frame = pd.DataFrame(cols).loc[START:END]
    frame.index.name = "date"
    frame.round(8).to_csv(RAW / "fx_usd_per_unit_daily.csv.xz")


def _bundesbank(m: str) -> pd.Series:
    text = _get(BUNDESBANK.format(m=m)).decode("utf-8-sig")
    rows = [line.split(",") for line in text.splitlines() if re.match(r"^\d{4}-\d{2}-\d{2},", line)]
    s = pd.Series({pd.Timestamp(r[0]): r[1] for r in rows})
    return pd.to_numeric(s, errors="coerce").dropna()


def foreign_bonds() -> None:
    de = pd.DataFrame({f"de_{m}y": _bundesbank(f"R{m:02d}XX") for m in (1, 2, 5, 10)})
    frames = []
    for url in MOF:
        text = _get(url).decode("latin-1")
        lines = [line for line in text.splitlines() if re.match(r"^\d{4}/\d{1,2}/\d{1,2},", line)]
        rows = [line.split(",") for line in lines]
        frames.append(pd.DataFrame({"date": [r[0] for r in rows], "jp_1y": [r[1] for r in rows], "jp_10y": [r[10] for r in rows]}))
    jp = pd.concat(frames)
    jp["date"] = pd.to_datetime(jp["date"], format="%Y/%m/%d")
    jp = jp.drop_duplicates("date", keep="last").set_index("date").apply(pd.to_numeric, errors="coerce")
    frame = de.join(jp, how="outer").sort_index().loc[START:END]
    frame.index.name = "date"
    frame.to_csv(RAW / "de_jp_yields_daily.csv.xz")


def energy() -> None:
    cols = {}
    for name, url in EIA.items():
        sheet = pd.read_excel(io.BytesIO(_get(url)), sheet_name="Data 1", header=2, engine="calamine")
        sheet.columns = ["date", "price"]
        sheet["date"] = pd.to_datetime(sheet["date"])
        cols[name] = pd.to_numeric(sheet.set_index("date")["price"], errors="coerce")
    frame = pd.DataFrame(cols).loc[START:END]
    frame.index.name = "date"
    frame.to_csv(RAW / "eia_energy_futures_daily.csv.xz")


def _french(name: str) -> str:
    archive = zipfile.ZipFile(io.BytesIO(_get(FRENCH.format(name=name))))
    return archive.read(archive.namelist()[0]).decode("latin-1")


def _french_table(text: str, date_len: int) -> pd.DataFrame:
    """First table in a French library file whose rows start with a date of date_len digits."""
    lines = text.splitlines()
    i = next(k for k, line in enumerate(lines) if line.lstrip().startswith(","))
    header = ["date"] + [c.strip() for c in lines[i].split(",")[1:]]
    rows = []
    for line in lines[i + 1 :]:
        first = line.split(",")[0].strip()
        if not (first.isdigit() and len(first) == date_len):
            break
        rows.append([first] + [float(x) for x in line.split(",")[1:]])
    return pd.DataFrame(rows, columns=header).set_index("date")


def _french_monthly(text: str) -> pd.DataFrame:
    frame = _french_table(text, date_len=6)
    frame.index = pd.PeriodIndex(pd.to_datetime(frame.index, format="%Y%m"), freq="M")
    frame.index.name = "month"
    return frame


def factors() -> None:
    ff = _french_monthly(_french("F-F_Research_Data_Factors"))
    mom = _french_monthly(_french("F-F_Momentum_Factor")).rename(columns=lambda c: "UMD" if "Mom" in c else c)
    frame = (ff.join(mom[["UMD"]]) / 100.0).loc["1980-01":]
    frame.to_csv(RAW / "ff_factors_monthly.csv")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    import sys
    steps = [aqr, factors, treasuries, foreign_bonds, energy, fx, equities]
    if len(sys.argv) > 1:
        steps = [s for s in steps if s.__name__ in sys.argv[1:]]
    for step in steps:
        print("downloading:", step.__name__)
        step()
    sums = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.glob("*")) if p.name != "SHA256SUMS.json"}
    (RAW / "SHA256SUMS.json").write_text(json.dumps(sums, indent=2) + "\n")
    print("done; files in", RAW, "and", AQR_DIR)


if __name__ == "__main__":
    main()
