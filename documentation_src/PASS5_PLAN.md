# PASS 5 Plan

## Objective

Beat the pass-four best MAE of `0.1659136747` while keeping the no-cheat, no-interpolation workflow intact and improving agreement with the official NASA `Cp` and `Cf` experiment tables.

## What Pass 4 Already Established

- The best pass-four improvement came from deeper convergence of the existing SST baseline.
- The analytic turbulent-boundary-layer inlet did not beat the simpler deeper-converged SST continuation.
- The direct `Cp` and `Cf` comparison pipeline is now available and should remain central.

## Ranked Pass-5 Experiment Plan

1. Continue the exact pass-four SST winner from `650` to later checkpoints.
   - Purpose:
     test whether the promoted best case is still under-converged.
   - Checkpoints:
     `650`, `800`, `1000`, `1200`

2. Run one official-grid-inspired SST geometry experiment.
   - Purpose:
     make the upper-wall contour and streamwise block placement more faithful to the no-plenum structured-grid intent.
   - Strategy:
     keep the total grid scale close to the official `817 x 217` family, but redistribute cells into the front-half suction region, separation region, and recovery region.

3. Run one Spalart-Allmaras model screen on the improved geometry.
   - Purpose:
     test whether a different separated-shear-layer response improves the remaining pressure and wall-shear mismatch.
   - Limitation:
     SA-RC will be documented as unavailable if the local OpenFOAM installation does not provide it.

## Promotion Logic

1. Lowest benchmark MAE
2. Better official `Cp` and `Cf` agreement
3. Physically defensible explanation
4. Reproducibility and numerical stability
