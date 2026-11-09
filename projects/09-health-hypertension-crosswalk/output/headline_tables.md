## Crosswalk by age and sex
| Age | Sex | Self report % | Measured % | Sensitivity % | Specificity % | Crosswalk d (95% CI) |
|---|---|---|---|---|---|---|
| 18-34 | Female | 8.4 | 2.8 | 67 | 93 | -1.16 (-1.48 to -0.85) |
| 18-34 | Male | 13.1 | 7.6 | 54 | 90 | -0.61 (-0.85 to -0.37) |
| 35-44 | Female | 18.9 | 15.4 | 82 | 93 | -0.29 (-0.43 to -0.16) |
| 35-44 | Male | 23.3 | 21.3 | 72 | 90 | -0.11 (-0.26 to +0.04) |
| 45-54 | Female | 31.8 | 29.2 | 82 | 89 | -0.15 (-0.31 to +0.02) |
| 45-54 | Male | 33.4 | 36.5 | 75 | 90 | +0.13 (-0.01 to +0.27) |
| 55-64 | Female | 46.5 | 50.0 | 84 | 91 | +0.15 (+0.03 to +0.27) |
| 55-64 | Male | 50.8 | 53.1 | 82 | 84 | +0.06 (-0.10 to +0.22) |
| 65+ | Female | 64.1 | 71.4 | 85 | 89 | +0.33 (+0.21 to +0.44) |
| 65+ | Male | 57.9 | 63.8 | 85 | 91 | +0.25 (+0.13 to +0.38) |

## Validation test origins 2013-2014 to 2017-2018 (age x sex cells; choice made on earlier origins)
| method | cells | bias_pp | mae_pp | max_abs_error_pp | coverage_95 |
|---|---|---|---|---|---|
| No adjustment (self report as is) | 30 | -0.31 | 4.27 | 10.55 | nan |
| Sensitivity and specificity correction, all earlier cycles | 30 | 3.14 | 4.1 | 15.57 | nan |
| Sensitivity and specificity correction, latest 3 cycles | 30 | 0.39 | 3.74 | 15.25 | nan |
| Logit crosswalk, constant, all earlier cycles | 30 | 1.38 | 2.22 | 7.15 | 0.97 |
| Logit crosswalk, age specific linear trend | 30 | -1.92 | 2.96 | 8.02 | 0.87 |
| Logit crosswalk, constant, latest 3 cycles | 30 | -0.35 | 2.21 | 6.57 | 0.97 |

## 2017 check: median of states vs NHANES 2017-2018
| age_group | self_report_pct | adjusted_pct | nhanes_self_pct | nhanes_measured_pct |
|---|---|---|---|---|
| 18-24 | 7.8 | 3.8 | 4.4 | 2.3 |
| 25-34 | 13.4 | 6.7 | 16.9 | 8.6 |
| 35-44 | 20.6 | 17.9 | 18.0 | 16.8 |
| 45-54 | 32.0 | 31.8 | 33.6 | 36.1 |
| 55-64 | 45.8 | 48.2 | 45.5 | 52.1 |
| 65+ | 60.0 | 66.6 | 59.6 | 68.5 |

## BRFSS 2017, age 65+, lowest and highest adjusted states
| state | self_report_pct | adjusted_pct | adjusted_lower_pct | adjusted_upper_pct |
|---|---|---|---|---|
| MT | 52.4 | 59.5 | 55.0 | 63.7 |
| CO | 52.8 | 59.8 | 55.9 | 63.9 |
| LA | 68.0 | 73.9 | 69.8 | 77.8 |
| WV | 69.4 | 75.1 | 71.4 | 78.5 |
