# Second-Pass Plan

## Purpose

This second pass refines the existing first-pass NASA hump reconstruction already present in the repository. The goal is to reduce error honestly, improve physical fidelity where the allowed information supports it, recreate the visible graph categories using CFD-derived data only, and produce a clearer documentation package.

## Targeted Refinement Strategy

## 1. Preserve The First-Pass Baseline

- Keep the first-pass case as the starting point rather than deleting it.
- Treat the current score `0.2338504550` as the baseline to beat.
- Record any new variant clearly so before/after comparison is possible.

## 2. Revisit The Setup Elements Most Likely To Affect Separation

- Re-check the hump geometry generator and domain extents.
- Revisit the upper slip boundary using the allowed page’s blockage-contour guidance.
- Revisit the inflow treatment so the upstream station better reflects a developed turbulent boundary layer rather than a uniform field.
- Revisit mesh distribution to strengthen resolution near the hump, in the shear layer, and in the recovery region.
- Revisit solver controls and iteration count so the case is judged from a more converged field.

## 3. Revisit Post-Processing Coverage

- Expand the figure-generation workflow so every graph family visible on the allowed page has a CFD-derived analog where feasible.
- Add a more explicit provenance trail for each graph.
- Refresh ParaView outputs and `.foam` artifacts after the refined run.

## Files And Settings To Revisit

- `scripts/generate_nasa_hump_blockmesh.py`
- `data/NASA_2DWMH/system/blockMeshDict`
- `data/NASA_2DWMH/caseDef`
- `data/NASA_2DWMH/0/U`
- `data/NASA_2DWMH/0/k`
- `data/NASA_2DWMH/0/omega`
- `data/NASA_2DWMH/0/nut`
- `data/NASA_2DWMH/system/controlDict`
- `data/NASA_2DWMH/system/fvSchemes`
- `data/NASA_2DWMH/system/fvSolution`
- `data/NASA_2DWMH/system/` sampling dictionaries
- `scripts/postprocess_nasa_hump_case.sh`
- `scripts/make_nasa_hump_figures.py`
- `scripts/evaluate_reconstructed_nasa_case.py`
- second-pass report and supporting documentation under `documentation/`

## Expected Effect Of Each Planned Change

- Better inflow treatment should improve the upstream boundary-layer state and therefore the downstream separation behavior.
- Better upper-boundary treatment should improve the pressure field and blockage representation.
- Better mesh targeting should improve wall quantities, separation behavior, and sampled profile quality.
- Longer and better-documented convergence should reduce noise and prevent judging the case too early.
- Expanded post-processing should make it easier to compare quantities honestly and identify which parts improved.

## How Improvement Will Be Measured

- Re-run the local evaluation workflow and compare the second-pass score against the first-pass score `0.2338504550`.
- Compare convergence history and final residual levels.
- Compare extracted wall-quantity trends and sampled profile behavior between pass 1 and pass 2.
- Record whether separation and reattachment indicators become more physically coherent.

## No-Cheat Preservation Plan

- Use only the allowed NASA hump validation webpage for external reference.
- Use only currently present local repo materials and first-pass outputs.
- Do not inspect git history or deleted files.
- Do not digitize webpage plots or create synthetic target curves.
- Keep all second-pass figures sourced from CFD output and direct post-processing only.
