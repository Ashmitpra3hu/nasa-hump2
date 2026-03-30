#!/bin/bash

set -euo pipefail

simpleFoam -postProcess -latestTime -func wallShearStress > log.wallShearStress
postProcess -latestTime -dict system/bottomValues > log.bottomValues
foamToVTK -ascii > log.foamToVTK
