#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PV_PYTHON="/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython"

for mode in \
  velocity \
  velocity_surface \
  pressure \
  pressure_surface \
  streamlines \
  mesh_wireframe \
  wall_patch
do
  "${PV_PYTHON}" "${ROOT_DIR}/scripts/render_nasa_hump_paraview.py" "${mode}"
done
