# GPU PyFR PASS 5 Cf Feasibility

PASS 5 does not invent `Cf`.

At the current stage, `Cf` is only defensible if the PyFR workflow can provide one of the following with finite values:

- wall shear stress directly,
- viscous fluxes on the wall,
- velocity gradients close enough to the wall to support a conservative near-wall derivative estimate.

The current PASS 4 outputs do not provide that:

- the exported PASS 4 `Velocity` field is globally non-finite,
- no wall-gradient fields are exported,
- the PASS 3 and PASS 4 runs both show `nan` pseudo statistics very early,
- the order-1 triangular mesh is not a strong basis for wall-shear estimation even if the field were finite.

Therefore PASS 5 treats `Cf` as unavailable unless a stabilized rerun produces finite velocity data and the resulting wall-gradient estimate is still physically defensible.

If PASS 5 diagnostic or promoted runs remain too coarse or too non-finite for near-wall gradients, the report will continue to state `Cf unavailable` rather than fabricate a comparison.
