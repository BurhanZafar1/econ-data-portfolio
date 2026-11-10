#!/usr/bin/env bash
# Master script: rebuilds every file in output/ and the generated docs from raw/ in order, timing each step, then
# writes output/CHECKSUMS.sha256 and output/RUN_LOG.txt. Run from the project root:  bash code/run_all.sh
# Downloads (01, 01b) are skipped when the raw files are present and verified. 06 needs the crosswalk project's
# output folder (../02-pakistan-tehsil-crosswalk/output, or set CROSSWALK_OUTPUT).
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=output/RUN_LOG.txt; mkdir -p output/figures output/rankings output/logs
{
echo "run started $(date -u +'%Y-%m-%d %H:%M:%S UTC') on $(uname -srm), $(nproc) cpu, $(free -g | awk '/Mem/{print $2}') GB"
python3 --version; python3 -c "import pandas,numpy,geopandas,rasterio,exactextract,pyproj,matplotlib; print('pandas',pandas.__version__,'numpy',numpy.__version__,'geopandas',geopandas.__version__,'rasterio',rasterio.__version__,'exactextract',exactextract.__version__,'pyproj',pyproj.__version__,'matplotlib',matplotlib.__version__)"
} | tee "$LOG"
T0=$(date +%s)
step () { local s=$(date +%s); echo "== $1" | tee -a "$LOG"
  python3 "code/$1" > "output/logs/log_${1%.py}.txt" 2>&1 || { echo "FAILED: $1 (see output/logs/log_${1%.py}.txt)" | tee -a "$LOG"; tail -20 "output/logs/log_${1%.py}.txt"; exit 1; }
  echo "   $(( $(date +%s) - s )) s" | tee -a "$LOG"; }
step 01_download_nightlights.py; step 01b_download_viirs_like.py
step 02_prepare_boundaries.py; step 03_zonal_stats.py; step 04_zonal_stats_viirs_like.py; step 05_checks.py
step 06_merge_with_census.py; step 07_district_rankings.py; step 08_rankings_report.py; step 09_codebook.py; step 99_checksums.py
if python3 -c "import pytest" 2>/dev/null; then echo "== tests/" | tee -a "$LOG"; python3 -m pytest -q tests > output/logs/log_pytest.txt 2>&1 && tail -1 output/logs/log_pytest.txt | tee -a "$LOG" || { echo "   TESTS FAILED (output/logs/log_pytest.txt)" | tee -a "$LOG"; exit 1; }; else echo "== tests skipped (no pytest)" | tee -a "$LOG"; fi
echo "run finished $(date -u +'%Y-%m-%d %H:%M:%S UTC'); total $(( $(date +%s) - T0 )) s" | tee -a "$LOG"
