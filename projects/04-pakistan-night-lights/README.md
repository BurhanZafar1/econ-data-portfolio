# Night-time lights by Pakistan district and tehsil, 1992 to 2025, on the Census 2023 frame

Built 5 November 2026 by Burhan Zafar for Professor M. Yasir Khan (University of Pittsburgh). Companion to the tehsil crosswalk in projects/02-pakistan-tehsil-crosswalk.

## What it is
A yearly index of night-time light for every one of the 649 sub-district units (tehsils, talukas, sub-divisions) and 156 districts on the PBS Census 2023 map, from the first year satellite night-light composites exist (1992) to the latest year available (2024 or 2025). The unit list is fixed at the 2023 frame, so the same polygon is measured every year and the series can be joined to anything already on 2023 units, including the crosswalked 1998 and 2017 census data.

Two independent source series are provided, because no single public dataset covers 1992 to today on one instrument:

| | Series A | Series B |
|---|---|---|
| Source | Li, Zhou, Zhao and Zhao (2020), harmonized DMSP-VIIRS night-time lights, figshare v10 (1992-2024) | Chen, Yu, Yang et al., global NPP-VIIRS-like night-time light, Version 2 (1992-2025), Harvard Dataverse, updated July 2026 |
| Unit | digital number 0-63 (DMSP scale) | radiance, nW/cm2/sr (VIIRS scale) |
| Pixel | 30 arc-seconds (about 0.9 km) | 15 arc-seconds (about 0.46 km) |
| Inputs | inter-calibrated DMSP-OLS 1992-2013; VIIRS converted to DMSP scale 2014-2024 | DMSP converted to VIIRS scale 1992-2012; VIIRS 2013-2025 |
| Known problem | 2014-2016 under-record dim lights (see VALIDATION.md) | 2013-2016 a quarter below 2012 and 2017 at the sensor change |
| Files | ntl_A_harmonizedDN_*.csv | ntl_B_viirslike_*.csv |

Series B is the one to start with for a single long series in physical units; series A is the standard DMSP-era reference and the better choice for 1992-2013 work. Across the 135 districts of the four provinces the two agree closely (correlation of log sum-of-lights 0.79 to 0.94 in every year), with one caveat at the dim end: in series A's VIIRS-converted years (2014 onward) remote districts show a faint glow that series B does not see; the dn_*_gt7 columns remove it (VALIDATION.md).

## Files
```
output/ntl_B_viirslike_tehsil_2023frame_1992_2025.csv     one row per tehsil and year (22,066 rows)
output/ntl_B_viirslike_district_2023frame_1992_2025.csv   one row per district and year (5,304 rows)
output/ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv  (21,417 rows)
output/ntl_A_harmonizedDN_district_2023frame_1992_2024.csv (5,148 rows)
output/*_wide_*.csv                                       the sum-of-lights measure, one column per year
output/panel_ntl_census_tehsil_2023frame.csv              analysis panel: both series joined to the crosswalked census populations (1951-2023) on 2023 units, with light per 1,000 people in census years
output/panel_ntl_census_district_2023frame.csv            the same at district level
output/boundaries_tehsil_2023.gpkg, boundaries_district_2023.gpkg, boundaries_units_2023.csv   the polygons used, with areas
output/validation_summary.json, docs/VALIDATION.md
code/01_download_nightlights.py   downloads and md5-checks series A (1.1 GB)
code/02_prepare_boundaries.py     repairs the PBS 2023 polygons and computes geodesic areas
code/03_zonal_stats.py            series A statistics
code/04_zonal_stats_viirs_like.py series B statistics (clips the 10 GB global files to Pakistan first)
code/05_checks.py                 checks and the validation report
code/06_merge_with_census.py      joins the light tables to the census population panel from project 02
code/ntl_common.py                shared functions (pixel areas, exact zonal statistics)
raw/                              inputs as downloaded (not in the repository because of size; see Sources)
```

