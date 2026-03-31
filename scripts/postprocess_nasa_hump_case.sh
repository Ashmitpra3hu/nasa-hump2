#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker run --rm \
  -v "${ROOT_DIR}:/home/openfoam" \
  -w /home/openfoam \
  --entrypoint /bin/bash \
  opencfd/openfoam-default \
  -lc "set -euo pipefail; simpleFoam -case data/NASA_2DWMH -postProcess -latestTime -func wallShearStress > data/NASA_2DWMH/log.wallShearStress; postProcess -case data/NASA_2DWMH -latestTime -func 'grad(U)' > data/NASA_2DWMH/log.gradU; postProcess -case data/NASA_2DWMH -latestTime -dict system/bottomValues > data/NASA_2DWMH/log.bottomValues; foamToVTK -case data/NASA_2DWMH -ascii > data/NASA_2DWMH/log.foamToVTK"
