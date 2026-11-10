#!/usr/bin/env bash
# Master script: rebuilds every file in output/ and docs/ from raw/ in order, timing each step, then writes
# output/CHECKSUMS.sha256 and output/RUN_LOG.txt. Run from the project root:  bash build/run_all.sh
# Inputs that are not in the repository (size) are listed in raw/SOURCES.txt; setup.sh installs the Python packages.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=output/RUN_LOG.txt; mkdir -p output/figures build/intermediate
{
echo "run started $(date -u +'%Y-%m-%d %H:%M:%S UTC') on $(uname -srm), $(nproc) cpu, $(free -g | awk '/Mem/{print $2}') GB"
python3 --version; python3 -c "import pandas,numpy,scipy,geopandas,shapely; print('pandas',pandas.__version__,'numpy',numpy.__version__,'scipy',scipy.__version__,'geopandas',geopandas.__version__,'shapely',shapely.__version__)"
} | tee "$LOG"
T0=$(date +%s)
step () {  # step <script> : runs it, logs wall-clock seconds
  local s=$(date +%s); echo "== $1" | tee -a "$LOG"
  python3 "build/$1" > "build/intermediate/log_${1%.py}.txt" 2>&1 || { echo "FAILED: $1 (see build/intermediate/log_${1%.py}.txt)" | tee -a "$LOG"; tail -20 "build/intermediate/log_${1%.py}.txt"; exit 1; }
  echo "   $(( $(date +%s) - s )) s" | tee -a "$LOG"
}
# 2017 -> 2023 layer
step 01_unit_master.py; step 02_crosswalk_pop.py; step 03_resolve_lp.py; step 02c_resolve_2017_2023_milp.py; step 02b_overlay.py; step 04_area_weights.py; step 05_district_and_validate.py; step 05b_validation_md.py
# 1998 layer, lineage, event register
step 06_unit_master_1998.py; step 07_crosswalk_1998_2017.py; step 08_crosswalk_1998_tables.py; step 10_event_register.py; step 09_lineage.py; step 11_validation_1998_md.py
# back to 1951, census-day frames
step 12_population_panel.py; step 13_backward_district_crosswalk.py; step 14_census_day_1998_frame.py
if command -v pdftotext >/dev/null && [ -f raw/census1998_frames/national/pco_population_of_admin_units_1998/PCO_Population_of_Administrative_Units_1998.pdf ]; then step 15_census_day_frames_pub161.py; else echo "== 15 skipped (pdftotext or the scan missing; its output is not used)" | tee -a "$LOG"; fi
step 16_census_day_layers.py; step 17_census_day_report.py
# documentation and checks
step 19_weights_and_uncertainty.py; step 18_codebook.py
if command -v Rscript >/dev/null; then echo "== code/run_checks.R" | tee -a "$LOG"; Rscript code/run_checks.R > build/intermediate/log_run_checks_R.txt 2>&1 && grep -c "FALSE" build/intermediate/log_run_checks_R.txt | xargs -I{} sh -c '[ "{}" = "0" ] && echo "   all R checks pass" || { echo "   R CHECK FAILED"; exit 1; }' | tee -a "$LOG"; else echo "== R checks skipped (no Rscript)" | tee -a "$LOG"; fi
step 99_checksums.py
if python3 -c "import pytest" 2>/dev/null; then echo "== tests/" | tee -a "$LOG"; python3 -m pytest -q tests > build/intermediate/log_pytest.txt 2>&1 && tail -1 build/intermediate/log_pytest.txt | tee -a "$LOG" || { echo "   TESTS FAILED (build/intermediate/log_pytest.txt)" | tee -a "$LOG"; exit 1; }; else echo "== tests skipped (no pytest)" | tee -a "$LOG"; fi
echo "run finished $(date -u +'%Y-%m-%d %H:%M:%S UTC'); total $(( $(date +%s) - T0 )) s" | tee -a "$LOG"
