#!/usr/bin/env bash
# Installs the pinned Python packages (requirements.txt).
set -e; cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
echo "Installed. Then: bash code/run_all.sh  (downloads about 4.5 GB of rasters on first run)"
