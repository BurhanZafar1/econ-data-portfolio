#!/usr/bin/env bash
# Installs the pinned Python packages (requirements.txt). R (base R only) and poppler's pdftotext are optional.
set -e; cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
echo "Python packages installed. Download the raw inputs listed in raw/SOURCES.txt into raw/, then: bash build/run_all.sh"
