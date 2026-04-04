#!/usr/bin/env python3
"""Create second-pass NASA hump data and figures from available CFD outputs."""

from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, griddata


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "data" / "NASA_2DWMH"
DOCS_DATA = ROOT / "documentation_src" / "data_second_pass"
DOCS_FIG = ROOT / "documentation_src" / "figures_second_pass"
FIRST_PASS_DATA = ROOT / "docs" / "data" / "reconstructed_nasa_score.json"
FIRST_PASS_FIG = ROOT / "docs" / "figures"
CHORD = 0.42
U_REF = 34.6
RHO = 1.225
Q_REF = 0.5 * RHO * U_REF**2
STATIONS = [
    ("xm214", -2.14),
    ("x065", 0.65),
    ("x080", 0.80),
    ("x090", 0.90),
    ("x100", 1.00),
    ("x110", 1.10),
    ("x120", 1.20),
    ("x130", 1.30),
]


def ensure_dirs() -> None:
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    DOCS_FIG.mkdir(parents=True, exist_ok=True)


def latest_numeric_dir(base: Path) -> Path:
    numeric_dirs = []
    for child in base.iterdir():
        if child.is_dir():
            try:
                numeric_dirs.append((float(child.name), child))
            except ValueError:
                continue
    if not numeric_dirs:
        raise FileNotFoundError(f"No numeric directories found in {base}")
    return max(numeric_dirs, key=lambda item: item[0])[1]


def parse_internal_field(path: Path) -> np.ndarray:
    text = path.read_text().splitlines()
    start = None
    count = None
    for idx, line in enumerate(text):
        stripped = line.strip()
        if stripped.isdigit():
            count = int(stripped)
            start = idx + 2
            break
    if start is None or count is None:
        raise ValueError(f"Could not parse internal field size from {path}")

    rows = []
    for line in text[start:]:
        stripped = line.strip()
        if stripped in {")", ");"}:
            break
        if stripped.startswith("(") and stripped.endswith(")"):
            rows.append([float(val) for val in stripped[1:-1].split()])
        elif stripped:
            rows.append([float(stripped)])
    arr = np.asarray(rows, dtype=float)
    if arr.shape[0] != count:
        raise ValueError(f"Expected {count} rows in {path}, found {arr.shape[0]}")
    return arr


def parse_bottom_wall_shear(path: Path) -> np.ndarray:
    text = path.read_text().splitlines()
    start = None
    count = None
    for idx, line in enumerate(text):
        if line.strip() == "bottomWall":
            for j in range(idx, min(idx + 15, len(text))):
                stripped = text[j].strip()
                if stripped.isdigit():
                    count = int(stripped)
                    start = j + 2
                    break
            break
    if start is None or count is None:
        raise ValueError(f"Could not locate bottomWall data in {path}")

    rows = []
    for line in text[start:]:
        stripped = line.strip()
        if stripped in {")", ");"}:
            break
        if stripped.startswith("(") and stripped.endswith(")"):
            rows.append([float(val) for val in stripped[1:-1].split()])
    arr = np.asarray(rows, dtype=float)
    if arr.shape[0] != count:
        raise ValueError(f"Expected {count} bottom-wall vectors in {path}, found {arr.shape[0]}")
    return arr


def parse_residuals(log_path: Path) -> np.ndarray:
    import re

    time_pat = re.compile(r"^Time = (\d+)")
    field_pat = {
        "U": re.compile(r"Solving for Ux, Initial residual = ([0-9.eE+-]+)"),
        "p": re.compile(r"Solving for p, Initial residual = ([0-9.eE+-]+)"),
        "k": re.compile(r"Solving for k, Initial residual = ([0-9.eE+-]+)"),
        "omega": re.compile(r"Solving for omega, Initial residual = ([0-9.eE+-]+)"),
    }

    current_time = None
    current = {}
    rows = []
    for line in log_path.read_text().splitlines():
        match = time_pat.match(line.strip())
        if match:
            if current_time is not None and {"U", "p", "k", "omega"} <= current.keys():
                rows.append([current_time, current["U"], current["p"], current["k"], current["omega"]])
            current_time = int(match.group(1))
            current = {}
            continue
        for key, pattern in field_pat.items():
            match = pattern.search(line)
            if match and key not in current:
                current[key] = float(match.group(1))
    if current_time is not None and {"U", "p", "k", "omega"} <= current.keys():
        rows.append([current_time, current["U"], current["p"], current["k"], current["omega"]])
    return np.asarray(rows, dtype=float)


