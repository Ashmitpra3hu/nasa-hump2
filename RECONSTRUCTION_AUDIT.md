# Reconstruction Audit

## Scope

This audit covers the original reconstruction of a new `data/NASA_2DWMH` case created after the old NASA hump case had been deleted from the local repository.

## Compliance Proof

- I used only the single allowed NASA page: `https://tmbwg.github.io/turbmodels/nasahump_val.html`.
- I used only files present in the current working tree for repository pattern reference.
- I did not run git-history recovery commands such as `git log`, `git show`, `git reflog`, `git checkout`, or `git restore`.
- I did not browse any other website, repo, paper, PDF, issue, or forum.
- I did not recover, copy, or restore the deleted NASA hump case from any hidden source.

## Newly Created or Modified Files

### Root-level planning and audit

- `NO_CHEAT_PLAN.md`
- `CASE_PATTERN_SUMMARY.md`
- `RECONSTRUCTION_AUDIT.md`

### New case

- `data/NASA_2DWMH/caseDef`
- `data/NASA_2DWMH/fieldDef`
- `data/NASA_2DWMH/0/U`
- `data/NASA_2DWMH/0/p`
- `data/NASA_2DWMH/0/k`
- `data/NASA_2DWMH/0/omega`
- `data/NASA_2DWMH/0/nut`
- `data/NASA_2DWMH/constant/transportProperties`
- `data/NASA_2DWMH/constant/turbulenceProperties`
- `data/NASA_2DWMH/system/blockMeshDict`
- `data/NASA_2DWMH/system/controlDict`
- `data/NASA_2DWMH/system/fvSchemes`
- `data/NASA_2DWMH/system/fvSolution`
- `data/NASA_2DWMH/system/residuals`
- `data/NASA_2DWMH/system/bottomValues`
- `data/NASA_2DWMH/system/singleGraph_xm214`
- `data/NASA_2DWMH/system/singleGraph_x065`
- `data/NASA_2DWMH/system/singleGraph_x080`
- `data/NASA_2DWMH/system/singleGraph_x090`
- `data/NASA_2DWMH/system/singleGraph_x100`
- `data/NASA_2DWMH/system/singleGraph_x110`
- `data/NASA_2DWMH/system/singleGraph_x120`
- `data/NASA_2DWMH/system/singleGraph_x130`
- `data/NASA_2DWMH/system/decomposeParDict`
- `data/NASA_2DWMH/run.sh`
- `data/NASA_2DWMH/postProcess.sh`
- `data/NASA_2DWMH/clean.sh`

### New repository-level scripts

- `scripts/generate_nasa_hump_blockmesh.py`
- `scripts/build_nasa_hump_case.sh`
- `scripts/run_nasa_hump_case.sh`
- `scripts/postprocess_nasa_hump_case.sh`
- `scripts/make_nasa_hump_figures.py`
- `scripts/make_figures.sh`
- `scripts/build_report.sh`

### Generated outputs

- `data/NASA_2DWMH/foam.foam`
- `data/NASA_2DWMH/log.blockMesh`
- `data/NASA_2DWMH/log.checkMesh`
- `data/NASA_2DWMH/log.writeCellCentres`
- `data/NASA_2DWMH/log.run`
- `data/NASA_2DWMH/log.wallShearStress`
- `data/NASA_2DWMH/log.bottomValues`
- `data/NASA_2DWMH/log.foamToVTK`
- `data/NASA_2DWMH/0/C`
- `data/NASA_2DWMH/0/Cx`
- `data/NASA_2DWMH/0/Cy`
- `data/NASA_2DWMH/0/Cz`
- `data/NASA_2DWMH/20/*`
- `data/NASA_2DWMH/40/*`
- `data/NASA_2DWMH/60/*`
- `data/NASA_2DWMH/80/*`
- `data/NASA_2DWMH/postProcessing/wallShearStress/0/*`
- `data/NASA_2DWMH/VTK/*`
- `docs/data/residual_history.csv`
- `docs/data/profile_manifest.json`
- `docs/data/profile_xm214.csv`
- `docs/data/profile_x065.csv`
- `docs/data/profile_x080.csv`
- `docs/data/profile_x090.csv`
- `docs/data/profile_x100.csv`
- `docs/data/profile_x110.csv`
- `docs/data/profile_x120.csv`
- `docs/data/profile_x130.csv`
- `docs/data/wall_coefficients.csv`
- `docs/data/summary.json`
- `docs/figures/mesh_overview.png`
- `docs/figures/velocity_contour.png`
- `docs/figures/pressure_contour.png`
- `docs/figures/hump_closeup_velocity.png`
- `docs/figures/velocity_profiles.png`
- `docs/figures/residual_history.png`
- `docs/figures/wall_coefficients.png`
- `docs/report/main.tex`
- `docs/report/references.bib`

