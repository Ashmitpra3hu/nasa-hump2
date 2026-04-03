# PASS 4 Experiment Notes

This file records the focused pass-four refinement work built on the existing third-pass winner.

## Objective

1. Import the official no-flow-control experimental `Cp` and `Cf` tables from the approved NASA hump resources.
2. Compare the current OpenFOAM wall coefficients against those tables directly.
3. Use those comparisons to guide one more physically justified improvement round.

## Baseline At Start Of Pass 4

- Case: `data/NASA_2DWMH`
- Best available MAE: `0.1801372055`
- Best field time: `500`
- Turbulence model: `kOmegaSST`
- Inlet mode: uniform
- Key inherited improvements:
  - longer upstream run-up
  - shaped upper slip wall for blockage
  - three-block streamwise mesh
  - deeper convergence than pass two

## New Experimental Data Added

- `data/experimental/NASA_hump/noflow_cp.dat`
- `data/experimental/NASA_hump/noflow_cf.dat`
- normalized CSV copies under the same directory

These files were fetched from the approved machine-readable NASA hump data location only. No plot tracing, digitization, or hidden-data recovery was used.

## First Cp/Cf Diagnosis

The first direct comparison against the pass-three baseline showed:

- `Cp` mismatch remained larger than `Cf` mismatch.
- The CFD wall-pressure trough over the front half of the hump was too weak in several regions.
- The CFD wall-shear magnitude on the front part of the hump was still low relative to the published trend.
- The pass-three field still responded favorably to longer convergence, so under-convergence remained a credible error source.

## Pass-Four Experiment Set

### 1. `pass4_uniform_sst_650`

- Change:
  continue the current best SST baseline from `500` to `650` iterations
- Purpose:
  test whether the remaining MAE and wall-coefficient error still respond to deeper convergence
- Outcome:
  winner

### 2. `pass4_tbl35_sst_500`

- Change:
  replace the uniform inlet with an analytic turbulent-boundary-layer profile of `delta = 35 mm`
- Purpose:
  test whether a more realistic inflow profile improves the upstream station and downstream wall behavior
- Outcome:
  finished and improved over pass three, but still lost to the deeper-converged uniform-inlet continuation

## Winning Result

- Best pass-four MAE: `0.1659136747`
- Improvement vs pass three: `0.0142235308`
- Wall comparison at the winning state:
  - `Cp` MAE: `0.1712464312`
  - `Cf` MAE: `0.0008483389`

## Main Takeaway

The pass-four winner was not a more elaborate inlet model. The strongest honest improvement came from extending the already-best SST baseline to a more converged state, and that helped both the local benchmark MAE and the direct `Cp`/`Cf` agreement against the official experimental tables.

## Ranked Pass-Four Results

1. `pass4_uniform_sst_650`
   - MAE: `0.1659136747`
   - `Cp` MAE: `0.1712464312`
   - `Cf` MAE: `0.0008483389`
2. `pass4_tbl35_sst_500`
   - MAE: `0.1674487658`
   - `Cp` MAE: `0.1812127339`
   - `Cf` MAE: `0.0009521055`
3. pass-three baseline
   - MAE: `0.1801372055`
   - `Cp` MAE: `0.1806030896`
   - `Cf` MAE: `0.0009550565`
