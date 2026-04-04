# PASS 5 Experiment Notes

## Objective

Reduce the pass-four best MAE of `0.1659136747` while keeping the strict no-cheat workflow and improving agreement with the official NASA `Cp` and `Cf` tables.

## Audit Summary

- Geometry generation:
  `scripts/generate_nasa_hump_blockmesh.py`
- Numerics and convergence:
  `scripts/configure_nasa_hump_case.py`
- Inlet profiles:
  `scripts/write_nasa_hump_inlet_profile.py`
- Benchmark MAE:
  `scripts/evaluate_nasa_hump_case.py`
- Official `Cp`/`Cf` comparison:
  `scripts/evaluate_nasa_hump_wall_metrics.py` and `scripts/make_nasa_hump_pass4_figures.py`

## Main Remaining Approximations At Pass-Five Start

1. The hump and top-wall geometry still come from an analytic reconstruction rather than an imported official no-plenum mesh.
2. The pass-four winner improved mainly through deeper convergence, which suggests the baseline was still under-converged.
3. The current baseline still underpredicts the front-half suction peak and slightly under-recovers wall shear.
4. The pass-four wall-metric helper still needed to be tightened to a nearest-sample comparison rule for consistency with the stricter pass-four figure workflow.
5. SA-RC is not available in the local OpenFOAM installation, so the model screen is limited to `SpalartAllmaras` against `kOmegaSST`.

## Ranked Pass-Five Experiment Set

1. `pass5_continue_sst_1200`
   - Continue the promoted pass-four SST winner from `650` to `1200`.
   - Evaluate at `650`, `800`, `1000`, and `1200`.

2. `pass5_gridfit_sst_800`
   - Broaden the blockage contour and redistribute the streamwise blocks to better reflect the official no-plenum structured-grid emphasis while keeping the total grid scale near the official `817 x 217` family.

3. `pass5_gridfit_sa_800`
   - Use the same official-grid-inspired mesh and blockage contour as the SST geometry test, but switch to `SpalartAllmaras`.

## Continuation Study Results Recorded So Far

- `650`: benchmark MAE `0.1659136747`, `Cp` MAE `0.1711800326`, `Cf` MAE `0.0008476129`
- `800`: benchmark MAE `0.1547381028`, `Cp` MAE `0.1641787966`, `Cf` MAE `0.0007681825`
- `1000`: benchmark MAE `0.1433377644`, `Cp` MAE `0.1578824614`, `Cf` MAE `0.0006999053`
- `1200`: benchmark MAE `0.1358901676`, `Cp` MAE `0.1537547946`, `Cf` MAE `0.0006734136`

These continuation checkpoints already show that the pass-four winner was still materially under-converged at the start of pass five.

## Geometry-Fidelity And Model-Screen Outcomes

- `pass5_gridfit_sst_800`
  - benchmark MAE `0.1866349502`
  - `Cp` MAE `0.1730924866`
  - `Cf` MAE `0.0008231240`
  - interpretation:
    the broader top-wall contour and redistributed streamwise blocks slightly improved `Cf` relative to pass four, but did not improve the benchmark MAE enough to compete with the deeper-converged continuation.

- `pass5_gridfit_sa_800`
  - status:
    failed to produce a usable converged field
  - interpretation:
    the local OpenFOAM installation supports `SpalartAllmaras`, but this setup did not stabilize into a promotable run. `SA-RC` was not available locally, so it could not be screened honestly in this pass.

## Promotion Decision

The promoted pass-five winner is the continued SST baseline at `1200` iterations. It beat every other tested configuration on:

1. benchmark MAE
2. `Cp` agreement
3. `Cf` agreement
4. stability and reproducibility

The main pass-five lesson is that convergence fidelity still dominates the remaining error more strongly than the geometry and model changes tested here.
