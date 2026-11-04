# Pakistan tehsil and district crosswalk, Censuses 1998, 2017 and 2023

Second release, 4 November 2026 (first release 3 November covered 2017 to 2023 only). Built by Burhan Zafar for Professor M. Yasir Khan (University of Pittsburgh).

## What it is
Tables that move any tehsil- or district-level variable reported on one census frame of Pakistan's four provinces onto another, with a population weight and an area weight for every pair of units:

- 1998 tehsils -> 2017 tehsils (424 units -> 535 units, 598 rows)
- 2017 tehsils -> 2023 tehsils (535 -> 590, 612 rows)
- 1998 tehsils -> 2023 tehsils, the base-year table Professor Khan asked for (424 -> 590, 678 rows, chained through 2017)
- the same three at district level (114 -> 134 -> 135 districts)

Two companion tables answer the questions in Professor Khan's note of 3 November: which tehsils became which districts (new_district_lineage.csv, tehsil_district_membership.csv), and when each district and tehsil change happened (event_register.csv, with a source and a confidence grade for every dated row).

## Files
```
output/crosswalk_tehsil_1998_to_2023.csv      base-year table: every 1998 unit onto the 2023 frame (678 rows)
output/crosswalk_tehsil_1998_to_2017.csv      1998 -> 2017 (598 rows)
output/crosswalk_tehsil_2017_to_2023.csv      2017 -> 2023 (612 rows)
output/crosswalk_district_1998_to_2023.csv    district level (151 rows)
output/crosswalk_district_1998_to_2017.csv    district level (142 rows)
output/crosswalk_district_2017_to_2023.csv    district level (143 rows)
output/new_district_lineage.csv               every district new in 2017 or 2023: the earlier tehsils that formed it, shares, year, source
output/tehsil_district_membership.csv         every tehsil's district in the later frame(s), with the share of its people there
output/event_register.csv                     dated district and tehsil changes 1998-2026 with sources (see docs/EVENT_REGISTER.md)
output/unit_master_1998.csv, district_master_1998.csv   the 1998 frame (PCO 1951-98 report)
output/unit_master_2017_all.csv, unit_master_2023_all.csv   all units in PBS Table 1 of each census
output/check_overlay_mismatches.csv           diagnostics on the free 2017 polygon layers
output/validation_summary.json, validation_summary_1998.json   the numbers behind the validation reports
code/apply_crosswalk.R                        apply in R (base R, no packages); works on all six tables
code/apply_crosswalk.do                       apply in Stata (14+); same interface
build/01 .. 11                                reproducible pipeline (Python), build/crosswalk_lib.py is the matching engine
docs/DATA_DICTIONARY.md, VALIDATION.md (2017->2023), VALIDATION_1998.md (1998 layer), EVENT_REGISTER.md
raw/                                          inputs as downloaded (see Sources)
```

## Sources
1. Pakistan Bureau of Statistics, Population and Housing Census 2017, Table 1 by district and tehsil (population 2017, area, and population 1998 restated on 2017 units).
2. Pakistan Bureau of Statistics, 7th Population and Housing Census 2023, Table 1 by district and tehsil (population 2023, area, and population 2017 restated on 2023 units).
3. Population Census Organisation, *Population of Administrative Units 1951-98* (Census Publication 161): population of every tehsil and district at the 1951, 1961, 1972, 1981 and 1998 censuses on the frame of the late 1990s and early 2000s.
   1 to 3 as parsed from the published PBS/PCO tables by Data Darbar (Hiba Sameen), warehouse tables census_panel_2017, census_panel_2023 and census_admin_units_1951_1998, release 2026-11-01, https://darbar.adaad.org/datasets/ (CC BY 4.0); spot-checked against the PBS PDF for Khyber Pakhtunkhwa.
