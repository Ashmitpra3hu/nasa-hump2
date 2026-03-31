#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/scripts/build_nasa_hump_case.sh"

docker run --rm \
  -v "${ROOT_DIR}:/home/openfoam" \
  -w /home/openfoam \
  --entrypoint /bin/bash \
  opencfd/openfoam-default \
  -lc "set -euo pipefail; simpleFoam -case data/NASA_2DWMH > data/NASA_2DWMH/log.run"
