# Case Pattern Summary

## Surviving Repository Conventions

- Benchmark cases live under `data/<family>/<case-name>` or `data/<case-name>`.
- A case directory usually contains OpenFOAM folders `0/`, `constant/`, and `system/`.
- Lightweight metadata is often stored in top-level files such as `caseDef` and `fieldDef`.
- Runtime artifacts are written back into the case directory, commonly as:
  - `log.run`
  - `log.postProcess`
  - `foam.foam`
  - `postProcessing/...`
  - `convergencePlots/...`
- Helper shell scripts often sit in the case directory for direct execution, while repository-level scripts perform broader automation.

## Metadata Patterns

- `caseDef` stores concise geometric or physical parameters for the case.
- `fieldDef` groups field names used by residual, probe, graph, or visualization dictionaries.
- Function-object dictionaries in `system/` often `#include "../fieldDef"` or `#include "../caseDef"` so field and parameter names stay centralized.

## OpenFOAM Dictionary Patterns

- `system/controlDict` commonly:
  - runs `simpleFoam` steady-state cases
  - writes ASCII output
  - includes function objects for residuals, probes, or line sampling
- `system/fvSchemes` and `system/fvSolution` use conventional steady RANS SIMPLE settings.
- Post-processing dictionaries are split into small files such as `residuals`, `singleGraph_x0`, `faceValues`, `wallValues`, or `sampleDict`.
- Existing cases favor readable dictionaries with comments and explicit patch naming rather than highly compressed generated files.

## Geometry and Mesh Patterns

- Geometry-driven 2D cases use a thin third dimension with `empty` front/back patches.
- Structured meshes are commonly generated with `blockMesh`, often with spline edges to represent curved walls.
- Mesh generation inputs are stored directly in `system/blockMeshDict`, sometimes produced from many spline points.

## Script Patterns

- Shell scripts are short, readable, and imperative.
- Existing scripts typically:
  - use `#!/bin/bash`
  - enable `set -e`
  - run the solver
  - then run post-processing steps
- Repository-level automation is sparse, so adding clear reproducible scripts at `scripts/` is consistent with the repo’s lightweight style.

## Implications For The New NASA Hump Case

- The reconstructed case should live at `data/NASA_2DWMH`.
- It should include `caseDef`, `fieldDef`, `0/`, `constant/`, and `system/` in the same spirit as the surviving cases.
- It should generate its own mesh through `blockMesh`, use `simpleFoam` for a baseline RANS run, and write post-processing output into `postProcessing/`.
- It should expose a `.foam` file, logs, line-sampling data, wall/patch exports, and repository-level scripts that rebuild and rerun the workflow through Docker.
