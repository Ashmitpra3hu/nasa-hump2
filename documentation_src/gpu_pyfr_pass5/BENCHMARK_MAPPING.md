# GPU PyFR PASS 5 Benchmark Mapping Feasibility

The existing benchmark MAE workflow in this repository was built around OpenFOAM-derived fields and evaluation-point extraction already matched to that pipeline.

For PyFR, an honest benchmark MAE requires:

1. a finite exported field,
2. variables that correspond to the expected evaluation quantities,
3. a reproducible point-sampling method in the same physical coordinates,
4. no post-hoc fitting or target interpolation.

PASS 4 cannot satisfy those conditions because its exported field is globally non-finite.

PASS 5 therefore treats benchmark MAE in two stages:

- Stage 1: determine whether the stabilized PyFR run yields finite exported state variables;
- Stage 2: if it does, evaluate whether those variables can be sampled onto the existing benchmark coordinates without inventing missing quantities.

Until Stage 1 succeeds, benchmark MAE remains unavailable. This is a workflow limitation, not a metric that should be guessed or back-filled.
