#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker run --rm \
  -v "${ROOT_DIR}:/home/openfoam" \
  --entrypoint /bin/bash \
  opencfd/openfoam-default \
  -lc "export HOME=/home/openfoam; export WM_PROJECT_USER_DIR=/home/openfoam; source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /home/openfoam/ml_models/kOmegaSSTML && wclean libso && wmake libso"
