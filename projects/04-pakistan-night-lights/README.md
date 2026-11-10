# Night-time lights by Pakistan district and tehsil, 1992 to 2025, on the Census 2023 frame

Version 2.0, 10 November 2026 (first release 5 November). Built by Burhan Zafar (Whitman College) for Professor M. Yasir Khan (University of Pittsburgh). Companion to the tehsil crosswalk in projects/02-pakistan-tehsil-crosswalk. Release history in CHANGELOG.md; how to cite in CITATION.cff; licences in LICENSE-DATA.txt (CC BY 4.0) and LICENSE-CODE.txt (MIT).

## 1. Overview
A yearly index of night-time light for every one of the 649 sub-district units (tehsils, talukas, sub-divisions) and 156 districts on the PBS Census 2023 map, from the first year satellite night-light composites exist (1992) to the latest year available (2024 or 2025). The unit list is fixed at the 2023 frame, so the same polygon is measured every year and the series can be joined to anything already on 2023 units, including the crosswalked 1998 and 2017 census data. On top of the light tables: a merged panel with the census populations 1951 to 2023 on the same units, and district rankings by light for every year under three exclusion rules, with mobility statistics and figures (docs/RANKINGS.md), which answer the first analysis question put to the data: are districts stuck in one ranking?

Two independent source series are provided, because no single public dataset covers 1992 to today on one instrument:

| | Series A | Series B |
|---|---|---|
| Source | Li, Zhou, Zhao and Zhao (2020), harmonized DMSP-VIIRS night-time lights, figshare v10 (1992-2024) | Chen, Yu, Yang et al., global NPP-VIIRS-like night-time light, Version 2 (1992-2025), Harvard Dataverse, updated July 2026 |
| Unit | digital number 0-63 (DMSP scale) | radiance, nW/cm2/sr (VIIRS scale) |
| Pixel | 30 arc-seconds (about 0.9 km) | 15 arc-seconds (about 0.46 km) |
| Inputs by year (sensor_basis column) | 1992-2013 calDMSP: inter-calibrated DMSP-OLS stable lights; 2014-2024 simVIIRS: VIIRS annual composites converted to the DMSP scale | 1992-2012 DMSP-derived: DMSP converted to the VIIRS radiance scale by the authors' cross-sensor model; 2013-2025 VIIRS: NPP-VIIRS annual composites |
| Join year | 2013/2014 | 2012/2013 |
| Known problem (series_note column) | 2014-2016 under-record dim lights (docs/VALIDATION.md) | 2013-2016 national sum about a quarter below 2012 and 2017 at the sensor change |
| Files | ntl_A_harmonizedDN_*.csv | ntl_B_viirslike_*.csv |

Series B is the one to start with for a single long series in physical units; series A is the standard DMSP-era reference and the better choice for 1992-2013 work. Across the 135 districts of the four provinces the two agree closely (correlation of log sum-of-lights 0.79 to 0.94 in every year; the full list by year is in docs/VALIDATION.md), with one caveat at the dim end: in series A's VIIRS-converted years (2014 onward) remote districts show a faint glow that series B does not see; the dn_*_gt7 columns remove it.

To reproduce from scratch: `bash setup.sh`, then `bash code/run_all.sh` (section 5).

## 2. Data availability and provenance
All inputs are public and were downloaded by the scripts in code/ (or by the listed URLs) with checksums verified against the publishers' records. No restricted or author-supplied data are used. Access cost: none; the figshare and Dataverse files need no registration.