def save_csv(path: Path, header: list[str], rows: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows.tolist())


def parse_case_def(path: Path) -> dict[str, object]:
    text = path.read_text().splitlines()
    data: dict[str, object] = {}
    for line in text:
        stripped = line.strip().rstrip(";")
        if not stripped or stripped.startswith("//"):
            continue
        if stripped.startswith("xMin"):
            data["xMin"] = float(stripped.split()[-1])
        elif stripped.startswith("xMax"):
            data["xMax"] = float(stripped.split()[-1])
        elif stripped.startswith("chord"):
            data["chord"] = float(stripped.split()[-1])
        elif stripped.startswith("zTop"):
            data["zTop"] = float(stripped.split()[-1])
        elif stripped.startswith("xSplits"):
            tokens = stripped[stripped.index("(") + 1:stripped.index(")")].split()
            data["xSplits"] = [float(token) for token in tokens]
        elif stripped.startswith("xCells"):
            tokens = stripped[stripped.index("(") + 1:stripped.index(")")].split()
            data["xCells"] = [int(token) for token in tokens]
    return data


def get_solution_fields() -> dict[str, np.ndarray | str]:
    latest = latest_numeric_dir(CASE_DIR)
    return {
        "latest_name": latest.name,
        "coords": parse_internal_field(CASE_DIR / "0" / "C"),
        "U": parse_internal_field(latest / "U"),
        "p": parse_internal_field(latest / "p").ravel(),
        "k": parse_internal_field(latest / "k").ravel(),
        "omega": parse_internal_field(latest / "omega").ravel(),
        "nut": parse_internal_field(latest / "nut").ravel(),
        "tau_wall": parse_bottom_wall_shear(latest / "wallShearStress"),
    }


def sample_field_column(coords: np.ndarray, values: np.ndarray, x_target: float, y_values: np.ndarray) -> np.ndarray:
    points = np.column_stack((coords[:, 0], coords[:, 1]))
    query = np.column_stack((np.full_like(y_values, x_target), y_values))
    linear = LinearNDInterpolator(points, values)
    nearest = NearestNDInterpolator(points, values)
    sampled = linear(query)
    nan_mask = np.isnan(sampled)
    if np.any(nan_mask):
        sampled[nan_mask] = nearest(query[nan_mask])
    return sampled


def build_station_profiles(fields: dict[str, np.ndarray | str]) -> dict[str, dict[str, np.ndarray | float]]:
    coords = fields["coords"]
    x_min = float(np.min(coords[:, 0]))
    y_max = float(np.max(coords[:, 1]))
    common_y = np.linspace(0.0, y_max, 240)

    profiles: dict[str, dict[str, np.ndarray | float]] = {}
    for stem, xc in STATIONS:
        x_target = xc * CHORD
        x_target = max(x_min + 1e-4, x_target)
        profile = {
            "x_over_c": xc,
            "x_m": x_target,
            "y_m": common_y,
            "Ux_ms": sample_field_column(coords, fields["U"][:, 0], x_target, common_y),
            "Uy_ms": sample_field_column(coords, fields["U"][:, 1], x_target, common_y),
            "p_m2s2": sample_field_column(coords, fields["p"], x_target, common_y),
            "k_m2s2": sample_field_column(coords, fields["k"], x_target, common_y),
            "omega_s-1": sample_field_column(coords, fields["omega"], x_target, common_y),
            "nut_m2s-1": sample_field_column(coords, fields["nut"], x_target, common_y),
        }
        profiles[stem] = profile
        rows = np.column_stack(
            (
                np.full_like(common_y, x_target),
                common_y,
                profile["Ux_ms"],
                profile["Uy_ms"],
                profile["p_m2s2"],
                profile["k_m2s2"],
                profile["omega_s-1"],
                profile["nut_m2s-1"],
            )
        )
        save_csv(
            DOCS_DATA / f"profile_{stem}_second_pass.csv",
            ["x_m", "y_m", "Ux_ms", "Uy_ms", "p_m2s2", "k_m2s2", "omega_s-1", "nut_m2s-1"],
            rows,
        )
    return profiles


