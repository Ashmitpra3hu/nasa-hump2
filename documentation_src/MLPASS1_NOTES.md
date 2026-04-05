# ML PASS 1 Notes

## Objective

Test a bounded, low-dimensional data-driven correction inside the SST turbulence model using only the approved NASA hump resources and the local repository workflow.

## Correction Form

- model name:
  `kOmegaSSTML`
- correction target:
  turbulent viscosity `nut`
- activation logic:
  wall-distance Gaussian band multiplied by an eddy-viscosity-ratio activation
- optimized parameters:
  - `amplitude`
  - `chi0`
  - `yPeak`
- fixed bounds:
  - `factorMin = 0.85`
  - `factorMax = 1.60`
  - `chiWidth = 1.0`
  - `yWidth = 0.010`

## Optimizer

- method:
  `Nelder-Mead`
- cheap stage:
  continuation from the pass-four `650` field to `720`
- full stage:
  continuation from the pass-four `650` field to `800`
- objective:
  `J = 0.55*benchmark_MAE + 0.30*Cp_MAE + 0.15*(Cf_MAE/1e-3) + penalty`
- penalty:
  `0.02*(amplitude/0.6)^2`

## Result

The best nonzero corrected candidate stayed numerically stable but did not improve the flow metrics relative to the plain SST baseline at the same continuation depth. The optimizer therefore collapsed toward the zero-amplitude limit, which is the correct conservative behavior for this experiment.

## Decision

Reject the correction for promotion in ML PASS 1.