| Data | Files | Where obtained | Access | In package | Citation |
|---|---|---|---|---|---|
| Series A rasters: Harmonized_DN_NTL_<year>_calDMSP.tif (1992-2013) and _simVIIRS.tif (2014-2024), global, 30 arc-second, uint8 | raw/harmonized_ntl/ (33 files, 1.0 GB) | https://doi.org/10.6084/m9.figshare.9828827, version 10; downloaded 5 Nov 2026 by code/01_download_nightlights.py, md5 of every file checked against the figshare record (raw/figshare_9828827.json) | open, CC BY 4.0 | no (size) | Li et al. (2020) |
| Series B rasters: <year>_Version2.zip (1992-2025), each holding a global 15 arc-second GeoTIFF | raw/viirs_like_v2/ (34 files, 3.4 GB); Pakistan clips in raw/viirs_like_v2_clip/ (89 MB) | https://doi.org/10.7910/DVN/YGIVCD, dataset version 10 (July 2026); downloaded 5 Nov 2026; md5 of every file checked against the Dataverse record (raw/viirs_like_list.txt, raw/dataverse_YGIVCD.json) by code/01b_download_viirs_like.py | open, CC BY 4.0 | no (size) | Chen et al. (2021, 2026) |
| PBS Digital Census 2023 tehsil and district polygons | raw/boundaries/pbs_tehsils_2023.geojson, pbs_districts_2023.geojson | https://darbar.adaad.org/data/boundaries/ (Data Darbar's redistribution of the PBS files, release 2026-11-01), accessed 3 Nov 2026 | open, CC BY 4.0 | no (in project 02's raw list) | Pakistan Bureau of Statistics (2023) |
| Census populations 1951-2023 on 2023 units | ../02-pakistan-tehsil-crosswalk/output/population_panel_2023_frame*.csv | project 02 of this repository | open | yes (project 02) | project 02 |

Nothing else enters. The raw annual composites behind both series are the DMSP-OLS stable lights (NOAA NGDC) and the VIIRS DNB annual composites (Earth Observation Group, Colorado School of Mines); the EOG site requires a free account, so the two harmonized products above, which redistribute processed versions openly, were used instead. If a raw VIIRS radiance series (2012 onward, EOG annual VNL v2.2) is wanted, the same scripts run on those files with one line changed.

## 3. Dataset list
Every column of every file is described in docs/codebook.csv (file, column, type, units, missing count, description, producing script). The files:

```
output/ntl_B_viirslike_tehsil_2023frame_1992_2025.csv     one row per tehsil and year (22,066 rows)
output/ntl_B_viirslike_district_2023frame_1992_2025.csv   one row per district and year (5,304 rows)
output/ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv  (21,417 rows)
output/ntl_A_harmonizedDN_district_2023frame_1992_2024.csv (5,148 rows)
output/*_wide_*.csv                                       the sum-of-lights measure, one column per year
output/panel_ntl_census_tehsil_2023frame.csv              analysis panel: both series joined to the crosswalked census populations (1951-2023) on 2023 units, with light per 1,000 people in census years
output/panel_ntl_census_district_2023frame.csv            the same at district level
output/rankings/                                          district rankings by year and mobility statistics (docs/RANKINGS.md)
output/figures/                                           fig1 to fig5 for the rankings note
output/boundaries_tehsil_2023.gpkg, boundaries_district_2023.gpkg, boundaries_units_2023.csv   the polygons used, with areas
output/validation_summary.json, docs/VALIDATION.md        checks: completeness, additivity, agreement between series, the sensor break, the dim end, face checks
output/CHECKSUMS.sha256, RUN_LOG.txt, logs/               SHA-256 of every output; timings and the log of each step of the last build
```
Keys: (dds_id, year) for tehsil tables, (district_code, year) for district tables, (series, measure, variant, year, unit) for the long rankings file; every table has a unique, non-missing key (checked in code/09_codebook.py).

Columns per unit and year: identifiers (year, sensor_basis, dds_id or district_code, tehsil_2023, district_2023, province_2023, in_four_provinces, outside_census_frame); area_km2 (geodesic) and pixel_area_km2 (what the raster grid assigns; they agree to 0.1 percent); series B rad_sum, rad_mean, rad_max, rad_lit_share, rad_sum_km2 (radiance times pixel area, summed: the "sum of lights" comparable between a tehsil in Punjab and one in Balochistan), rad_per_km2, log1p_rad_sum_km2, asinh_rad_sum_km2, rad_sum_gt1_km2 and rad_lit_share_gt1 (counting only pixels above 1 nW/cm2/sr), coverage_pixels, series_note; series A the same with dn_ in place of rad_, and dn_sum_gt7_km2 / dn_lit_share_gt7 for the DN > 7 floor the authors recommend. The merged panel adds pop_census (the census population in 1998, 2017 and 2023, blank in other years; nothing is interpolated), rad_sum_km2_per_1000 and dn_sum_km2_per_1000, and the constant-frame population history pop_1951 .. pop_2023 on every row.

