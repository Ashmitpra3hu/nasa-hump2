# ML PASS 2 Notes

## Scope

ML PASS 2 was built directly on top of the PASS 4 / ML PASS 1 workflow. It
kept the same Dockerized OpenFOAM execution pattern, the same benchmark MAE
evaluation, and the same official NASA Cp/Cf comparison pipeline.

## What ML PASS 1 Used

ML PASS 1 used `kOmegaSSTML`, a bounded multiplicative correction to `nut`
based on:

- eddy-viscosity ratio `nut/nu`
- wall distance banding

That correction acted after the base SST closure had already formed its
production / destruction balance, so it was too weakly coupled to the hump
separation and recovery physics.

## ML PASS 2 Correction

ML PASS 2 introduced `kOmegaSSTML2`, which is a new correction family. It does
not multiply `nut` directly. Instead, it scales the SST production pathway by
modifying both:

- `Pk(G)` in the `k` equation
- `GbyNu(...)` in the `omega` production term

The correction is activated by a bounded sensor combining:

- an adverse-pressure-gradient proxy from streamline deceleration
- a strain / vorticity ratio as a shear-layer indicator
- a wall-distance localization band

## Audit of Control Files

- Custom turbulence model:
  `ml_models/kOmegaSSTML/kOmegaSSTML2.H`,
  `ml_models/kOmegaSSTML/kOmegaSSTML2.C`,
  `ml_models/kOmegaSSTML/mlHumpTurbulenceModels.C`
- Build workflow:
  `scripts/build_ml_hump_model.sh`
- Case configuration:
  `scripts/configure_nasa_hump_case.py`
- ML PASS 2 driver:
  `scripts/run_nasa_hump_mlpass2.py`,
  `scripts/run_nasa_hump_mlpass2.sh`
- Wall Cp/Cf evaluation:
  `scripts/evaluate_nasa_hump_wall_metrics.py`
- Benchmark MAE evaluation:
  `scripts/evaluate_nasa_hump_case.py`
- Figure generation:
  `scripts/make_nasa_hump_mlpass2_figures.py`

## Result

The primary ML PASS 2 batch was numerically stable, but every completed cheap
and full evaluation produced the same CFD metrics as the plain SST continuation
to the printed precision. The correction was therefore scientifically cleaner
than ML PASS 1, but still too insensitive to justify promotion.

## Backup Attempt

A broader-activation backup case was launched after the primary batch to check
whether the first sensor was simply too selective. That backup was not retained
in the final conclusions because the Docker run stalled before producing a
usable solver log or evaluation record.