def build_wall_series(fields: dict[str, np.ndarray | str]) -> dict[str, np.ndarray | float | None]:
    coords = fields["coords"]
    p = fields["p"]
    tau = fields["tau_wall"][:, 0]
    case_def = parse_case_def(CASE_DIR / "caseDef")
    if "xSplits" in case_def:
        x_splits = np.asarray(case_def["xSplits"], dtype=float)
    else:
        x_splits = np.array(
            [
                float(case_def["xMin"]),
                0.0,
                float(case_def["chord"]),
                float(case_def["xMax"]),
            ],
            dtype=float,
        )
    x_cells = list(case_def["xCells"])
    x_segments = []
    for i, n_cells in enumerate(x_cells):
        edges = np.linspace(x_splits[i], x_splits[i + 1], n_cells + 1)
        x_segments.append(0.5 * (edges[:-1] + edges[1:]))
    x = np.concatenate(x_segments)
    if len(x) != len(tau):
        x_min = float(np.min(coords[:, 0]))
        x_max = float(np.max(coords[:, 0]))
        x_edges = np.linspace(x_min, x_max, len(tau) + 1)
        x = 0.5 * (x_edges[:-1] + x_edges[1:])

    p_wall = np.zeros(len(tau))
    for i in range(len(tau)):
        window = max((x[1] - x[0]) * 1.5 if len(x) > 1 else 0.002, 0.002)
        mask = np.abs(coords[:, 0] - x[i]) <= window
        if not np.any(mask):
            p_wall[i] = p_wall[i - 1] if i > 0 else p[0]
            continue
        local_coords = coords[mask]
        local_p = p[mask]
        min_y = float(local_coords[:, 1].min())
        near_wall = np.abs(local_coords[:, 1] - min_y) < 0.003
        p_wall[i] = float(local_p[near_wall].mean()) if np.any(near_wall) else float(local_p.mean())

    x_ref = -2.14 * CHORD
    ref_mask = (np.abs(coords[:, 0] - x_ref) < 0.01) & (coords[:, 1] > 0.04)
    if not np.any(ref_mask):
        ref_mask = np.abs(coords[:, 0] - x_ref) < 0.01
    p_ref = float(np.mean(p[ref_mask])) if np.any(ref_mask) else float(p[0])

    cp = (p_wall - p_ref) / Q_REF
    cf = -tau / Q_REF

    separation = None
    reattachment = None
    post_hump = x >= 0.0
    neg = np.where((cf < 0.0) & post_hump)[0]
    if len(neg) > 0:
        separation = float(x[neg[0]])
        pos_after = np.where((cf > 0.0) & (x > separation))[0]
        if len(pos_after) > 0:
            reattachment = float(x[pos_after[0]])

    rows = np.column_stack((x, x / CHORD, cp, cf, tau, p_wall))
    save_csv(
        DOCS_DATA / "wall_coefficients_second_pass.csv",
        ["x_m", "x_over_c", "Cp", "Cf", "tau_w_m2s2", "p_wall_m2s2"],
        rows,
    )
    return {
        "x_m": x,
        "x_over_c": x / CHORD,
        "cp": cp,
        "cf": cf,
        "tau": tau,
        "separation_x_m": separation,
        "reattachment_x_m": reattachment,
    }


