#!/usr/bin/env python3
"""Generate PASS 2 PyFR configs with a controlled sampler ladder."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = ROOT / "data" / "NASA_2DWMH_PyFR"
CFG_DIR = CASE_DIR / "configs"
SAMPLE_DIR = CASE_DIR / "sampling"
CHORD = 0.42
X_MIN = -1.35
X_MAX = 0.84
TOP_Z = 0.35
U_INF = 34.6
NU = 1.5534188034188036e-05
AC_ZETA = 1600.0


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return 0.053 * math.sin(math.pi * xi) ** 2


def top_height(x: float) -> float:
    if x <= -0.25 or x >= 0.65:
        return TOP_Z
    xi = (x + 0.25) / 0.90
    return TOP_Z - 0.02 * math.sin(math.pi * xi) ** 2


def tuple_list(points: list[tuple[float, float]]) -> str:
    return "[" + ", ".join(f"({x:.9f}, {y:.9f})" for x, y in points) + "]"


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def sample_sets() -> dict[str, list[tuple[float, float]]]:
    field_rows = load_manifest(SAMPLE_DIR / "field_points.csv")
    wall_rows = load_manifest(SAMPLE_DIR / "wall_points.csv")
    eval_rows = load_manifest(SAMPLE_DIR / "eval_points.csv")

    field_only = [
        (float(r["x_m"]), float(r["y_m"]))
        for r in field_rows[:: max(1, len(field_rows) // 9)][:9]
    ]
    sparse_wall = [
        (float(r["x_probe1_m"]), float(r["y_probe1_m"]))
        for r in wall_rows[:: max(1, len(wall_rows) // 8)][:8]
    ]
    full_wall = [
        (float(r["x_probe1_m"]), float(r["y_probe1_m"]))
        for r in wall_rows
    ]
    eval_subset = [
        (float(r["x_m"]), float(r["y_m"]))
        for r in eval_rows[:: max(1, len(eval_rows) // 12)][:12]
    ]

    return {
        "field_only": field_only,
        "sparse_wall": sparse_wall,
        "full_wall": full_wall,
        "evaluation_subset": eval_subset,
    }


def cfg_text(run_name: str, *, tend: float, dt: float, pseudo_dt: float, pseudo_niters: int, order: int, sampler_mode: str) -> str:
    run_dir = f"runs/gpu_pyfr_pass2/{run_name}"
    text = f"""[backend]
precision = double
rank-allocator = linear

[backend-cuda]
device-id = local-rank
mpi-type = standard

[constants]
nu = {NU:.12e}
ac-zeta = {AC_ZETA:.6f}

[solver]
system = ac-navier-stokes
order = {order}
anti-alias = flux

[solver-time-integrator]
formulation = dual
scheme = backward-euler
pseudo-scheme = rk45
controller = none
pseudo-controller = local-pi
tstart = 0.0
tend = {tend:.6f}
dt = {dt:.6f}
pseudo-dt = {pseudo_dt:.6f}
pseudo-niters-max = {pseudo_niters:d}
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
quad-deg = {2*order + 4}
quad-pts = gauss-legendre

[solver-elements-tri]
soln-pts = williams-shunn
quad-deg = {2*order + 4}
quad-pts = williams-shunn

[soln-ics]
p = 0.0
u = {U_INF:.6f}
v = 0.0

[soln-bcs-inlet]
type = ac-in-fv
u = {U_INF:.6f}
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
basedir = {run_dir}/solutions
basename = {run_name}
dt-out = {dt:.6f}

[soln-plugin-pseudostats]
file = {run_dir}/pseudo_stats
flushsteps = 20

[soln-plugin-fluidforce-bottomwall]
nsteps = 5
file = {run_dir}/fluidforce_bottomWall
"""

    sets = sample_sets()
    if sampler_mode == "minimal":
        return text
    if sampler_mode == "field_only":
        return text + f"""

[soln-plugin-sampler-fieldmini]
nsteps = 5
format = primitive
file = {run_dir}/fieldmini
samp-pts = {tuple_list(sets["field_only"])}
"""
    if sampler_mode == "sparse_wall":
        return text + f"""

[soln-plugin-sampler-fieldmini]
nsteps = 5
format = primitive
file = {run_dir}/fieldmini
samp-pts = {tuple_list(sets["field_only"])}

[soln-plugin-sampler-wallmini]
nsteps = 5
format = primitive
file = {run_dir}/wallmini
samp-pts = {tuple_list(sets["sparse_wall"])}
"""
    return text + f"""

[soln-plugin-sampler-fieldmini]
nsteps = 5
format = primitive
file = {run_dir}/fieldmini
samp-pts = {tuple_list(sets["field_only"])}

[soln-plugin-sampler-wallfull]
nsteps = 5
format = primitive
file = {run_dir}/wallfull
samp-pts = {tuple_list(sets["full_wall"])}

[soln-plugin-sampler-evalmini]
nsteps = 5
format = primitive
file = {run_dir}/evalmini
samp-pts = {tuple_list(sets["evaluation_subset"])}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=["minimal", "field_only", "sparse_wall", "full_wall", "all"],
        default="all",
    )
    args = parser.parse_args()

    CFG_DIR.mkdir(parents=True, exist_ok=True)
    variants = [args.variant] if args.variant != "all" else ["minimal", "field_only", "sparse_wall", "full_wall"]

    settings = {
        "minimal": dict(tend=0.12, dt=0.02, pseudo_dt=0.0005, pseudo_niters=12, order=1),
        "field_only": dict(tend=0.12, dt=0.02, pseudo_dt=0.0005, pseudo_niters=12, order=1),
        "sparse_wall": dict(tend=0.10, dt=0.02, pseudo_dt=0.0004, pseudo_niters=12, order=1),
        "full_wall": dict(tend=0.08, dt=0.02, pseudo_dt=0.0003, pseudo_niters=10, order=1),
    }

    for variant in variants:
        text = cfg_text(f"pass2_{variant}", sampler_mode=variant, **settings[variant])
        (CFG_DIR / f"pass2_{variant}.ini").write_text(text)
        manifest = {
            "mesh": "nasa_hump_medium.pyfrm",
            "run_name": f"pass2_{variant}",
            "variant": variant,
            **settings[variant],
        }
        (CFG_DIR / f"pass2_{variant}_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