## 4. Computational requirements
- Software: Python 3.13.18 with the packages pinned in requirements.txt (pandas 3.0.5, numpy 2.5.3, geopandas 1.2.0, shapely 2.2.0, pyproj 3.8.0, pyogrio 0.13.0, rasterio 1.5.2, exactextract 0.3.0, matplotlib 3.11.2). No R or Stata is needed; the CSVs load in either.
- Hardware and run time: Ubuntu 24.04 on 2 cpu and 7 GB memory. After the downloads, the whole build takes about ten minutes (output/RUN_LOG.txt gives each step; the series B clipping in code/04 is the longest). Memory: well within the 7 GB of the build machine (one clipped Pakistan window of the 15 arc-second raster at a time). Storage: 4.5 GB of raw rasters, about 32 MB of outputs.
- Randomness: none. No pseudo-random number generator is used; every number is a weighted sum or mean of published pixel values, or a rank of such numbers.
- Network: only for the two download scripts (figshare and Harvard Dataverse APIs).

## 5. Instructions to replicators
1. `bash setup.sh` (installs the pinned packages).
2. Put the PBS 2023 boundary files in raw/boundaries/ (URLs in section 2), and have project 02's output folder at ../02-pakistan-tehsil-crosswalk/output (or set the environment variable CROSSWALK_OUTPUT to it).
3. `bash code/run_all.sh` from the project root. It downloads and verifies the rasters (skipping files already present and verified), then runs code/02 to code/09 in order, logs each step to output/logs/, regenerates every file in output/ and the generated documents (docs/VALIDATION.md, docs/RANKINGS.md, docs/codebook.csv), and writes output/CHECKSUMS.sha256.
4. Compare with the released checksums: `sha256sum -c output/CHECKSUMS.sha256` (the two generated notes carry the build date, so those lines differ by date only).
5. `python -m pytest -q tests` checks the released tables without rebuilding (balanced panels, non-negative sums, raster and geodesic areas agree, districts add up from tehsils, rankings are permutations, codebook complete, checksums match); run_all.sh runs it at the end when pytest is installed.

No manual step and no GIS software is involved; all geometry is done in code.