def build_shear_stress_profiles(profiles: dict[str, dict[str, np.ndarray | float]]) -> dict[str, np.ndarray]:
    stems = [stem for stem, _ in STATIONS]
    x_positions = np.asarray([profiles[stem]["x_m"] for stem in stems], dtype=float)
    common_y = np.asarray(profiles[stems[0]]["y_m"], dtype=float)

    shear_map: dict[str, np.ndarray] = {}
    for idx, stem in enumerate(stems):
        ux = np.asarray(profiles[stem]["Ux_ms"], dtype=float)
        uy = np.asarray(profiles[stem]["Uy_ms"], dtype=float)
        nut = np.asarray(profiles[stem]["nut_m2s-1"], dtype=float)
        dudy = np.gradient(ux, common_y, edge_order=2)

        if idx == 0:
            dx = x_positions[idx + 1] - x_positions[idx]
            dvdx = (
                np.asarray(profiles[stems[idx + 1]]["Uy_ms"], dtype=float) - uy
            ) / dx
        elif idx == len(stems) - 1:
            dx = x_positions[idx] - x_positions[idx - 1]
            dvdx = (
                uy - np.asarray(profiles[stems[idx - 1]]["Uy_ms"], dtype=float)
            ) / dx
        else:
            dx = x_positions[idx + 1] - x_positions[idx - 1]
            dvdx = (
                np.asarray(profiles[stems[idx + 1]]["Uy_ms"], dtype=float)
                - np.asarray(profiles[stems[idx - 1]]["Uy_ms"], dtype=float)
            ) / dx

        tau_uv = -nut * (dudy + dvdx)
        shear_map[stem] = tau_uv
        rows = np.column_stack((np.full_like(common_y, profiles[stem]["x_m"], dtype=float), common_y, tau_uv))
        save_csv(
            DOCS_DATA / f"turbulent_shear_{stem}_second_pass.csv",
            ["x_m", "y_m", "tau_uv_m2s2"],
            rows,
        )
    return shear_map


def plot_residuals(residuals: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(residuals[:, 0], residuals[:, 1], label="U")
    ax.semilogy(residuals[:, 0], residuals[:, 2], label="p")
    ax.semilogy(residuals[:, 0], residuals[:, 3], label="k")
    ax.semilogy(residuals[:, 0], residuals[:, 4], label="omega")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Initial residual")
    ax.set_title("Residual history")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "residual_history_second_pass.png", dpi=200)
    plt.close(fig)


def plot_velocity_profiles(profiles: dict[str, dict[str, np.ndarray | float]]) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharey=True)
    axes = axes.flatten()
    for ax, (stem, xc) in zip(axes, STATIONS):
        profile = profiles[stem]
        ax.plot(profile["Ux_ms"], profile["y_m"], color="tab:blue")
        ax.set_title(f"x/c = {xc}")
        ax.set_xlabel("u [m/s]")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("y [m]")
    fig.suptitle("Streamwise-velocity profiles")
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "velocity_profiles_second_pass.png", dpi=200)
    plt.close(fig)


def plot_shear_profiles(profiles: dict[str, dict[str, np.ndarray | float]], shear_map: dict[str, np.ndarray]) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharey=True)
    axes = axes.flatten()
    for ax, (stem, xc) in zip(axes, STATIONS):
        ax.plot(shear_map[stem], profiles[stem]["y_m"], color="tab:red")
        ax.set_title(f"x/c = {xc}")
        ax.set_xlabel(r"$-\overline{u'v'}$ analog [m$^2$/s$^2$]")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("y [m]")
    fig.suptitle("Modeled turbulent shear-stress analog profiles")
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "turbulent_shear_profiles_second_pass.png", dpi=200)
    plt.close(fig)