## Assumptions

- The hump geometry is an authored smooth cosine-squared profile over a `0.42 m` chord with `0.053 m` peak height.
- The top boundary is a flat slip wall at `0.35 m`.
- The case uses a no-flow-control baseline with no plenum.
- The inflow uses uniform freestream velocity `34.6 m/s` and uniform turbulence quantities.
- The baseline is an `80`-iteration SST `simpleFoam` run intended as a reproducible first RANS case rather than a final converged validation reference.
- Profile CSV files are extracted from solved cell-center fields at target streamwise stations rather than from the original deleted sampling pipeline.

## Commands Executed

### Primary workflow commands

- `bash scripts/build_nasa_hump_case.sh`
- `bash scripts/run_nasa_hump_case.sh`
- `bash scripts/postprocess_nasa_hump_case.sh`
- `python3 scripts/make_nasa_hump_figures.py`

### Key supporting inspection/debug commands

- `rg --files`
- `find . -maxdepth 2 -type d | sort`
- `sed -n ...` on representative surviving case files
- `rg -n "NASA_2DWMH|2DWMH|hump" .`
- `docker --version`
- `docker ps --format ...`
- `docker rm -f <container-id>` when stopping overly long intermediate runs
- `tail -n ... data/NASA_2DWMH/log.run`
- `find data/NASA_2DWMH/postProcessing ...`

## What Ran Successfully

- `blockMesh` completed successfully.
- `checkMesh` completed successfully and reported `Mesh OK`.
- `writeCellCentres` completed successfully.
- `simpleFoam` completed through iteration directory `80`.
- `simpleFoam -postProcess -func wallShearStress` completed successfully.
- `foamToVTK` completed successfully.
- The Python post-processing script generated CSV and PNG outputs successfully.

## Output Summary

- ParaView-friendly case marker: `data/NASA_2DWMH/foam.foam`
- VTK export tree: `data/NASA_2DWMH/VTK/`
- Solved field snapshots: `20`, `40`, `60`, `80`
- Machine-readable profile data: `docs/data/profile_*.csv`
- Residual history: `docs/data/residual_history.csv`
- Wall-derived coefficients: `docs/data/wall_coefficients.csv`
- Summary metrics: `docs/data/summary.json`
- Figure set: `docs/figures/*.png`
- Report source: `docs/report/main.tex`

## Approximations, Mismatches, and Uncertainties

- The geometry is a new original reconstruction rather than the original NASA benchmark coordinate definition.
- The top-wall contour is simplified.
- The wall-pressure plot is derived from near-wall solved cells, not a recovered original wall-pressure extraction file.
- The profile extraction script works directly from cell centers because the OpenFOAM container version differed from some legacy helper-dictionary behavior in the surviving cases.
- The local machine does not currently have `latexmk` or `pdflatex`, so the LaTeX report source exists but was not compiled into PDF here.

## Final Compliance Statement

No forbidden source was used. No deleted NASA hump case content was recovered. The new case was originally rebuilt from the single allowed NASA page, the surviving repository structure, Dockerized OpenFOAM, and files authored during this task.
