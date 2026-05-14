#!/usr/bin/env python3
"""Build stabilized PASS 5 PyFR configurations for Gilbreth."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "configs"

RHO = 1.225
UINF = 34.6
PINF = 101325.0
MU = RHO * 1.553418803419e-05


def render_config(*, tend: float, dt: float, pseudo_dt: float, pseudo_min: int, pseudo_max: int, dt_out: float) -> str:
    return f"""[backend]
precision = double
rank-allocator = linear

[backend-cuda]
device-id = local-rank
mpi-type = standard

[constants]
gamma = 1.4
mu = {MU:.15e}
Pr = 0.72

[solver]
system = navier-stokes
order = 1
anti-alias = flux
viscosity-correction = none
shock-capturing = none

[solver-time-integrator]
formulation = dual
scheme = backward-euler
pseudo-scheme = rk45
controller = none
pseudo-controller = local-pi
tstart = 0.0
tend = {tend:.6f}
dt = {dt:.6f}
pseudo-dt = {pseudo_dt:.7f}
pseudo-niters-max = {pseudo_max:d}
pseudo-niters-min = {pseudo_min:d}
pseudo-resid-tol = 1.0e-5
pseudo-resid-norm = l2
atol = 1.0e-8
safety-fact = 0.7
min-fact = 0.90
max-fact = 1.02
pseudo-dt-max-mult = 1.5

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
rho = {RHO:.6f}
u = {UINF:.6f}
v = 0.0
p = {PINF:.6f}

[soln-bcs-inlet]
type = sub-in-frv
rho = {RHO:.6f}
u = {UINF:.6f}
v = 0.0

[soln-bcs-outlet]
type = sub-out-fp
p = {PINF:.6f}

[soln-bcs-bottomwall]
type = no-slp-adia-wall

[soln-bcs-topwall]
type = slp-adia-wall

[soln-plugin-writer]
basedir = runs/gpu_pyfr_pass5/current/solutions
basename = pass5_current
dt-out = {dt_out:.6f}

[soln-plugin-pseudostats]
file = runs/gpu_pyfr_pass5/current/pseudo_stats
flushsteps = 10
"""


def main() -> None:
    CFG_DIR.mkdir(parents=True, exist_ok=True)

    configs = {
        "pass5_diagnostic.ini": {
            "text": render_config(tend=0.005, dt=0.001, pseudo_dt=1.0e-5, pseudo_min=4, pseudo_max=14, dt_out=0.0020),
            "manifest": {
                "run_name": "pass5_diagnostic",
                "mesh": "nasa_hump_medium.pyfrm",
                "system": "navier-stokes",
                "order": 1,
                "goal": "Establish the first finite-field PyFR hump solution with pressure suitable for external Cp extraction.",
                "notes": "Switches from ac-navier-stokes to dimensional navier-stokes, keeps the stable no-sampler path, and lowers the physical and pseudo time step aggressively.",
            },
        },
        "pass5_promoted.ini": {
            "text": render_config(tend=0.020, dt=0.001, pseudo_dt=1.0e-5, pseudo_min=4, pseudo_max=16, dt_out=0.005),
            "manifest": {
                "run_name": "pass5_promoted",
                "mesh": "nasa_hump_medium.pyfrm",
                "system": "navier-stokes",
                "order": 1,
                "goal": "Promoted longer PASS 5 PyFR run using the same stabilized settings after the diagnostic case is finite.",
                "notes": "Retains the PASS 5 diagnostic numerical settings but extends physical time to support wall-pressure extraction and visualization.",
            },
        },
    }

    for name, payload in configs.items():
        cfg_path = CFG_DIR / name
        cfg_path.write_text(payload["text"])
        manifest_path = CFG_DIR / f"{cfg_path.stem}_manifest.json"
        manifest_path.write_text(json.dumps(payload["manifest"], indent=2))


if __name__ == "__main__":
    main()
