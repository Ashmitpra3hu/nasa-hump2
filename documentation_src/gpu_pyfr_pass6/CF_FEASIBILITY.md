# GPU PyFR PASS 6 Cf Feasibility

PASS 6 continues the strict rule from PASS 5: `Cf` is only reportable if wall shear can be extracted physically and defensibly.

PASS 6 has removed the old field-validity blocker:
- the promoted hump VTU now has globally finite density, velocity, and pressure,
- wall pressure can therefore be extracted and converted into `Cp`.

`Cf` remains unavailable for a different reason:
- the exported PyFR VTU used in PASS 6 does not contain wall gradients,
  viscous fluxes, or direct wall shear outputs,
- the run is first-order on a piecewise-linear triangular mesh, so a
  near-wall finite-difference estimate would be too fragile to present as an
  honest validation metric,
- no sampler plugin or higher-order wall-recovery path was validated in this
  pass.

Therefore PASS 6 still does **not** report `Cf`.
