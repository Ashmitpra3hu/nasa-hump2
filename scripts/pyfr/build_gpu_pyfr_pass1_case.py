#!/usr/bin/env python3
"""Generate PyFR PASS 1 meshes, sampling manifests, and ini files."""

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
MESH_DIR = CASE_DIR / "meshes"
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"
EVAL_POINTS = ROOT / "data" / "evaluation_points" / "NASA_2DWMH_points.csv"

CHORD = 0.42
X_MIN = -1.35
X_MAX = 0.84
TOP_Z = 0.35
U_INF = 34.6
NU = 1.5534188034188036e-05
AC_ZETA = 1600.0
RHO = 1.225
Q_REF = 0.5 * RHO * U_INF**2
PROFILE_STATIONS = [-2.14, 0.65, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30]
PROFILE_LABELS = ["xm214", "x065", "x080", "x090", "x100", "x110", "x120", "x130"]


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return 0.053 * math.sin(math.pi * xi) ** 2


def hump_slope(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return 0.053 * math.sin(2.0 * math.pi * xi) * math.pi / CHORD


def top_height(x: float) -> float:
    if x <= -0.25 or x >= 0.65:
        return TOP_Z
    xi = (x + 0.25) / 0.90
    return TOP_Z - 0.02 * math.sin(math.pi * xi) ** 2


def load_csv(path: Path, cols: int) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open() as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            rows.append([float(val) for val in row[:cols]])
    return np.asarray(rows, dtype=float)


def wall_offset_point(x: float, offset: float) -> tuple[float, float]:
    y = hump_height(x)
    dydx = hump_slope(x)
    nx = -dydx
    ny = 1.0
    scale = math.hypot(nx, ny)
    return x + offset * nx / scale, y + offset * ny / scale


def tuple_list(points: list[tuple[float, float]]) -> str:
    return "[" + ", ".join(f"({x:.9f}, {y:.9f})" for x, y in points) + "]"


def write_manifest(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def build_sampling_manifests() -> dict[str, object]:
    cp_exp = load_csv(EXP_DIR / "noflow_cp.csv", 2)
    cf_exp = load_csv(EXP_DIR / "noflow_cf.csv", 3)
    eval_pts = np.loadtxt(EVAL_POINTS, delimiter=",")

    wall_x_over_c = sorted({float(x) for x in cp_exp[:, 0]} | {float(x) for x in cf_exp[:, 0]})
    wall_rows = []
    wall_eps1 = []
    wall_eps2 = []
    for xoc in wall_x_over_c:
        x = min(max(xoc * CHORD, X_MIN + 1.0e-4), X_MAX - 1.0e-4)
        p1 = wall_offset_point(x, 5.0e-4)
        p2 = wall_offset_point(x, 1.5e-3)
        tx = 1.0
        ty = hump_slope(x)
        tmag = math.hypot(tx, ty)
        tx /= tmag
        ty /= tmag
        wall_rows.append([xoc, x, tx, ty, p1[0], p1[1], p2[0], p2[1]])
        wall_eps1.append(p1)
        wall_eps2.append(p2)
    write_manifest(
        SAMPLE_DIR / "wall_points.csv",
        ["x_over_c", "x_surface_m", "tx", "ty", "x_probe1_m", "y_probe1_m", "x_probe2_m", "y_probe2_m"],
        wall_rows,
    )

    profile_points = []
    profile_rows = []
    for label, xoc in zip(PROFILE_LABELS, PROFILE_STATIONS):
        x = xoc * CHORD
        ys = np.linspace(0.0, TOP_Z - 1.0e-3, 96)
        for j, y in enumerate(ys):
            profile_points.append((x, float(y)))
            profile_rows.append([label, xoc, j, x, y])
    write_manifest(
        SAMPLE_DIR / "profile_points.csv",
        ["station", "x_over_c", "index", "x_m", "y_m"],
        profile_rows,
    )

    field_points = []
    field_rows = []
    xs = np.linspace(X_MIN, X_MAX, 140)
    ys = np.linspace(0.0, TOP_Z, 64)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if y <= hump_height(float(x)) + 2.0e-4 or y >= top_height(float(x)) - 2.0e-4:
                continue
            field_points.append((float(x), float(y)))
            field_rows.append([i, j, x, y])
    write_manifest(SAMPLE_DIR / "field_points.csv", ["i", "j", "x_m", "y_m"], field_rows)

    eval_points = [(float(x), float(y)) for x, _, y in eval_pts]
    eval_rows = [[idx, x, y] for idx, (x, y) in enumerate(eval_points)]
    write_manifest(SAMPLE_DIR / "eval_points.csv", ["index", "x_m", "y_m"], eval_rows)

    summary = {
        "wall_probe1": len(wall_eps1),
        "wall_probe2": len(wall_eps2),
        "profiles": len(profile_points),
        "field": len(field_points),
        "evaluation": len(eval_points),
    }
    (SAMPLE_DIR / "sampling_summary.json").write_text(json.dumps(summary, indent=2))
    return {
        "wall_probe1": wall_eps1,
        "wall_probe2": wall_eps2,
        "profiles": profile_points,
        "field": field_points,
        "evaluation": eval_points,
        "summary": summary,
    }


def cfg_text(mesh_name: str, run_name: str, samples: dict[str, object], *, order: int, tend: float, dt: float, pseudo_dt: float, pseudo_niters: int, include_hump_sampling: bool = True) -> str:
    run_dir = f"runs/gpu_pyfr_pass1/{run_name}"
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

[solver-elements-quad]
soln-pts = gauss-legendre
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
    if not include_hump_sampling:
        return text

    return text + f"""

[soln-plugin-sampler-wallprobe1]
nsteps = 5
format = primitive
file = {run_dir}/wall_probe1
samp-pts = {tuple_list(samples["wall_probe1"])}

[soln-plugin-sampler-wallprobe2]
nsteps = 5
format = primitive
file = {run_dir}/wall_probe2
samp-pts = {tuple_list(samples["wall_probe2"])}

[soln-plugin-sampler-profiles]
nsteps = 5
format = primitive
file = {run_dir}/profiles
samp-pts = {tuple_list(samples["profiles"])}

[soln-plugin-sampler-field]
nsteps = 5
format = primitive
file = {run_dir}/field
samp-pts = {tuple_list(samples["field"])}

[soln-plugin-sampler-evaluation]
nsteps = 5
format = primitive
file = {run_dir}/evaluation
samp-pts = {tuple_list(samples["evaluation"])}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["smoke", "medium", "promoted", "all"], default="all")
    args = parser.parse_args()

    CFG_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    samples = build_sampling_manifests()

    variants = [args.variant] if args.variant != "all" else ["smoke", "medium", "promoted"]
    for variant in variants:
        if variant == "smoke":
            text = cfg_text("smoke_rect.pyfrm", "smoke_test", samples, order=1, tend=0.25, dt=0.05, pseudo_dt=0.002, pseudo_niters=10, include_hump_sampling=False)
            mesh = "smoke_rect.pyfrm"
        elif variant == "medium":
            text = cfg_text("nasa_hump_medium.pyfrm", "medium", samples, order=2, tend=0.40, dt=0.05, pseudo_dt=0.001, pseudo_niters=18)
            mesh = "nasa_hump_medium.pyfrm"
        else:
            text = cfg_text("nasa_hump_promoted.pyfrm", "promoted", samples, order=2, tend=0.60, dt=0.05, pseudo_dt=0.0008, pseudo_niters=24)
            mesh = "nasa_hump_promoted.pyfrm"

        (CFG_DIR / f"{variant}.ini").write_text(text)
        (CFG_DIR / f"{variant}_manifest.json").write_text(json.dumps({"mesh": mesh, "run_name": variant}, indent=2))


if __name__ == "__main__":
    main()
