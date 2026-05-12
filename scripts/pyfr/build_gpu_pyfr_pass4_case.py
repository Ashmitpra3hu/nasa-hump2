#!/usr/bin/env python3
"""Generate the longer PASS 4 PyFR hump config."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "configs"


CONFIG_TEXT = """[backend]
precision = double
rank-allocator = linear

[backend-cuda]
device-id = local-rank
mpi-type = standard

[constants]
nu = 1.553418803419e-05
ac-zeta = 1600.000000

[solver]
system = ac-navier-stokes
order = 1
anti-alias = flux

[solver-time-integrator]
formulation = dual
scheme = backward-euler
pseudo-scheme = rk45
controller = none
pseudo-controller = local-pi
tstart = 0.0
tend = 0.100000
dt = 0.010000
pseudo-dt = 0.000500
pseudo-niters-max = 8
pseudo-niters-min = 3
pseudo-resid-tol = 1.0e-5
pseudo-resid-norm = l2
atol = 1.0e-6
safety-fact = 0.9
min-fact = 0.98
max-fact = 1.01
pseudo-dt-max-mult = 3.0

[solver-interfaces]
riemann-solver = rusanov
ldg-beta = 0.5
ldg-tau = 0.1

[solver-interfaces-line]
flux-pts = gauss-legendre
quad-deg = 6
quad-pts = gauss-legendre

[solver-elements-tri]
soln-pts = williams-shunn
quad-deg = 6
quad-pts = williams-shunn

[soln-ics]
p = 0.0
u = 34.600000
v = 0.0

[soln-bcs-inlet]
type = ac-in-fv
u = 34.600000
v = 0.0

[soln-bcs-outlet]
type = ac-out-fp
p = 0.0

[soln-bcs-bottomwall]
type = no-slp-wall
u = 0.0
v = 0.0

[soln-bcs-topwall]
type = slp-wall

[soln-plugin-writer]
basedir = runs/gpu_pyfr_pass4/long/solutions
basename = pass4_long
dt-out = 0.020000

[soln-plugin-pseudostats]
file = runs/gpu_pyfr_pass4/long/pseudo_stats
flushsteps = 10
"""


def main() -> None:
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CFG_DIR / "pass4_long.ini"
    manifest_path = CFG_DIR / "pass4_long_manifest.json"
    config_path.write_text(CONFIG_TEXT)
    manifest = {
        "mesh": "nasa_hump_medium.pyfrm",
        "run_name": "pass4_long",
        "variant": "long",
        "order": 1,
        "tend": 0.10,
        "dt": 0.01,
        "pseudo_dt": 0.0005,
        "pseudo_niters_max": 8,
        "plugins": ["writer", "pseudostats"],
        "notes": "Longer PASS 4 no-sampler GPU hump configuration intended for external wall-pressure extraction.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
