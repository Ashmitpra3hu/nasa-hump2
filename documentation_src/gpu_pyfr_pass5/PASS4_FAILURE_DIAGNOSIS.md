# GPU PyFR PASS 4 Failure Diagnosis

## Summary
GPU PyFR PASS 4 advanced the PyFR hump workflow beyond the original sampler failures by:

- reusing the stable no-sampler execution path from PASS 3,
- running a longer case on Gilbreth job `10702493`,
- exporting a VTU field,
- attempting external wall-pressure extraction.

However, PASS 4 still did not produce valid validation metrics. PASS 5 begins by treating that as a field-validity problem rather than a plotting problem.

## What PASS 4 Did Successfully
- Slurm job `10702493` completed on `a100-40gb`.
- The run wrote:
  - `runs/gpu_pyfr_pass4/long/solutions/pass4_long.pyfrs`
  - `runs/gpu_pyfr_pass4/long/pass4_long_latest.vtu`
  - `runs/gpu_pyfr_pass4/long/pseudo_stats.csv`
- External postprocessing, ParaView rendering, and wall-extraction scripts all executed to completion.

## What PASS 4 Still Lacked
- No finite wall-pressure values were available for a usable `Cp` curve.
- No defensible `Cf` extraction path was available.
- No honest mapping into the existing OpenFOAM benchmark MAE pipeline was available.

## Exact Failure Mode
PASS 5 audited `runs/gpu_pyfr_pass4/long/pass4_long_latest.vtu` directly with VTK through `pvpython`.

The field audit found:

- point-data arrays: `Velocity`, `Pressure`
- cell-data arrays: `Partition`
- points: `316770`
- cells: `285093`

The crucial result is that the exported solution arrays are globally non-finite:

- `Velocity` component 0 finite count: `0 / 316770`
- `Velocity` component 1 finite count: `0 / 316770`
- `Pressure` finite count: `0 / 316770`

Near the lower wall, the outcome is the same:

- exact-wall pressure finite count: `0 / 1572`
- near-wall band pressure finite count: `0 / 5759`

This means PASS 4 did not fail because the wall extractor picked the wrong points. The underlying VTU solution field itself contains only `NaN` values for the exported fluid variables.

## Pseudo-Stat Diagnosis
The pseudo-stat file confirms that the issue begins during the solve, not only during export.

Representative rows from `runs/gpu_pyfr_pass4/long/pseudo_stats.csv`:

```text
n,t,i,p,u,v
1,0.0,1,-,-,-
2,0.0,2,-,-,-
3,0.0,3,nan,nan,nan
4,0.0,4,nan,nan,nan
...
```

So the run writes scheduler-complete outputs, but the pseudo residuals become `nan` almost immediately.

PASS 3 shows the same pattern in its own `pseudo_stats.csv`, which means PASS 3 and PASS 4 were runtime/export milestones, not finite-field validation runs.

## Root Cause Classification
PASS 5 classifies the PASS 4 failure as:

- not primarily a plotting failure,
- not primarily a lower-wall point-selection failure,
- not primarily a wrong VTU array-name failure,
- primarily a **solver-state invalidity / non-finite exported field** problem.

## Reusable Files From PASS 4
These PASS 4 pieces remain useful and are reused in PASS 5:

- `scripts/pyfr/build_gpu_pyfr_pass4_case.py`
- `scripts/submit_pyfr_pass4_long_gilbreth.sh`
- `scripts/fetch_gpu_pyfr_pass4_results.sh`
- `scripts/postprocess_gpu_pyfr_pass4.py`
- `scripts/render_gpu_pyfr_pass4_paraview.py`
- `runs/gpu_pyfr_pass4/long/slurm-10702493.out`
- `runs/gpu_pyfr_pass4/long/slurm-10702493.err`

## PASS 5 Consequence
Because the PASS 4 field is globally non-finite, PASS 5 must do two things:

1. preserve the honest diagnosis and field audit;
2. run a more conservative stabilized PyFR case before claiming any `Cp`, `Cf`, or benchmark mapping results.

That is why PASS 5 introduces:

- a VTU field-audit script,
- a repaired pseudo-stat summary,
- a more geometry-aware wall extractor,
- stabilized diagnostic and promoted PyFR run scripts for Gilbreth.
