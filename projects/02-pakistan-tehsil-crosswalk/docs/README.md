# Pakistan tehsil and district crosswalk, Census 2017 to Census 2023

First release, 3 November 2026. Built by Burhan Zafar for Professor M. Yasir Khan (University of Pittsburgh).

## What it is
A table that moves any tehsil- or district-level variable reported on the Census 2017 administrative frame of Pakistan's four provinces onto the Census 2023 frame, with a population weight and an area weight for every (2017 unit, 2023 unit) pair, and the reverse. 535 sub-district units of 2017 (tehsils, talukas, sub-divisions, sub-tehsils, including the former FATA) map onto 590 units of 2023; 134 districts onto 135.

## Files
```
output/crosswalk_tehsil_2017_to_2023.csv      main table, 612 rows
output/crosswalk_district_2017_to_2023.csv    district table, 143 rows
output/unit_master_2017_all.csv               all units in PBS Census 2017 Table 1
output/unit_master_2023_all.csv               all units in PBS Census 2023 Table 1 (with dds_id)
output/check_overlay_disagreements.csv        diagnostics on the 2017 polygon layer
output/validation_summary.json                the numbers behind VALIDATION.md
code/apply_crosswalk.R                        apply in R (base R, no packages)
code/apply_crosswalk.do                       apply in Stata (14+)
build/01_unit_master.py .. 05_district_and_validate.py   reproducible pipeline (Python)
docs/DATA_DICTIONARY.md, docs/VALIDATION.md
raw/                                          inputs as downloaded (see Sources)
```

## Sources
1. Pakistan Bureau of Statistics, Population and Housing Census 2017, Table 1 by district and tehsil (population 2017, area, and population 1998 restated on 2017 units).
2. Pakistan Bureau of Statistics, 7th Population and Housing Census 2023, Table 1 by district and tehsil (population 2023, area, and population 2017 restated on 2023 units).
   Both as parsed from PBS's published Excel tables by Data Darbar (Hiba Sameen), warehouse tables census_panel_2017 and census_panel_2023, release 2026-11-01, https://darbar.adaad.org/datasets/ ; spot-checked here against the PBS PDF for Khyber Pakhtunkhwa (https://www.pbs.gov.pk/sites/default/files/population/2023/tables/table_1_kp_districts.pdf).
3. Data Darbar, subdistrict_crosswalk_2017_2023 (grouping of units into territory-covering groups; CC BY 4.0). Every group re-verified against the PBS populations.
4. PBS Digital Census 2023 tehsil polygons as redistributed by Data Darbar (pbs_tehsils_2023.geojson, 649 units keyed by dds_id), used only for adjacency in the 10 LP-resolved groups.
5. geoBoundaries PAK ADM3 (boundaryYearRepresented 2017; Runfola et al. 2020, ODbL), used only as a check column.

## Method in one paragraph
Each 2023 unit carries PBS's own count of its 2017 population. Where a 2017 unit's name survives unchanged and its 2017 population equals the restated figure, the pair is one-to-one (481 units). Where units were restructured, the 2023 units' restated populations are partitioned among the 2017 parents so that each parent's 2017 population is reproduced exactly (29 district groups); the population weight is then restated child population over parent population, a PBS figure divided by a PBS figure. In 10 groups no exact partition exists because territory moved between existing units or a new unit draws from several parents; there a transportation LP conserves both margins and chooses the sparsest flow consistent with adjacency in the 2023 polygons, and the rows are marked medium confidence. Area weights use PBS's published 2023 areas, split between sources in proportion to people only where a 2023 unit has more than one source. Full details, every split row and the checks are in docs/VALIDATION.md.

## How to use
R:
```r
source("code/apply_crosswalk.R")
cw <- read_crosswalk("output/crosswalk_tehsil_2017_to_2023.csv")
check_crosswalk(cw)                                     # should print max deviation 0
out <- apply_crosswalk(my2017data, cw, id = "unit_id_2017",
                       counts = c("schools"), rates = c("literacy_rate"), weight = "pop")
```
Stata:
```stata
do code/apply_crosswalk.do
use my2017data, clear
apply_crosswalk, cw("output/crosswalk_tehsil_2017_to_2023.csv") id(unit_id_2017) counts(schools) rates(literacy_rate)
```
Your data must carry the 2017 unit id. Join on (district_2017, unit_2017) with PBS's spellings to get unit_id_2017 from unit_master_2017_all.csv, or on district_2017 for district data. The R and Stata functions were written against the file layout and mirrored line for line in Python, which was run; R and Stata themselves were not available on the build machine, so please run check_crosswalk once before first use and report any error.

## Limits
- The crosswalk links the two census frames. Changes notified between censuses that PBS did not adopt for Census 2023 (Punjab's October 2022 districts) are not in it; a yearly extension needs the notifications.
- Islamabad, AJK and Gilgit-Baltistan are excluded at Professor Khan's request to get the four provinces right first.
- Confidence "medium" rows (82 of 612) rest on PBS's restated populations plus an inference about which successor received a transfer; they conserve population exactly but the within-group allocation is not a PBS figure.
- Karachi: all Karachi sub-divisions map one-to-one (Karachi West's split into Keamari follows sub-division lines), so no Karachi-specific assumption was needed; karachi_division flags the seven districts for users who want one unit.

## Reproduce
```
pip install pandas pyarrow geopandas scipy
python build/01_unit_master.py && python build/02_crosswalk_pop.py && python build/03_resolve_lp.py && python build/04_area_weights.py && python build/05_district_and_validate.py
```
