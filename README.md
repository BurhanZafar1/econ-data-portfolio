# Applied economics portfolio

Small, complete, tested projects in applied microeconomics, antitrust, finance and data work. Each project lives in its own folder with a README, data sources, tests and a one command entry point.

| # | Project | Problem | Methods | Link |
|---|---|---|---|---|
| 01 | Merger screen toolkit | Flag mergers that trip the 2023 US Merger Guidelines concentration presumption | HHI and change in HHI, 30 percent share test, proportional diversion, GUPPI and UPP | [projects/01-merger-screen](projects/01-merger-screen) |
| 02 | Pakistan tehsil and district crosswalk, censuses 1951 to 2023 | Move tehsil and district data across Pakistan's census frames (the census-day and report frames of 1998, 2017, 2023, and the district maps back to 1951) with population and area weights, plus a dated register of boundary changes | Exact population balancing on PBS restatements, fixed-charge transportation MILP with a grade for every inferred row, published-area weights, hand-transcribed census-day tables checked by sums, per-unit uncertainty bounds, sourced lineage of every district; full replication package (master script, pinned dependencies, codebook, checksums, tests) | [projects/02-pakistan-tehsil-crosswalk](projects/02-pakistan-tehsil-crosswalk) |
| 03 | Staggered difference in differences | Estimate the effect of state minimum wage increases when adoption is staggered, and find out what TWFE hides | TWFE, Goodman-Bacon decomposition, Callaway and Sant'Anna from scratch, event study, state clustering, placebo states, randomization inference | [projects/03-staggered-did](projects/03-staggered-did) |
| 04 | Night-time lights by Pakistan district and tehsil, 1992 to 2025 | A yearly light index for every unit on the Census 2023 map from two harmonized satellite series, merged with the census populations, and district rankings by light under three exclusion rules | Exact area-weighted zonal statistics (exactextract) on PBS 2023 polygons, pixel-area weighting, additivity and cross-series checks, rank mobility within sensor eras; full replication package | [projects/04-pakistan-night-lights](projects/04-pakistan-night-lights) |
| 05 | Probabilistic record linkage without a shared ID | Link two person files with typos and no common identifier, and know how many links are wrong | Multi-pass Soundex blocking, Jaro-Winkler, Fellegi-Sunter fitted by EM with missing data, one to one assignment, precision and recall against true pairs | [projects/05-record-linkage](projects/05-record-linkage) |
| 06 | Age standardized blood pressure and hypertension, NHANES 1999 to 2018 | Give comparable yearly estimates of a leading risk factor and separate ageing from rising risk | Survey weights, strata and PSUs, Taylor linearization, WHO 2000-2025 standard population, reproduction of 30 NCHS published estimates, cross-check in R survey | [projects/06-health-nhanes-blood-pressure](projects/06-health-nhanes-blood-pressure) |
| 07 | Deposit betas and rate pass through | Measure how much of each Fed move reaches depositors, whether rates rise faster than they fall, and what that means for a bank's deposit cost next year | Cycle betas, asymmetric distributed lag regression, Newey-West HAC errors from scratch, FDIC method break handling, scenario projection | [projects/07-deposit-betas](projects/07-deposit-betas) |
| 08 | Replicating an LSTM S&P 500 direction model (Stanford CS230, 2019) | Check whether a published deep learning result that calls the market's next month holds up, and whether its accuracy is skill or drift | Exact replication of the paper's baselines, stateful LSTM, always up benchmark, purged walk forward validation, moving block bootstrap AUC intervals, multi seed runs, out of sample test 2019 to 2026 | [projects/08-sp500-lstm-replication](projects/08-sp500-lstm-replication) |
| 09 | Self reported versus measured hypertension crosswalk, NHANES to BRFSS states | Turn "ever told" survey answers into measured equivalent prevalence by age and sex, with uncertainty, so self report data can be pooled with examination surveys | Paired survey weighted logit differences with Taylor linearization, DerSimonian-Laird random effects meta-regression (MR-BRT style), rolling origin validation with a held out test period, 1,000 draws, cross-check in R survey and metafor | [projects/09-health-hypertension-crosswalk](projects/09-health-hypertension-crosswalk) |
| 10 | Replicating pairs trading (Gatev, Goetzmann and Rouwenhorst, 2006) | Test whether the distance method's 1962 to 2002 pairs trading profits hold on public data, after costs and after 2002 | The paper's distance rule with six overlapping portfolios, survivorship free industry portfolios, point in time S&P 500 universe, wait one day and break even costs, random pair placebo, factor regressions, deflated Sharpe ratio, out of sample 2003 to 2026 | [projects/10-pairs-trading-replication](projects/10-pairs-trading-replication) |
| 11 | Share of US heart disease deaths due to high systolic blood pressure | Estimate how many ischemic heart disease deaths would not occur if SBP sat at the theoretical minimum, by age and sex, with uncertainty | Continuous exposure PAF on NHANES 2017-2018 microdata, PSC age and sex specific hazard ratios, TMREL uniform 110 to 115 mmHg, WHO Mortality Database deaths, 1,000 draws (Rao-Wu bootstrap, relative risk and TMREL), sensitivity analysis, GBD 2019 benchmark, cross-check in R survey | [projects/11-health-sbp-ihd-paf](projects/11-health-sbp-ihd-paf) |
| 12 | Replicating time series momentum (Moskowitz, Ooi and Pedersen, 2012) | Test whether 12 month trend following across futures earns the paper's 1985 to 2009 alpha, survives its critiques and lasts after 2009 | Known answer tests on the authors' factor file, rebuild on 23 public markets (bond returns from yields, calendar rolled energy futures), ex ante volatility scaling, pooled regressions clustered by month, look back and holding grid, volatility scaling decomposition, deflated Sharpe ratio, block bootstrap, break even costs, out of sample 2010 to 2026 | [projects/12-time-series-momentum](projects/12-time-series-momentum) |
| 13 | Cartel overcharge damages: the JEC railroad cartel, 1880 to 1886 | Estimate how much a cartel overcharged its customers, put a dollar figure and interval on the harm, and show the checks an opposing expert would demand | Dummy variable (during versus price war) and forecasting but for prices, Newey-West HAC errors, Kennedy correction, leave one price war out validation, circular shift placebo test, 2SLS demand elasticity for the volume effect, known answer tests against published regressions | [projects/13-cartel-overcharge-damages](projects/13-cartel-overcharge-damages) |

## Authorship

Projects 02 and 04 come from my research assistant work for Professor M. Yasir Khan (University of Pittsburgh); the others use public data. All of them were developed with AI coding assistance under my direction and review, as some commit messages record.

## Running a project

```bash
cd projects/<project-folder>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py          # most projects
bash build/run_all.sh  # project 02 (project 04: bash code/run_all.sh); each README has the full steps
pytest
```

Licensed under the MIT License (see `LICENSE`).