def plot_wall_coefficients(wall: dict[str, np.ndarray | float | None]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(wall["x_over_c"], wall["cp"], color="tab:purple")
    axes[0].set_ylabel("Cp")
    axes[0].set_title("Pressure coefficient along hump wall")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(wall["x_over_c"], wall["cf"], color="tab:green")
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_xlabel("x/c")
    axes[1].set_ylabel("Cf")
    axes[1].set_title("Skin-friction coefficient along hump wall")
    axes[1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(DOCS_FIG / "cp_cf_second_pass.png", dpi=200)
    plt.close(fig)


def plot_field_contours(fields: dict[str, np.ndarray | str]) -> None:
    coords = fields["coords"]
    u = fields["U"]
    p = fields["p"]
    x = coords[:, 0]
    y = coords[:, 1]
    speed = np.linalg.norm(u, axis=1)
    cp_field = (p - np.median(p[x < -0.75])) / Q_REF
    tri = mtri.Triangulation(x, y)

    for values, title, filename, cmap in [
        (speed, "Velocity magnitude", "velocity_contour_second_pass.png", "viridis"),
        (cp_field, "Pressure coefficient field", "pressure_contour_second_pass.png", "coolwarm"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 3.8))
        contour = ax.tricontourf(tri, values, levels=40, cmap=cmap)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(title)
        fig.colorbar(contour, ax=ax)
        fig.tight_layout()
        fig.savefig(DOCS_FIG / filename, dpi=200)
        plt.close(fig)


def plot_streamlines(fields: dict[str, np.ndarray | str]) -> None:
    coords = fields["coords"]
    u = fields["U"]
    x = coords[:, 0]
    y = coords[:, 1]
    xmin, xmax = float(np.min(x)), float(np.max(x))
    ymin, ymax = float(np.min(y)), float(np.max(y))
    xi = np.linspace(xmin, xmax, 280)
    yi = np.linspace(ymin, ymax, 120)
    xx, yy = np.meshgrid(xi, yi)
    uu = griddata((x, y), u[:, 0], (xx, yy), method="linear")
    vv = griddata((x, y), u[:, 1], (xx, yy), method="linear")
    spd = np.sqrt(np.nan_to_num(uu) ** 2 + np.nan_to_num(vv) ** 2)

    mask = np.isnan(uu) | np.isnan(vv)
    uu[mask] = 0.0
    vv[mask] = 0.0

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.streamplot(xi, yi, uu, vv, density=2.0, color=spd, cmap="plasma", linewidth=1.0)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Streamline-style flow visualization")
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "streamlines_second_pass.png", dpi=200)
    plt.close(fig)


def copy_paraview_artifacts() -> list[str]:
    copied = []
    for name in [
        "paraview_velocity.png",
        "paraview_velocity_surface.png",
        "paraview_pressure.png",
        "paraview_pressure_surface.png",
        "paraview_streamlines.png",
        "paraview_mesh_wireframe.png",
        "paraview_wall_shear.png",
    ]:
        source = FIRST_PASS_FIG / name
        if source.exists():
            target = DOCS_FIG / name
            shutil.copy2(source, target)
            copied.append(str(target.relative_to(ROOT)))
    return copied


def write_summary(
    fields: dict[str, np.ndarray | str],
    wall: dict[str, np.ndarray | float | None],
    residuals: np.ndarray,
    copied_paraview: list[str],
) -> None:
    first_pass_score = None
    if FIRST_PASS_DATA.exists():
        first_pass_score = json.loads(FIRST_PASS_DATA.read_text()).get("score")

    summary = {
        "latest_time_directory": fields["latest_name"],
        "reference_freestream_ms": U_REF,
        "reference_chord_m": CHORD,
        "first_pass_score_reference": first_pass_score,
        "residual_iterations_available": int(residuals[-1, 0]) if residuals.size else None,
        "final_residuals": {
            "U": None if residuals.size == 0 else float(residuals[-1, 1]),
            "p": None if residuals.size == 0 else float(residuals[-1, 2]),
            "k": None if residuals.size == 0 else float(residuals[-1, 3]),
            "omega": None if residuals.size == 0 else float(residuals[-1, 4]),
        },
        "separation_x_m": wall["separation_x_m"],
        "reattachment_x_m": wall["reattachment_x_m"],
        "paraview_images_copied": copied_paraview,
        "docker_second_pass_run_status": "pending_or_blocked_until_new_case_run",
    }
    (DOCS_DATA / "second_pass_summary.json").write_text(json.dumps(summary, indent=2))


def main() -> None:
    ensure_dirs()
    fields = get_solution_fields()
    profiles = build_station_profiles(fields)
    wall = build_wall_series(fields)
    shear_map = build_shear_stress_profiles(profiles)
    residuals = parse_residuals(CASE_DIR / "log.run")
    save_csv(DOCS_DATA / "residual_history_second_pass.csv", ["iteration", "U", "p", "k", "omega"], residuals)

    plot_residuals(residuals)
    plot_velocity_profiles(profiles)
    plot_shear_profiles(profiles, shear_map)
    plot_wall_coefficients(wall)
    plot_field_contours(fields)
    plot_streamlines(fields)
    copied_paraview = copy_paraview_artifacts()
    write_summary(fields, wall, residuals, copied_paraview)


if __name__ == "__main__":
    main()
