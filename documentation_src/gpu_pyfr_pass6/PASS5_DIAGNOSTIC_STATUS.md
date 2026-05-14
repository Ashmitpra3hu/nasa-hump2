# GPU PyFR PASS 6 PASS 5 Diagnostic Status

## Diagnostic Job
- Slurm job: `10706975`
- Queue/partition: `a100-40gb`
- Host: `gilbreth-n010.rcac.purdue.edu`
- State: `COMPLETED`
- Elapsed: `00:00:33`

## Files Produced
- `runs/gpu_pyfr_pass5/diagnostic/pass5_diagnostic_latest.vtu`
- `runs/gpu_pyfr_pass5/diagnostic/pseudo_stats.csv`
- `runs/gpu_pyfr_pass5/diagnostic/solutions/pass5_current.pyfrs`
- `runs/gpu_pyfr_pass5/diagnostic/slurm-10706975.out`
- `runs/gpu_pyfr_pass5/diagnostic/slurm-10706975.err`

## What PASS 6 Audited
PASS 6 audited the fetched VTU locally and on Gilbreth using the same
`inspect_pyfr_vtu_fields.py` script.

The diagnostic VTU contains these point-data arrays:
- `Density`
- `Velocity`
- `Pressure`

However, every one of those arrays is globally non-finite:

- `Density`: `0 / 316770` finite
- `Velocity_x`: `0 / 316770` finite
- `Velocity_y`: `0 / 316770` finite
- `Pressure`: `0 / 316770` finite

Near the lower wall:
- exact-wall pressure finite count: `0 / 1572`
- near-wall band finite count: `0 / 5759`

So PASS 5 still did **not** produce a finite field that can support `Cp`, `Cf`, or benchmark MAE.

## Pseudo-Stat Status
The conservative-variable pseudo-stat file confirms immediate instability:

```text
n,t,i,rho,rhou,rhov,E
1,0.0,1,-,-,-,-
2,0.0,2,-,-,-,-
3,0.0,3,-,-,-,-
4,0.0,4,nan,nan,nan,nan
...
```

The first non-finite row is:
- row index: `4`
- physical time: `0.0`
- pseudo iteration: `4`

This means the dimensional `navier-stokes` stabilization attempt in PASS 5 did not fix the underlying numerical breakdown.

## PASS 6 Consequence
PASS 6 must therefore:
1. treat PASS 5 as another non-finite-field failure,
2. run a small, focused stability sweep,
3. only attempt `Cp` extraction or benchmark MAE mapping from a hump VTU once the exported velocity field is finite.
