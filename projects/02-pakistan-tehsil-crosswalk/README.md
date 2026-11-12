# Pakistan tehsil and district crosswalk, Censuses 1951 to 2023

Fifth release (version 5.0), 10 November 2026. Prepared by Burhan Zafar (Whitman College) as research assistant work for Professor M. Yasir Khan (University of Pittsburgh). Release history in CHANGELOG.md; how to cite in CITATION.cff; licences in LICENSE-DATA.txt (CC BY 4.0) and LICENSE-CODE.txt (MIT).

## 1. Overview
Tables that move any tehsil- or district-level variable reported on one census frame of Pakistan's four provinces onto another, with a population weight and an area weight for every pair of units, and the documentation needed to judge every weight:

- 1998 tehsils (report frame) -> 2017 tehsils: 424 -> 535 units, 597 rows
- 2017 tehsils -> 2023 tehsils: 535 -> 590 units, 613 rows
- 1998 tehsils -> 2023 tehsils, the base-year table (424 -> 590 units, 678 rows, chained through 2017)
- the census-day 1998 tehsils (1 March 1998; 417 units in 118 districts and agencies) -> the report frame (450 rows) and -> 2023 (817 rows)
- the same at district level (114 -> 134 -> 135 districts; 118 census-day districts)
- the district maps of the 1951, 1961, 1972 and 1981 censuses -> 1998 and 2023 districts
- a population panel: every 2023 tehsil and district at all seven censuses, 1951 to 2023
- which tehsils became which districts, and when each district and tehsil change happened, with a source and a grade for every dated row

Everything in output/ and docs/ is rebuilt from raw/ by one command (section 5). Every number in the generated reports is read from the output files when the report is written.

To reproduce from scratch: run setup.sh (installs the pinned Python packages), download the inputs listed in raw/SOURCES.txt that are not in the repository, then run `bash build/run_all.sh`. About two minutes on a laptop.

## 2. Data availability and provenance
All inputs are public. No data were obtained under a licence that restricts redistribution; none were obtained from the authors of any paper. The person who built this package had access to every input through the URLs below and has the right to redistribute what is included (see LICENSE-DATA.txt for inherited terms). Access cost: none; the Lahore School of Economics repository and Open Data Pakistan require no registration; darbar.adaad.org requires none.

