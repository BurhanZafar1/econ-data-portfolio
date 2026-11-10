# Changelog

Releases are commits in https://github.com/BurhanZafar1/econ-data-portfolio (projects/04-pakistan-night-lights). Output checksums for each release are in output/CHECKSUMS.sha256 at that commit.

## 2.0, 10 November 2026
- District rankings by light for every year under three exclusion rules (all districts; without Islamabad, Lahore, Peshawar, Quetta and Karachi; without those and the 21 districts touching them), three measures, both series, with mobility statistics, three-year-window robustness, figures and a generated note (code/07, 08; docs/RANKINGS.md).
- Inverse hyperbolic sine columns (asinh_*_sum_km2) beside log(1 + x) in every light table.
- Series B download script with md5 verification against the Dataverse record (code/01b).
- Replication package: code/run_all.sh (master script with timings and logs), setup.sh and pinned requirements.txt, output/CHECKSUMS.sha256, docs/codebook.csv (every column of every file), LICENSE-DATA.txt (CC BY 4.0) and LICENSE-CODE.txt (MIT), CITATION.cff, this changelog, and a README restructured along the Social Science Data Editors template (data availability and provenance per source and per year, rights, computational requirements, program-to-output map, omissions).

## 1.1, 5 November 2026 (commit 2c8a0d6)
- Merged analysis panel (both light series plus census populations 1951-2023 on 2023 units, light per thousand people in census years); dim-end check (DN > 7 floor) in the validation report.

## 1.0, 5 November 2026 (commit 3f67a97)
- Series A (Li et al. harmonized DMSP-VIIRS, 1992-2024) and series B (Chen et al. NPP-VIIRS-like V2, 1992-2025) exact area-weighted statistics for every Census 2023 tehsil and district; boundary repair and geodesic areas; validation report.
