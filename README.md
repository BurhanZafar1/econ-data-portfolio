# Applied economics portfolio

Small, complete, tested projects in applied microeconomics, antitrust, finance and data work. Each project lives in its own folder with a README, data sources, tests and a one command entry point.

| # | Project | Problem | Methods | Link |
|---|---|---|---|---|
| 01 | Merger screen toolkit | Flag mergers that trip the 2023 US Merger Guidelines concentration presumption | HHI and change in HHI, 30 percent share test, proportional diversion, GUPPI and UPP | [projects/01-merger-screen](projects/01-merger-screen) |
| 02 | Pakistan tehsil and district crosswalk, censuses 1951 to 2023 | Move tehsil and district data across Pakistan's census frames (1998, 2017, 2023, and the district maps back to 1951) with population and area weights, plus a dated register of boundary changes | Exact population balancing on PBS restatements, fixed-charge transportation MILP with uniqueness checks, published-area weights, sourced lineage of every district, conservation checks | [projects/02-pakistan-tehsil-crosswalk](projects/02-pakistan-tehsil-crosswalk) |
| 03 | Staggered difference in differences | Estimate the effect of state minimum wage increases when adoption is staggered, and find out what TWFE hides | TWFE, Goodman-Bacon decomposition, Callaway and Sant'Anna from scratch, event study, state clustering, placebo states, randomization inference | [projects/03-staggered-did](projects/03-staggered-did) |
| 04 | Night-time lights by Pakistan district and tehsil, 1992 to 2025 | A yearly light index for every unit on the Census 2023 map, from two harmonized satellite series | Exact area-weighted zonal statistics (exactextract) on PBS 2023 polygons, pixel-area weighting, additivity and cross-series checks | [projects/04-pakistan-night-lights](projects/04-pakistan-night-lights) |
| 05 | Probabilistic record linkage without a shared ID | Link two person files with typos and no common identifier, and know how many links are wrong | Multi-pass Soundex blocking, Jaro-Winkler, Fellegi-Sunter fitted by EM with missing data, one to one assignment, precision and recall against true pairs | [projects/05-record-linkage](projects/05-record-linkage) |
| 06 | Age standardized blood pressure and hypertension, NHANES 1999 to 2018 | Give comparable yearly estimates of a leading risk factor and separate ageing from rising risk | Survey weights, strata and PSUs, Taylor linearization, WHO 2000-2025 standard population, reproduction of 30 NCHS published estimates, cross-check in R survey | [projects/06-health-nhanes-blood-pressure](projects/06-health-nhanes-blood-pressure) |
| 07 | Deposit betas and rate pass through | Measure how much of each Fed move reaches depositors, whether rates rise faster than they fall, and what that means for a bank's deposit cost next year | Cycle betas, asymmetric distributed lag regression, Newey-West HAC errors from scratch, FDIC method break handling, scenario projection | [projects/07-deposit-betas](projects/07-deposit-betas) |
| 08 | Replicating an LSTM S&P 500 direction model (Stanford CS230, 2019) | Check whether a published deep learning result that calls the market's next month holds up, and whether its accuracy is skill or drift | Exact replication of the paper's baselines, stateful LSTM, always up benchmark, purged walk forward validation, moving block bootstrap AUC intervals, multi seed runs, out of sample test 2019 to 2026 | [projects/08-sp500-lstm-replication](projects/08-sp500-lstm-replication) |

## Running a project

```bash
cd projects/<project-folder>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
pytest
```

Licensed under the MIT License (see `LICENSE`).
