# Changelog

All releases are commits in https://github.com/BurhanZafar1/econ-data-portfolio (projects/02-pakistan-tehsil-crosswalk). Output checksums for each release are in output/CHECKSUMS.sha256 at that commit.

## 5.0, 10 November 2026
- Census-day 1998 frame for Sindh, Khyber Pakhtunkhwa, FATA and Balochistan: Tables 2, 3, 5 and 6 of PCO Census Publication 161 transcribed by hand from the scanned pages (raw/census1998_frames/transcribed/), every sum checked, linked to the report frame and to 2023 (build/16; unit_master_1998census_all.csv, crosswalk_tehsil_1998census_to_pcoframe.csv, _to_2023.csv, district versions; docs/CENSUS_DAY_1998.md). Joined with the Punjab layer of release 4 into country-wide tables (417 units, 118 districts).
- District-level confidence now grades the district flow itself (the weakest tehsil row that crosses a district line), not the weakest row inside the district; applied in every district table (crosswalk_lib.district_confidence).
- Resolver: a name printed more than once (Quetta Tehsil in two parts) is pinned to its equal-population partner when that equality singles out one pair.
- Replication package: build/run_all.sh (master script with timings and logs), setup.sh and pinned requirements.txt, output/CHECKSUMS.sha256, docs/codebook.csv (machine-readable, every column of every file), docs/WEIGHTS_AND_UNCERTAINTY.md (weight distribution, population mapped, per-unit uncertainty bound, map), code/run_checks.R, LICENSE-DATA.txt (CC BY 4.0) and LICENSE-CODE.txt (MIT), CITATION.cff, this changelog, and a README restructured along the Social Science Data Editors template (data availability and provenance, rights, computational requirements, program-to-output map, omissions).
- R and Stata helpers accept the census-day frames.
- docs/STANDARDS_RESEARCH.md: the standards the package was checked against, with sources.

## 4.0, 5 November 2026 (commit 2c8a0d6)
- One resolver for every layer with a three-way grade of every row (forced / inferred / ambiguous); 2017 to 2023 re-solved on the same method.
- Census-day 1998 frame for Punjab (118 tehsils, Punjab Government table) linked to the report frame and to 2023; district_1998_at_census column (Umerkot, Nushki).
- FR Lakki Marwat and FR Tank separate from 1972 per PCO; second research pass on undated tehsils; catalogue of the PCO 1998 census scans with download links; text extract of Census Publication 161 and its 1981-98 change annexures; R and Stata helpers for the historical district tables.

## 3.0, 5 November 2026 (commit 3f67a97)
- Back to the first census: PCO's 1951-1981 restatements carried to the 2023 frame (population panels), district maps of each census reconstructed from a sourced lineage table, district crosswalk from the 1951-1981 maps to 1998 and 2023 (docs/BACKWARD_EXTENSION.md).

## 2.0, 4 November 2026
- The 1998 layer (1998 -> 2017 and chained 1998 -> 2023), new-district lineage, tehsil-district membership, and the event register of dated changes with sources.

## 1.0, 3 November 2026
- 2017 -> 2023 tehsil and district crosswalk with population and area weights, validation report, R and Stata apply functions.