| Data | Files | Where obtained | Access | In package | Citation |
|---|---|---|---|---|---|
| Census 2017, Table 1 by district and tehsil (population 2017, area, population 1998 restated on 2017 units) | raw/census_panel_2017.parquet | https://darbar.adaad.org/data/warehouse/census_panel_2017.parquet (Data Darbar's parse of the PBS tables), accessed 3 Nov 2026 | open, CC BY 4.0 | no (see raw/SOURCES.txt) | Pakistan Bureau of Statistics (2017); Data Darbar (2026) |
| Census 2023, Table 1 by district and tehsil (population 2023, area, population 2017 restated on 2023 units) | raw/census_panel_2023.parquet | https://darbar.adaad.org/data/warehouse/census_panel_2023.parquet, accessed 3 Nov 2026 | open | no | Pakistan Bureau of Statistics (2023); Data Darbar (2026) |
| PCO, Population of Administrative Units 1951-98 (Census Publication 161), the PBS web table on the mid-2000s map | raw/census_admin_units_1951_1998.parquet; scan raw/census1998_frames/national/pbs_admin_units_1951_1998_webtable/ | https://darbar.adaad.org/data/warehouse/census_admin_units_1951_1998.parquet, accessed 4 Nov 2026; PBS PDF via Lahore School repository | open | parquet no; PDF yes | Population Census Organisation (2002) |
| PCO Census Publication 161, January 2002, scan of the printed report (census-day frame; Tables 2 to 6; Annexures A to D) | raw/census1998_frames/national/pco_population_of_admin_units_1998/PCO_Population_of_Administrative_Units_1998.pdf (15.8 MB) | https://repository.lahoreschool.edu.pk/server/api/core/bitstreams/59ce27e7-3b4e-401b-9637-cf46d5bde2d0/content, accessed 5 Nov 2026 | open | yes | Population Census Organisation (2002) |
| Hand transcriptions of Publication 161 Tables 2, 3, 5 and 6 | raw/census1998_frames/transcribed/*.csv | transcribed from the page images in this project, 9 Nov 2026; every province, division and district sum checked against the printed totals | - | yes | this package |
| Government of the Punjab, 1998 census population by district and tehsil (census-day frame) | raw/punjab1998/punjab_1998_tehsil_table.xls | Punjab Government table republished on Open Data Pakistan, dataset 14ed2f82-c9d1-4e49-be7d-0ae5fecbefe6, accessed 5 Nov 2026 | open | yes | Government of the Punjab (1998) |
| Data Darbar grouping of 2017 and 2023 units (used to form groups; every group re-verified against PBS populations) | raw/subdistrict_crosswalk_2017_2023.parquet, district_crosswalk_2017_2023.parquet, census_unit_map.parquet | https://darbar.adaad.org/data/warehouse/, accessed 3 Nov 2026 | open | no | Data Darbar (2026) |
| PBS Digital Census 2023 tehsil and district polygons (adjacency prior, areas, figure) | raw/pbs_tehsils_2023.geojson, pbs_districts_2023.geojson | https://darbar.adaad.org/data/boundaries/, accessed 3 Nov 2026 | open | no | Pakistan Bureau of Statistics (2023), via Data Darbar |
| US Census Bureau Demobase Pakistan, 2017 tehsil polygons (adjacency prior for the 1998 -> 2017 layer; overlay check) | raw/demobase/Pakistan.gdb, layer PK_GEOG1_ADM4_2017_uscb_202401 | https://www.census.gov/geographies/mapping-files/time-series/demo/international-programs/demobase.html (pakistan-uscb-20241.zip), accessed 4 Nov 2026 | public domain | no | US Census Bureau (2024) |
| geoBoundaries PAK ADM2 and ADM3 (overlay check only) | raw/gb_PAK_ADM2_2017.geojson, gb_PAK_ADM3_2017.geojson | https://github.com/wmgeolab/geoBoundaries (commit 9469f09), accessed 3 Nov 2026 | CC BY 4.0 | no | Runfola et al. (2020) |
| Event register and lineage sources: provincial notifications where found, Dawn, The News, Express Tribune, Balochistan High Court, Wikipedia pages that cite notifications | URLs in output/event_register.csv and output/district_lineage_1951_1998.csv, one per row, with the date read | web, Nov 2026 | open | URLs | per row |
| Catalogue of about 350 scanned 1998 census publications (District Census Reports, bulletins) with download links | raw/census1998_frames/SOURCES_1998_frames.csv, lahoreschool_dspace_1998_census_catalog.csv | Lahore School of Economics DSpace, Nov 2026 | open | yes | - |

Files not in the repository are excluded for size only (the parquet tables, the geodatabase and the large scans; about 500 MB together); raw/SOURCES.txt gives each URL. The Punjab table, the Publication 161 scan, the transcriptions and the catalogues are included.

## 3. Dataset list
Every file in output/ is described column by column in docs/codebook.csv (machine-readable: file, column, type, units, missing count, description, producing script) and in prose in docs/DATA_DICTIONARY.md. The main ones:

```
output/crosswalk_tehsil_1998_to_2023.csv      base-year table: every 1998 report-frame unit onto the 2023 frame (678 rows)
output/crosswalk_tehsil_1998_to_2017.csv      1998 -> 2017 (597 rows)
output/crosswalk_tehsil_2017_to_2023.csv      2017 -> 2023 (613 rows)
output/crosswalk_district_1998_to_2023.csv, _1998_to_2017.csv, _2017_to_2023.csv   district level (151, 142, 143 rows)
output/unit_master_1998census_all.csv         the census-day 1998 frame, all provinces (417 units), with PCO's 1951-1981 restatements on census-day units
output/crosswalk_tehsil_1998census_to_pcoframe.csv, _to_2023.csv   census-day units onto the report frame (450 rows) and onto 2023 (817 rows)
output/crosswalk_district_1998census_to_pcoframe.csv, _to_2023.csv   district level (127, 186 rows)
output/new_district_lineage.csv               every district new in 2017 or 2023: the earlier tehsils that formed it, shares, year, source
output/tehsil_district_membership.csv         every tehsil's district in the later frame(s), with the share of its people there
output/event_register.csv                     dated district and tehsil changes 1998-2026 with sources (291 rows: 97 verified, 105 reported, 89 unverified)
output/population_panel_1998_frame*.csv       1951, 1961, 1972, 1981, 1998 populations on the 1998 report frame (PCO), tehsil and district
output/population_panel_2023_frame*.csv       all seven censuses 1951-2023 on the 2023 tehsils (590) and districts (135)
output/district_lineage_1951_1998.csv         when each 1998 district was created and from what, with sources (128 rows)
output/district_frames_by_census.csv          the district map at each census, 1951-1998
output/crosswalk_district_historical_to_1998.csv, _to_2023.csv   district crosswalk from the 1951-1981 maps (479 and 604 rows)
output/unit_master_1998.csv, district_master_1998.csv, unit_master_2017_all.csv, unit_master_2023_all.csv   the frames as published
output/weights_and_uncertainty_by_layer.csv, uncertainty_by_target_unit.csv   weight distribution and per-unit uncertainty (docs/WEIGHTS_AND_UNCERTAINTY.md)
output/validation_summary*.json               the numbers behind the validation reports
output/CHECKSUMS.sha256, RUN_LOG.txt          SHA-256 of every output and doc; timings of the last build
output/figures/fig_crosswalk_uncertainty_map.png
code/apply_crosswalk.R, apply_crosswalk.do, run_checks.R   apply in R (base R) or Stata (14+); R checks of every table
```
Keys: unit_id_1998 (T98-nnnn), unit_id_2017 (T17-nnnn), unit_id_1998census (T98C-PP-nnn), unit_id_2023 (PBS dds_id); district files are keyed on district names as PBS prints them; every table has a unique, non-missing key (checked in build/18_codebook.py). Weights sum to one over the targets of each source unit in every table (checked in the build and by code/run_checks.R).

## 4. Computational requirements
- Software used for this release: Python 3.13.18 with the packages pinned in requirements.txt (pandas 3.0.5, numpy 2.5.3, scipy 1.18.1 with the HiGHS solver it bundles, geopandas 1.2.0, shapely 2.2.0, pyproj 3.8.0, pyogrio 0.13.0, lxml 6.1.3, matplotlib 3.11.2); R 4.3.3 (base R only) for code/run_checks.R; poppler pdftotext 24.02 for the optional build/15. Stata was not available; code/apply_crosswalk.do was written to mirror the R function and has not been executed (see section 7).
- Hardware and run time: Ubuntu 24.04 on 2 cpu and 7 GB memory; the whole build takes under 2 minutes (output/RUN_LOG.txt gives each step; the longest, build/16, 24 seconds). Storage: 2.5 MB of outputs; about 520 MB of raw inputs.
- Randomness: no pseudo-random number generator is used anywhere; the integer programmes are deterministic given the inputs (HiGHS, time limit 60 s per group, never reached).
- Network: none needed after the raw downloads.

## 5. Instructions to replicators
1. `bash setup.sh` (or `pip install -r requirements.txt`).
2. Download the files listed in raw/SOURCES.txt into raw/ (names as given there).
3. `bash build/run_all.sh` from the project root. It runs build/01 to build/19 in order, writes a log per step to build/intermediate/, regenerates every file in output/ and every generated document in docs/, runs the R checks if Rscript is present, and writes output/CHECKSUMS.sha256.
4. Compare with the released checksums: `sha256sum -c output/CHECKSUMS.sha256` (generated documents carry the build date, so those lines differ by date only).
5. `python -m pytest -q tests` re-derives the key properties from the CSVs alone (weights sum to one, population conserved, PBS restated columns reproduced, every unit covered, transcriptions add up, codebook complete, checksums match); run_all.sh runs it at the end when pytest is installed.

No manual step is involved. build/15 (the OCR text extract of the scan) is skipped if pdftotext is absent; its output is kept only to show why the scan had to be transcribed by hand and is used nowhere.

## 6. Programs and the outputs they produce
| Program | Produces |
|---|---|
| build/01_unit_master.py | unit_master_2017_all.csv, unit_master_2023_all.csv, intermediate unit lists |
| build/02_crosswalk_pop.py, 03_resolve_lp.py | first-release 2017 -> 2023 flows (kept as build/intermediate/crosswalk_tehsil_2017_to_2023_pop_v1.csv for comparison) |
| build/02c_resolve_2017_2023_milp.py | 2017 -> 2023 flows with the common resolver (build/crosswalk_lib.py) |
| build/02b_overlay.py | check_overlay_mismatches.csv |
| build/04_area_weights.py | crosswalk_tehsil_2017_to_2023.csv (area weights added) |
| build/05_district_and_validate.py, 05b_validation_md.py | crosswalk_district_2017_to_2023.csv, validation_summary.json, docs/VALIDATION.md |
| build/06_unit_master_1998.py | unit_master_1998.csv, district_master_1998.csv, research_notes_1998_frame.csv |
| build/07_crosswalk_1998_2017.py, 08_crosswalk_1998_tables.py | crosswalk_tehsil_1998_to_2017.csv, _1998_to_2023.csv, district versions, validation_summary_1998.json |
| build/09_lineage.py | new_district_lineage.csv, tehsil_district_membership.csv |
| build/10_event_register.py | event_register.csv, docs/EVENT_REGISTER.md |
| build/11_validation_1998_md.py | docs/VALIDATION_1998.md |
| build/12_population_panel.py | population_panel_1998_frame*.csv, population_panel_2023_frame*.csv, validation_summary_panel.json |
| build/13_backward_district_crosswalk.py | district_lineage_1951_1998.csv, district_frames_by_census.csv, crosswalk_district_historical_to_1998.csv, _to_2023.csv, validation_summary_backward.json |
| build/14_census_day_1998_frame.py | unit_master_1998census_punjab.csv, crosswalk_tehsil_1998census_to_pcoframe_punjab.csv, _to_2023_punjab.csv |
| build/15_census_day_frames_pub161.py | UNVERIFIED_ocr_extract_pub161_tehsil_lines.csv (not used) |
| build/16_census_day_layers.py, 17_census_day_report.py | unit_master_1998census_all.csv, crosswalk_tehsil_1998census_to_pcoframe.csv, _to_2023.csv, district versions, validation_summary_censusday.json, docs/CENSUS_DAY_1998.md |
| build/19_weights_and_uncertainty.py | weights_and_uncertainty_by_layer.csv, uncertainty_by_target_unit.csv, figures/fig_crosswalk_uncertainty_map.png, docs/WEIGHTS_AND_UNCERTAINTY.md |
| build/18_codebook.py | docs/codebook.csv; refreshes row counts in docs/DATA_DICTIONARY.md |
| build/99_checksums.py | output/CHECKSUMS.sha256 |
| tests/test_outputs.py | pytest checks of the released tables (no rebuild needed) |
| code/run_checks.R | prints the weight, conservation and PBS-restatement checks for all ten crosswalk tables |

Hand-written documents: this README, docs/DATA_DICTIONARY.md (prose; row counts refreshed by the build), docs/BACKWARD_EXTENSION.md, docs/STANDARDS_RESEARCH.md, CHANGELOG.md. Every other document in docs/ is generated.

## 7. What is not in the package, and other omissions
- Stata: code/apply_crosswalk.do has not been run (no Stata licence on the build machine). It mirrors code/apply_crosswalk.R line by line; please run `check_crosswalk, cw("output/crosswalk_tehsil_1998_to_2023.csv")` once before first use and report any error. The Stata program handles the tables whose target is 2017 or 2023; the two census-day -> report-frame tables carry population weights only and are for R.
- Islamabad, Azad Jammu and Kashmir and Gilgit-Baltistan are excluded from the crosswalk (the four provinces first, as asked). Islamabad is present in the unit masters.
- Changes notified between censuses are dated in event_register.csv but have weights only where PBS published populations on both old and new boundaries, i.e. at the census frames. Punjab's five districts of October 2022 (Murree, Talagang, Wazirabad, Kot Addu, Taunsa) and the Balochistan and KP districts PBS did not tabulate separately in 2023 are in the register, not in the crosswalk.
- No tehsil-level crosswalk exists from the 1951-1981 maps (the tehsil lists of those censuses are in District Census Reports that are not online); the district maps are reconstructed and the 1998-frame tehsil panel is the substitute (docs/BACKWARD_EXTENSION.md).
- Karachi is one unit in the 1998 report frame (the report lists 2001 towns), as agreed; the five census-day Karachi districts map to it. Lahore and Peshawar likewise enter the 1998 report frame as one unit each.
- Annexures A to D of Publication 161 (PCO's own register of changes 1981-1998) are extracted as text but not transcribed.
- 89 of 291 event-register rows and 7 of 128 lineage rows are graded unverified (no notification or dated report found); they are kept with that grade rather than dropped.

## 8. Method in plain words
PBS did the hard part. In each census it printed, for every new tehsil, the population of the previous census on the new boundary. Dividing that figure by the old tehsil's population gives the share of the old tehsil that went to the new one, a PBS number divided by a PBS number. Where a tehsil's name survived and its population is identical in both tables, it is one to one. Where tehsils were split, merged, renamed or lost a strip of territory, the flows between old and new units are chosen so that both sets of published populations are reproduced exactly while opening as few unexpected links as possible (same-named pairs first, then pairs whose polygons touch; a small integer programme per district group, build/crosswalk_lib.py). Every link that is not a same-name pair is then tested: if the tables cannot balance without it, it is forced (confidence high); if another allocation would balance but is less plausible given adjacency, it is an inference (medium); if an equally plausible alternative exists, it is ambiguous (low) and the note says so. Area weights use PBS's published areas of the new units, split between sources in proportion to people only where a new unit was formed from more than one old one. The 1998 -> 2023 table multiplies the two layers. The census-day layer links the tehsils as they stood on 1 March 1998 (transcribed from the printed report) to the report frame with the same procedure.

Counts of inferred rows: 1998 -> 2017, 58 medium and 4 low of 597; 2017 -> 2023, 31 medium and 0 low of 613; chained 1998 -> 2023, 94 medium and 4 low of 678; census-day -> report frame, 16 medium and 2 low of 450. The share of population that moves on inferred rows, the distribution of weights, and a per-unit uncertainty bound are in docs/WEIGHTS_AND_UNCERTAINTY.md. District-level grades describe the district flow itself (the weakest tehsil row that crosses a district line), since inferences between tehsils of one district leave the district total untouched.

## 9. How to use
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
Your data must carry the source unit id (unit_id_1998 = T98-nnnn, unit_id_2017 = T17-nnnn, unit_id_1998census = T98C-PP-nnn, or the district name for the district files). To get the id, join your unit names on (district, unit) in the unit master of that frame, which keeps PBS's spellings. Crosswalk counts (stocks); rebuild rates and shares from numerator and denominator counts, or pass them as rates to be averaged with the people moved as weights. Use the most disaggregated table your data allow (tehsil rather than district). Results that matter should be reported with both the population and the area weights, and, where the uncertain share of a unit is large (output/uncertainty_by_target_unit.csv), with and without those units.

## 10. Limits, in plain words
- "1998 report frame" means the frame of PCO's 1951-98 report as issued by PBS, which carries the 1998 populations on the administrative map of the mid-2000s. The census-day frame (1 March 1998) is a separate layer; docs/CENSUS_DAY_1998.md lists every district that differs between the two.
- A crosswalk built from counts allocates a variable in proportion to people (or area). A variable distributed more unevenly than people over a split unit will be allocated with more error; nothing in the published tables can fix that.
- Every row not equal to a published figure is graded, and the grade is carried through every chained and district table. Nothing is dropped, interpolated or modelled; all rows conserve population exactly.
- karachi_division flags Karachi rows so users can collapse Karachi to one unit in any frame.

## 11. References
- Pakistan Bureau of Statistics (2017). Population and Housing Census 2017, Table 1: Area, population by sex, sex ratio, population density, urban proportion, household size and annual growth rate, by district and tehsil. Islamabad.
- Pakistan Bureau of Statistics (2023). 7th Population and Housing Census 2023, Table 1 by district and tehsil; Digital Census 2023 administrative boundaries. Islamabad.
- Population Census Organisation (2002). Population of Administrative Units 1951-98 (as on 1st March 1998), Census Publication No. 161. Statistics Division, Government of Pakistan, Islamabad, January 2002.
- Government of the Punjab (1998). Population of Punjab by district and tehsil, 1998 census (Bureau of Statistics table, republished on Open Data Pakistan).
- Data Darbar / Hiba Sameen (2026). Pakistan census warehouse tables and PBS boundary files, release 2026-11-01. https://darbar.adaad.org/datasets/ (CC BY 4.0).
- US Census Bureau (2024). Demobase Pakistan, release 202401.
- Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. PLoS ONE 15(4): e0231866.
- Huangfu, Q. and Hall, J. A. J. (2018). Parallelizing the dual revised simplex method. Mathematical Programming Computation 10, 119-142 (HiGHS, used through scipy.optimize.milp).
- Jordahl, K. et al. GeoPandas; Gillies, S. et al. Shapely; Virtanen, P. et al. (2020) SciPy 1.0, Nature Methods 17, 261-272.
- Standards followed: AEA Data and Code Availability Policy; Social Science Data Editors, Template README for Social Science Replication Packages; Gentzkow and Shapiro (2014), Code and Data for the Social Sciences; Eckert, Gvirtz, Liang and Peters (2020) and Ferrara, Testa and Zhou (2024) on crosswalk documentation (docs/STANDARDS_RESEARCH.md).
