#!/bin/bash

set -euo pipefail

rm -rf constant/polyMesh postProcessing VTK log.* foam.foam
find . -mindepth 1 -maxdepth 1 -type d -regex '.*/[1-9][0-9]*' -exec rm -rf {} +
