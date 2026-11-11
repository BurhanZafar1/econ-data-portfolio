# Data

| File | What it is | Source | Rebuilt by |
|---|---|---|---|
| `nhanes_sbp_2017_2018.csv.gz` | 3,499 examined, non pregnant adults aged 40+ with mean SBP, sex, age, MEC exam weight, masked variance stratum and PSU | CDC NHANES 2017-2018 public files `DEMO_J` and `BPX_J`, https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.xpt and `.../BPX_J.xpt`, accessed 2026-11-11 | `python get_data.py` |
| `who_us_ihd_deaths_2018.csv` | United States deaths with underlying cause ICD-10 I20 to I25, 2018, by sex and age group | WHO Mortality Database, ICD-10 raw data part 5, https://cdn.who.int/media/docs/default-source/world-health-data-platform/mortality-raw-data/morticd10_part5.zip, country code 2450, accessed 2026-11-11 | `python get_data.py` |
| `psc2002_ihd_hazard_ratios.csv` | Hazard ratios (95% CI) for IHD death per 20 mmHg lower usual SBP, by age band, for both sexes, men and women | Lewington et al., Lancet 2002;360:1903-13 (IHD mortality hazard ratios by age, both sexes and by sex), transcribed by hand | Typed from the paper |

All values are public, aggregated or de-identified. `data/raw/` (the downloaded XPT and zip files) is not committed.
