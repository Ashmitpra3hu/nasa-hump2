# GPU PyFR PASS 3 Audit

## What worked

PASS 3 established the first fully completed PyFR NASA hump run on Gilbreth GPU hardware. The stable path was:

- `scripts/submit_pyfr_pass3_minimal_gilbreth.sh`
- `scripts/pyfr/build_gpu_pyfr_pass3_case.py`
- `data/NASA_2DWMH_PyFR/configs/pass3_minimal.ini`
- one `A100-40gb`
- `ac-navier-stokes`
- order `1`
- medium piecewise-linear triangular hump mesh
- no sampler plugins

The successful job was Slurm job `10702409`, and it produced:

- `runs/gpu_pyfr_pass3/minimal/solutions/pass3_minimal.pyfrs`
- `runs/gpu_pyfr_pass3/minimal/pass3_minimal_latest.vtu`
- `runs/gpu_pyfr_pass3/minimal/pseudo_stats.csv`
- `runs/gpu_pyfr_pass3/minimal/slurm-10702409.out`
- `runs/gpu_pyfr_pass3/minimal/slurm-10702409.err`

PASS 3 also proved the local postprocessing/report path worked:

- `scripts/fetch_gpu_pyfr_pass3_results.sh`
- `scripts/postprocess_gpu_pyfr_pass3.py`
- `scripts/render_gpu_pyfr_pass3_paraview.py`
- `documentation/gpu_pyfr_pass3.pdf`

## What remained missing

PASS 3 did not yet provide a defensible validation package against the NASA wall data. Specifically:

- no external wall-pressure extraction was implemented
- no `Cp` comparison against the official NASA experimental data was produced
- no `Cf` comparison was attempted
- no benchmark `MAE` was computed
- no sparse or wall probe recovery path was demonstrated

## Why no valid Cp/Cf/MAE existed yet

The PASS 3 run was intentionally the shortest stable no-sampler execution. That was the correct milestone for robustness, but it meant:

1. the run was too short to treat as a validation-quality field,
2. the VTU export was used only for visualization, not for wall-data extraction,
3. no external wall reconstruction method had been written yet,
4. PyFR in this workflow is still `ac-navier-stokes`, not OpenFOAM SST, so any future comparison must stay explicitly cross-method and not pretend to be turbulence-model equivalent.

`Cf` was especially unavailable because PASS 3 had no defensible wall-shear extraction path from the exported fields.

## Files to reuse in PASS 4

PASS 4 should directly reuse:

- `scripts/submit_pyfr_pass3_minimal_gilbreth.sh`
- `scripts/fetch_gpu_pyfr_pass3_results.sh`
- `scripts/postprocess_gpu_pyfr_pass3.py`
- `scripts/render_gpu_pyfr_pass3_paraview.py`
- `scripts/pyfr/build_gpu_pyfr_pass3_case.py`
- `data/NASA_2DWMH_PyFR/configs/pass3_minimal.ini`
- `runs/gpu_pyfr_pass3/minimal/pass3_minimal_latest.vtu`
- `runs/gpu_pyfr_pass3/minimal/pseudo_stats.csv`
- `documentation_src/gpu_pyfr_pass3/REPRODUCIBILITY.md`

## PASS 4 implication

The right next move is not a new mesh family or a new solver model. PASS 4 should keep the exact PASS 3 execution path and extend it in this order:

1. longer stable no-sampler run,
2. external VTU-based wall-pressure extraction,
3. first honest `Cp` comparison against the official NASA data,
4. `Cf` only if the extracted information is physically and numerically defensible.