4. Data Darbar, subdistrict_crosswalk_2017_2023 (grouping of 2017 and 2023 units into territory-covering groups). Every group re-verified against the PBS populations.
5. PBS Digital Census 2023 tehsil polygons as redistributed by Data Darbar (pbs_tehsils_2023.geojson), used for adjacency only.
6. US Census Bureau, Demobase Pakistan, PK_GEOG1_ADM4_2017 tehsil polygons (release 202401), used for adjacency in the 1998 -> 2017 layer and as an overlay check; geoBoundaries PAK ADM3 as a second check. Neither free layer is used as a source of weights (see VALIDATION.md section 5).
7. Event register: provincial notifications where found, Dawn, The News, Express Tribune and Wikipedia pages that cite them; each row carries its URL and a grade (verified, reported, unverified).

## Method in plain words
PBS did the hard part. In each census it printed, for every new tehsil, the population of the previous census on the new boundary. Dividing that figure by the old tehsil's population gives the share of the old tehsil that went to the new one, a PBS number divided by a PBS number. Where a tehsil's name survived and its population is identical in both tables, it is one to one. Where tehsils were split, merged, renamed or lost a strip of territory, the flows between old and new units are chosen so that both sets of published populations are reproduced exactly while opening as few unexpected links as possible (same-named pairs first, then pairs whose polygons touch). Where more than one allocation fits the tables equally well, the rows are marked medium confidence and the alternative is described in the note. Area weights use PBS's published areas of the new units, split between sources in proportion to people only where a new unit was formed from more than one old one. The 1998 -> 2023 table multiplies the two layers.

## How to use
R:
```r
source("code/apply_crosswalk.R")
cw <- read_crosswalk("output/crosswalk_tehsil_1998_to_2023.csv")
check_crosswalk(cw)       # weights sum to 1, totals conserved, PBS restated column reproduced where one exists
out <- apply_crosswalk(my1998data, cw, id = "unit_id_1998",
                       counts = c("schools"), rates = c("literacy_rate"), weight = "pop")
```
Stata:
```stata
do code/apply_crosswalk.do
use my1998data, clear
apply_crosswalk, cw("output/crosswalk_tehsil_1998_to_2023.csv") id(unit_id_1998) counts(schools) rates(literacy_rate)
```
Your data must carry the source unit id (unit_id_1998 = T98-nnnn, unit_id_2017 = T17-nnnn, or the district name for the district files). To get the id, join your unit names on (district, unit) in unit_master_1998.csv or unit_master_2017_all.csv, which keep PBS's spellings. The R function was run on all six tables on the build machine (R 4.3.3) and reproduces PBS's restated columns to floating-point precision. Stata was not available to me, so the Stata program was written to mirror the R function line by line; please run `check_crosswalk, cw("...")` once before first use and tell me about any error.

## Limits, in plain words
- The crosswalk links census frames. District and tehsil changes notified between censuses are dated in event_register.csv, but the weights only exist for the census frames, because only there did PBS publish populations on both old and new boundaries. Punjab's five districts of October 2022 (Murree, Talagang, Wazirabad, Kot Addu, Taunsa) and Balochistan's and KP's post-2017 districts that PBS did not tabulate separately in 2023 are in the event register but not in the crosswalk.
- Islamabad, AJK and Gilgit-Baltistan are excluded, to get the four provinces right first.
- The 1951-98 report lists 2001-era towns, not 1998 tehsils, for Karachi, Lahore and Peshawar; those three districts enter the 1998 layer as one unit each (Karachi as one unit was agreed; Peshawar loses nothing; Lahore loses its City/Cantt split).
- Rows marked medium conserve population exactly but the allocation within the group is an inference, not a PBS figure (4 of 598 rows in 1998 -> 2017, 82 of 612 in 2017 -> 2023, 91 of 678 in the chained table).
- karachi_division flags Karachi rows so users can collapse Karachi to one unit in any frame.

## Reproduce
```
pip install pandas pyarrow geopandas scipy
python build/01_unit_master.py && python build/02_crosswalk_pop.py && python build/03_resolve_lp.py && python build/02b_overlay.py && python build/04_area_weights.py && python build/05_district_and_validate.py
python build/06_unit_master_1998.py && python build/07_crosswalk_1998_2017.py && python build/08_crosswalk_1998_tables.py && python build/10_event_register.py && python build/09_lineage.py && python build/11_validation_1998_md.py
```
