#!/usr/bin/env python3
"""Build focused GPU PyFR PASS 6 stability-sweep configurations."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "configs"

RHO = 1.225
UINF = 34.6
PINF = 101325.0
MU = RHO * 1.553418803419e-05


def config_text(
    *,
    run_name: str,
    system: str,
    dt: float,
    tend: float,
    pseudo_dt: float,
    pseudo_min: int,
    pseudo_max: int,
    dt_out: float,
    inlet_type: str,
    outlet_type: str,
    use_pressure_at_inlet: bool,
) -> str:
    bc_inlet = [f"type = {inlet_type}", f"rho = {RHO:.6f}", f"u = {UINF:.6f}", "v = 0.0"]
    if use_pressure_at_inlet:
        bc_inlet.append(f"p = {PINF:.6f}")
    bc_outlet = [f"type = {outlet_type}"]
    if outlet_type in {"sub-out-fp", "char-riem-inv"}:
        bc_outlet.append(f"p = {PINF:.6f}")
    if outlet_type == "char-riem-inv":
        bc_outlet.insert(1, f"rho = {RHO:.6f}")
        bc_outlet.insert(3, f"u = {UINF:.6f}")
        bc_outlet.insert(4, "v = 0.0")

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
system = {system}
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
dt = {dt:.7f}
pseudo-dt = {pseudo_dt:.9f}
pseudo-niters-max = {pseudo_max:d}
pseudo-niters-min = {pseudo_min:d}
pseudo-resid-tol = 1.0e-6
pseudo-resid-norm = l2
atol = 1.0e-10
safety-fact = 0.5
min-fact = 0.80
max-fact = 1.01
pseudo-dt-max-mult = 1.2

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
{chr(10).join(bc_inlet)}

[soln-bcs-outlet]
{chr(10).join(bc_outlet)}

[soln-bcs-bottomwall]
type = no-slp-adia-wall

[soln-bcs-topwall]
type = slp-adia-wall

[soln-plugin-writer]
basedir = runs/gpu_pyfr_pass6/stability/{run_name}/solutions
basename = {run_name}
dt-out = {dt_out:.7f}

[soln-plugin-pseudostats]
file = runs/gpu_pyfr_pass6/stability/{run_name}/pseudo_stats
flushsteps = 10
"""


def main() -> None:
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    cases = [
        {
            "name": "pass6_smoke_ns_sub",
            "mesh": "smoke_rect.pyfrm",
            "variant": "smoke",
            "system": "navier-stokes",
            "dt": 2.0e-4,
            "tend": 1.0e-3,
            "pseudo_dt": 1.0e-7,
            "pseudo_min": 4,
            "pseudo_max": 20,
            "dt_out": 1.0e-3,
            "inlet_type": "sub-in-frv",
            "outlet_type": "sub-out-fp",
            "use_pressure_at_inlet": False,
            "notes": "Rectangular smoke test to check whether dimensional navier-stokes can stay finite away from the hump geometry.",
        },
        {
            "name": "pass6_hump_ns_sub_dt1e4",
            "mesh": "nasa_hump_medium.pyfrm",
            "variant": "medium",
            "system": "navier-stokes",
            "dt": 1.0e-4,
            "tend": 5.0e-4,
            "pseudo_dt": 1.0e-7,
            "pseudo_min": 4,
            "pseudo_max": 20,
            "dt_out": 5.0e-4,
            "inlet_type": "sub-in-frv",
            "outlet_type": "sub-out-fp",
            "use_pressure_at_inlet": False,
            "notes": "Same physics as PASS 5 but with a ten-times smaller physical and pseudo step.",
        },
        {
            "name": "pass6_hump_ns_sub_dt5e5",
            "mesh": "nasa_hump_medium.pyfrm",
            "variant": "medium",
            "system": "navier-stokes",
            "dt": 5.0e-5,
            "tend": 2.5e-4,
            "pseudo_dt": 5.0e-8,
            "pseudo_min": 4,
            "pseudo_max": 24,
            "dt_out": 2.5e-4,
            "inlet_type": "sub-in-frv",
            "outlet_type": "sub-out-fp",
            "use_pressure_at_inlet": False,
            "notes": "Even smaller step size to test whether the PASS 5 blow-up is purely time-integration driven.",
        },
        {
            "name": "pass6_hump_ns_char_dt1e4",
            "mesh": "nasa_hump_medium.pyfrm",
            "variant": "medium",
            "system": "navier-stokes",
            "dt": 1.0e-4,
            "tend": 5.0e-4,
            "pseudo_dt": 1.0e-7,
            "pseudo_min": 4,
            "pseudo_max": 20,
            "dt_out": 5.0e-4,
            "inlet_type": "char-riem-inv",
            "outlet_type": "char-riem-inv",
            "use_pressure_at_inlet": True,
            "notes": "Switches to characteristic inviscid boundaries to test whether the subsonic boundary treatment is the primary instability trigger.",
        },
        {
            "name": "pass6_hump_ns_char_dt5e5",
            "mesh": "nasa_hump_medium.pyfrm",
            "variant": "medium",
            "system": "navier-stokes",
            "dt": 5.0e-5,
            "tend": 2.5e-4,
            "pseudo_dt": 5.0e-8,
            "pseudo_min": 4,
            "pseudo_max": 24,
            "dt_out": 2.5e-4,
            "inlet_type": "char-riem-inv",
            "outlet_type": "char-riem-inv",
            "use_pressure_at_inlet": True,
            "notes": "Most conservative hump case in the sweep: tiny physical step plus characteristic boundaries.",
        },
    ]

    for case in cases:
        cfg_path = CFG_DIR / f"{case['name']}.ini"
        cfg_path.write_text(
            config_text(
                run_name=case["name"],
                system=case["system"],
                dt=case["dt"],
                tend=case["tend"],
                pseudo_dt=case["pseudo_dt"],
                pseudo_min=case["pseudo_min"],
                pseudo_max=case["pseudo_max"],
                dt_out=case["dt_out"],
                inlet_type=case["inlet_type"],
                outlet_type=case["outlet_type"],
                use_pressure_at_inlet=case["use_pressure_at_inlet"],
            )
        )
        manifest = dict(case)
        manifest_path = CFG_DIR / f"{case['name']}_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