## Columns (per unit and year)
- Identifiers: year, sensor_basis, dds_id / district_code (PBS Digital Census ids), tehsil_2023, district_2023, province_2023, in_four_provinces, outside_census_frame (polygon has no row in the 2023 census tables).
- area_km2: geodesic area of the polygon; pixel_area_km2: the area the raster grid assigns to the unit (agree to 0.1 percent).
- Series B: rad_sum (radiance summed over pixels, each weighted by the share of the pixel inside the unit), rad_mean (area-weighted mean radiance), rad_max, rad_lit_share (share of the unit's area with radiance above 0), rad_sum_km2 (radiance times pixel area, summed; the "sum of lights" that is comparable between a tehsil in Punjab and one in Balochistan), rad_per_km2 (= rad_sum_km2 / pixel_area_km2), log1p_rad_sum_km2, rad_sum_gt1_km2 and rad_lit_share_gt1 (the same two counting only pixels above 1 nW/cm2/sr), coverage_pixels, series_note.
- Series A: the same with dn_ in place of rad_, and dn_sum_gt7_km2 / dn_lit_share_gt7 for the DN > 7 floor the authors recommend.

For a regression the usual choices are log1p_rad_sum_km2 (or log1p_dn_sum_km2) and rad_per_km2 (density). Use rad_mean when comparing units of very different size. Zeros are real: many Balochistan tehsils had no detectable light in the 1990s. The merged panel adds pop_census (the census population in 1998, 2017 and 2023, blank in other years; nothing is interpolated) and rad_sum_km2_per_1000 / dn_sum_km2_per_1000 (light per thousand people in census years), together with the constant-frame population history pop_1951 .. pop_2023 on every row.

## Method in plain words
For each year the global raster is cut to a window around Pakistan. For every polygon, every pixel that touches it contributes in proportion to the share of the pixel's area that lies inside (exactextract), so a pixel on the border between two tehsils is split between them rather than given to one. Pixel areas are computed from the cell size and the row's latitude, so sums are in km2 terms. Districts are computed from their own polygons and checked against the sum of their tehsils (they agree to 0.2 percent at the median; the gaps come from the two PBS layers not nesting perfectly along the Karachi coast and in two AJK districts). Nothing is interpolated or modelled; every number is a weighted sum or mean of published pixel values.

## Reproduce
```
pip install rasterio geopandas exactextract pyproj pandas numpy
python code/01_download_nightlights.py            # series A rasters
# series B: download the <year>_Version2.zip files listed in raw/viirs_like_list.txt into raw/viirs_like_v2/
python code/02_prepare_boundaries.py && python code/03_zonal_stats.py && python code/04_zonal_stats_viirs_like.py && python code/05_checks.py
python code/06_merge_with_census.py      # needs ../pk_crosswalk/output (or set CROSSWALK_OUTPUT to projects/02-pakistan-tehsil-crosswalk/output)
```
The whole run takes about ten minutes on a laptop after the downloads.

## Sources
1. Li, X., Zhou, Y., Zhao, M., Zhao, X. (2020). A harmonized global nighttime light dataset 1992-2018. Scientific Data 7, 168. Data: figshare, https://doi.org/10.6084/m9.figshare.9828827 (version 10, extended to 2024). CC BY 4.0.
2. Chen, Z., Yu, B., Yang, C., Zhou, Y., Yao, S., Qian, X., Wang, C., Wu, B., Wu, J. (2021). An extended time series (2000-2018) of global NPP-VIIRS-like nighttime light data from a cross-sensor calibration. Earth System Science Data 13, 889-906; and Chen, Z., Liao, L., Wang, C., Shi, K., Yu, B. (2026). The 1992-2024 global NPP-VIIRS-like nighttime light annual data from deep learning super-resolution reconstruction. Journal of Remote Sensing 6, 0874. Data: Harvard Dataverse, https://doi.org/10.7910/DVN/YGIVCD (Version 2, July 2026).
3. Boundaries: Pakistan Bureau of Statistics, Digital Census 2023 tehsil and district polygons, as redistributed by Data Darbar (Hiba Sameen), https://darbar.adaad.org/, release 2026-11-01.
4. Software: exactextract 0.3 (Baston, ISciences), rasterio, GeoPandas, pyproj.

The raw annual composites behind both series are the DMSP-OLS stable lights (NOAA NGDC) and the VIIRS DNB annual composites (Earth Observation Group, Colorado School of Mines). The EOG site requires a free account, so the two harmonized products above, which redistribute processed versions openly, were used instead. If a raw VIIRS radiance series (2012 onward, EOG annual VNL v2.2) is wanted, the same scripts run on those files with one line changed.
