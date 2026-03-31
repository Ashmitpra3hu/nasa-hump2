# First-Pass Diagnosis

## Scope Of This Diagnosis

This file evaluates the existing first-pass NASA hump reconstruction already present in the working tree. It does not restart the reconstruction from scratch. The goal is to identify what is usable, what is weak, and what should be improved honestly during the second pass.

## What Exists From Pass 1

- A reconstructed OpenFOAM case at `data/NASA_2DWMH`.
- Dockerized workflow scripts:
  - `scripts/build_nasa_hump_case.sh`
  - `scripts/run_nasa_hump_case.sh`
  - `scripts/postprocess_nasa_hump_case.sh`
  - `scripts/make_figures.sh`
  - `scripts/build_report.sh`
  - `scripts/evaluate_reconstructed_nasa_case.py`
- A generated `blockMeshDict`, baseline SST setup, post-processing logs, `foam.foam`, and VTK export.
- First-pass plots in `docs/figures/`.
- First-pass sampled and summary data in `docs/data/`.
- First-pass LaTeX report source at `documentation/main.tex` and compiled PDF at `documentation/build/main.pdf`.

## What Worked In Pass 1

- The repository now contains a complete NASA hump case structure in the same broad style as the surviving cases: `0/`, `constant/`, `system/`, metadata files, helper scripts, logs, and ParaView-friendly output.
- The case runs through Dockerized OpenFOAM rather than a host-native OpenFOAM installation.
- The workflow is reproducible enough to rebuild the mesh, run the solver, post-process, create plots, and evaluate the case.
- The case writes station sampling dictionaries for the webpage profile stations `x/c = -2.14, 0.65, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3`.
- A baseline accuracy run exists, which is essential for an honest second pass.

## What Failed Or Fell Short

- The first-pass evaluation score is poor for a validation case: `0.2338504550` from `docs/data/reconstructed_nasa_score.json`.
- The solver run ended at only `80` SIMPLE iterations, which is likely too short for a separated-flow RANS case with a long recirculation region.
- The top boundary was modeled as a flat slip wall, even though the allowed NASA page explicitly states that the CFD upper boundary includes a shaped contour to approximate blockage from the experimental end plates.
- The inflow turbulence was imposed as uniform `k` and `omega`, while the allowed page describes an incoming fully turbulent boundary layer of about `35 mm` thickness at `x/c = -2.14`.
- The first-pass hump geometry is an original smooth reconstruction, but it is intentionally simplified and may not reproduce the experimental curvature distribution closely enough to generate the correct adverse pressure gradient.
- The first-pass mesh is a single structured block with global grading only. That is easy to reproduce, but it is weak for:
  - near-wall resolution around the hump crest and downstream recovery region
  - separation shear-layer resolution
  - accurate extraction of wall quantities such as `Cp` and `Cf`
- The first-pass post-processing covered velocity profiles, residual history, wall-related quantities, and ParaView screenshots, but it did not clearly reimplement every graph family visible on the allowed webpage in a second-pass-ready, auditable package.

## Likely Sources Of MAE Or Mismatch

## 1. Inflow Condition Weakness

The allowed page says the incoming turbulent boundary layer at `x/c = -2.14` is about `35 mm`, or about `8%` of the `0.42 m` chord. A uniform inlet profile makes it hard for the solver to develop the correct upstream state before the hump, even with upstream run length.

## 2. Upper-Boundary Simplification

The page states the upper boundary is a slip wall with a contour to account approximately for blockage. A flat top wall preserves the slip condition but misses the contour-induced pressure redistribution.

## 3. Mesh Resolution And Distribution

The single-block mesh uses a large global cell count, but it does not target the regions that matter most for this case:
- hump leading-edge acceleration
- crest and immediate adverse-pressure-gradient region
- separated shear layer
- reattachment and recovery

## 4. Solver Convergence Depth

Residuals in `docs/data/summary.json` are not low enough to treat the field as well converged, and the wall-shear summary still reports no clear separation point. That suggests the field is still evolving.

## 5. Geometry Fidelity Limits

Because only the allowed webpage and local patterns were used, the hump shape was reconstructed defensibly but not exactly. This can move the pressure plateau, separation onset, and reattachment position.

## Graph Coverage Gaps

- The first-pass report contains plots and ParaView views, but the graph families are not yet organized explicitly as webpage analogs.
- A second-pass package still needs clearly labeled CFD-derived analogs for:
  - `Cp` versus `x/c`
  - `Cf` versus `x/c`
  - inflow `u` profile at `x/c = -2.14`
  - downstream `u` profiles at the listed stations
  - turbulent shear-stress profiles at the listed stations
  - velocity/streamline visualization analogous to the webpage overview image
- Each graph also needs a provenance statement showing that it comes directly from OpenFOAM outputs or direct post-processing, not from any traced reference curve.

## Mesh / Setup / BC / Model Weaknesses

- Flat upper slip boundary instead of a shaped upper boundary.
- Uniform inlet turbulence specification rather than a profile-based incoming turbulent boundary layer.
- Single-block topology with limited local control.
- Short iteration count.
- Only one turbulence-model baseline has been used so far.
- No clear before/after study exists yet to show which refinements actually reduce error.

## Documentation And Evaluation Gaps

- The first-pass report is useful, but it is not structured as a dedicated refinement report.
- The first-pass files do not yet separate:
  - original baseline assumptions
  - second-pass corrections
  - measurable accuracy changes
- The evaluation result exists, but it is not yet presented as the centerpiece of a pass-1 versus pass-2 comparison.

## Second-Pass Diagnosis Summary

The first pass succeeded as a clean, reproducible baseline reconstruction, but it is still too simplified to expect strong agreement on a difficult separated-flow benchmark. The most defensible second-pass opportunities are:

- improve inflow realism
- improve the upper-boundary treatment
- improve mesh targeting
- run to deeper convergence
- expand graph coverage and data provenance
- compare second-pass evaluation against the first-pass score instead of relying on qualitative appearance