## 6. Programs and the outputs they produce
| Program | Produces |
|---|---|
| code/01_download_nightlights.py | raw/harmonized_ntl/*.tif (series A), md5-verified |
| code/01b_download_viirs_like.py | raw/viirs_like_v2/*.zip (series B), md5-verified |
| code/02_prepare_boundaries.py | boundaries_tehsil_2023.gpkg, boundaries_district_2023.gpkg, boundaries_units_2023.csv (repaired polygons, geodesic areas) |
| code/03_zonal_stats.py | ntl_A_* tables (long and wide) |
| code/04_zonal_stats_viirs_like.py | raw/viirs_like_v2_clip/*.tif (Pakistan windows), ntl_B_* tables |
| code/05_checks.py | validation_summary.json, docs/VALIDATION.md |
| code/06_merge_with_census.py | panel_ntl_census_tehsil_2023frame.csv, panel_ntl_census_district_2023frame.csv |
| code/07_district_rankings.py | output/rankings/* and figures/fig1 to fig5 |
| code/08_rankings_report.py | docs/RANKINGS.md (every number read from output/rankings) |
| code/09_codebook.py | docs/codebook.csv |
| code/99_checksums.py | output/CHECKSUMS.sha256 |
| tests/test_outputs.py | pytest checks of the released tables |
| code/ntl_common.py | shared functions: pixel areas by latitude, exact zonal statistics |

Figures: fig1_rank_stability_spearman.png, fig2_quintile_transitions_1992_2025.png, fig3_biggest_climbers_rank_paths.png, fig4_rank_1992_vs_2025_scatter.png, fig5_biggest_climbers_density.png are all drawn by code/07 from the files in output/rankings. Hand-written documents: this README and CHANGELOG.md; docs/VALIDATION.md, docs/RANKINGS.md and docs/codebook.csv are generated.

## 7. Method in plain words
For each year the global raster is cut to a window around Pakistan. For every polygon, every pixel that touches it contributes in proportion to the share of the pixel's area that lies inside (exactextract), so a pixel on the border between two tehsils is split between them rather than given to one. Pixel areas are computed from the cell size and the row's latitude, so sums are in km2 terms. Districts are computed from their own polygons and checked against the sum of their tehsils (they agree to 0.2 percent at the median; the gaps come from the two PBS layers not nesting perfectly along the Karachi coast and in two AJK districts). Nothing is interpolated or modelled.

Transformations. For a regression the usual choices are log1p_rad_sum_km2 (or log1p_dn_sum_km2) and rad_per_km2 (density); the asinh_ columns give the inverse hyperbolic sine, which behaves like log(1 + x) for large values and keeps zeros, so a user can report both. Use rad_mean when comparing units of very different size. Zeros are real: many Balochistan tehsils had no detectable light in the 1990s. The rankings are invariant to any increasing transformation, so log versus asinh does not affect them. The sensor_basis column lets a user include sensor-period effects (DMSP years against VIIRS years), which is the minimum a panel regression across 2012/13 should do; year fixed effects absorb a national shift at the join but not a shift that differs between bright and dim units, which is what the dim-end check shows for series A.

Cautions the sources themselves give, and that hold here: DMSP digital numbers saturate in city centres (top-coding at 63) and blur light outward over several kilometres, so DMSP-era values for the brightest and the dimmest units are the least reliable; the pre-2013 values of series B are modelled from DMSP, not observed VIIRS radiance; and in sparsely populated, rural tehsils light is a weak proxy for activity. The validation report quantifies the transition years and the dim end; the rankings note measures change within sensor eras as well as end to end for that reason.

## 8. Omissions
- Gilgit-Baltistan, Azad Jammu and Kashmir and Islamabad units are included in the light tables (flagged in_four_provinces = False) but the census populations in the merged panel cover the four provinces only, as in project 02; Islamabad's census populations (1998, 2017, 2023) are added in the rankings script from PBS Table 1's Islamabad rows (the same figures as in project 02's unit_master_2017_all.csv and unit_master_2023_all.csv).
- No raw EOG VIIRS radiance (2012 onward) is included; see section 2.
- The rankings use Census 2023 districts; the 21 districts dropped in variant (iii) are those whose polygon touches one of the five big-city districts (computed from the PBS polygons with a 50 m tolerance; list in output/rankings/adjacent_to_big_cities.csv).

## 9. References
1. Li, X., Zhou, Y., Zhao, M., Zhao, X. (2020). A harmonized global nighttime light dataset 1992-2018. Scientific Data 7, 168. Data: figshare, https://doi.org/10.6084/m9.figshare.9828827 (version 10, extended to 2024). CC BY 4.0.
2. Chen, Z., Yu, B., Yang, C., Zhou, Y., Yao, S., Qian, X., Wang, C., Wu, B., Wu, J. (2021). An extended time series (2000-2018) of global NPP-VIIRS-like nighttime light data from a cross-sensor calibration. Earth System Science Data 13, 889-906; and Chen, Z., Liao, L., Wang, C., Shi, K., Yu, B. (2026). The 1992-2024 global NPP-VIIRS-like nighttime light annual data from deep learning super-resolution reconstruction. Journal of Remote Sensing 6, 0874. Data: Harvard Dataverse, https://doi.org/10.7910/DVN/YGIVCD (Version 2, July 2026).
3. Pakistan Bureau of Statistics (2023). Digital Census 2023 tehsil and district polygons, as redistributed by Data Darbar (Hiba Sameen), https://darbar.adaad.org/, release 2026-11-01.
4. Baston, D. (ISciences). exactextract 0.3; Gillies, S. et al., rasterio; Jordahl, K. et al., GeoPandas; pyproj (PROJ).
5. Henderson, J. V., Storeygard, A., Weil, D. N. (2012). Measuring economic growth from outer space. American Economic Review 102(2), 994-1028. Gibson, J., Olivia, S., Boe-Gibson, G., Li, C. (2021). Which night lights data should we use in economics, and where? Journal of Development Economics 149, 102602. (Background for the cautions in section 7.)
