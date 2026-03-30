#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MPLCONFIGDIR="${ROOT_DIR}/docs/.mplconfig" python3 "${ROOT_DIR}/scripts/make_nasa_hump_figures.py"
