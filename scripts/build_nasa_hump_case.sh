#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="${ROOT_DIR}/data/NASA_2DWMH"

python3 "${ROOT_DIR}/scripts/generate_nasa_hump_blockmesh.py"

mkdir -p \
  "${ROOT_DIR}/docs/data" \
  "${ROOT_DIR}/docs/figures" \
  "${ROOT_DIR}/documentation_src/data_second_pass" \
  "${ROOT_DIR}/documentation_src/figures_second_pass" \
  "${ROOT_DIR}/documentation"

docker run --rm \
  -v "${ROOT_DIR}:/home/openfoam" \
  -w /home/openfoam \
  --entrypoint /bin/bash \
  opencfd/openfoam-default \
  -lc "set -euo pipefail; rm -rf data/NASA_2DWMH/constant/polyMesh data/NASA_2DWMH/postProcessing data/NASA_2DWMH/VTK data/NASA_2DWMH/log.* data/NASA_2DWMH/foam.foam; find data/NASA_2DWMH -mindepth 1 -maxdepth 1 -type d -regex '.*/[1-9][0-9]*' -exec rm -rf {} +; mkdir -p data/NASA_2DWMH; blockMesh -case data/NASA_2DWMH > data/NASA_2DWMH/log.blockMesh; checkMesh -case data/NASA_2DWMH > data/NASA_2DWMH/log.checkMesh; postProcess -case data/NASA_2DWMH -func writeCellCentres -time 0 > data/NASA_2DWMH/log.writeCellCentres"

touch "${CASE_DIR}/foam.foam"
