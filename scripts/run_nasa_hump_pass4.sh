#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"
python3 scripts/import_nasa_hump_experimental_data.py
MPLCONFIGDIR="${ROOT_DIR}/docs/.mplconfig" python3 scripts/make_nasa_hump_pass4_figures.py
