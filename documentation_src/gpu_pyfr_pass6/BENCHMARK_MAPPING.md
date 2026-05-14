# GPU PyFR PASS 6 Benchmark Mapping

PASS 6 keeps the benchmark-MAE rule strict:

- benchmark MAE is only reported if a hump VTU contains finite velocity data,
- the mapping uses the existing local evaluation points,
- the field-to-point sampling is treated as normal CFD field sampling, not target interpolation,
- no coordinate warping or post-hoc fitting is allowed.

PASS 6 now has finite hump VTUs from the stabilized dimensional `navier-stokes`
cases, so benchmark mapping is available.

Current mapping method:
- read the promoted PyFR VTU point coordinates and pointwise `Velocity`,
- discard any non-finite points before interpolation,
- sample onto the existing local NASA hump benchmark query points using
  `LinearNDInterpolator`,
- use nearest-neighbour fallback only for query points that fall outside the
  linear interpolation hull,
- evaluate the resulting `(u, 0, v)` predictions with the same
  `closure_challenge.eval.evaluate_individual_case("NASA_2DWMH", ...)`
  routine already used for the OpenFOAM cases.

Promoted PASS 6 benchmark result:
- case: `pass6_hump_ns_char_dt5e5`
- benchmark MAE: `0.29371445045471833`
- query points: `1000`
- finite PyFR velocity points used: `316770`
- nearest-fallback count: `8`
- max nearest distance: `0.01786729544123034 m`
- mean nearest distance: `0.0008698643200912001 m`

This is an honest cross-method PyFR benchmark score. It is much worse than the
OpenFOAM SST baselines, but it is now real, finite, and reproducible.
