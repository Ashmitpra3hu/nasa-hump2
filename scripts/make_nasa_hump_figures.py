#!/usr/bin/env python3
"""Create plots and machine-readable summaries for the reconstructed NASA hump case."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "data" / "NASA_2DWMH"
DOCS_DATA = ROOT / "docs" / "data"
DOCS_FIG = ROOT / "docs" / "figures"
U_REF = 34.6
RHO = 1.225
Q_REF = 0.5 * RHO * U_REF**2

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")


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


def get_solution_fields() -> dict[str, np.ndarray]:
    latest = latest_numeric_dir(CASE_DIR)
    return {
        "latest_name": np.array([latest.name]),
        "coords": parse_internal_field(CASE_DIR / "0" / "C"),
        "U": parse_internal_field(latest / "U"),
        "p": parse_internal_field(latest / "p").ravel(),
        "k": parse_internal_field(latest / "k").ravel(),
        "omega": parse_internal_field(latest / "omega").ravel(),
        "nut": parse_internal_field(latest / "nut").ravel(),
        "tau_wall": parse_bottom_wall_shear(latest / "wallShearStress"),
    }


def nearest_column_data(fields: dict[str, np.ndarray], x_target: float) -> np.ndarray:
    coords = fields["coords"]
    tol = 0.002
    mask = np.abs(coords[:, 0] - x_target) < tol
    if not np.any(mask):
        tol = 0.003
        mask = np.abs(coords[:, 0] - x_target) < tol
    local = np.column_stack(
        (
            coords[mask],
            fields["U"][mask],
            fields["p"][mask],
            fields["k"][mask],
            fields["omega"][mask],
            fields["nut"][mask],
        )
    )
    local = local[np.argsort(local[:, 1])]

    y_bins = np.linspace(local[:, 1].min(), local[:, 1].max(), 181)
    bucket = np.digitize(local[:, 1], y_bins) - 1
    rows = []
    for idx in range(180):
        members = local[bucket == idx]
        if len(members) == 0:
            continue
        rows.append(members.mean(axis=0))
    return np.asarray(rows)


def build_profile_exports(fields: dict[str, np.ndarray]) -> list[dict[str, str | float]]:
    station_meta = [
        ("profile_xm214", -0.8988, -2.14),
        ("profile_x065", 0.2730, 0.65),
        ("profile_x080", 0.3360, 0.80),
        ("profile_x090", 0.3780, 0.90),
        ("profile_x100", 0.4200, 1.00),
        ("profile_x110", 0.4620, 1.10),
        ("profile_x120", 0.5040, 1.20),
        ("profile_x130", 0.5460, 1.30),
    ]

    manifest = []
    for stem, x_target, xc in station_meta:
        rows = nearest_column_data(fields, x_target)
        out = DOCS_DATA / f"{stem}.csv"
        save_csv(
            out,
            ["x_m", "y_m", "z_m", "Ux_ms", "Uy_ms", "Uz_ms", "p_m2s2", "k_m2s2", "omega_s-1", "nut_m2s-1"],
            rows,
        )
        manifest.append({"station": stem, "x_target_m": x_target, "x_over_c": xc, "file": str(out.relative_to(ROOT))})

    (DOCS_DATA / "profile_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def plot_residuals(residuals: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(residuals[:, 0], residuals[:, 1], label="U")
    ax.semilogy(residuals[:, 0], residuals[:, 2], label="p")
    ax.semilogy(residuals[:, 0], residuals[:, 3], label="k")
    ax.semilogy(residuals[:, 0], residuals[:, 4], label="omega")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Initial residual")
    ax.set_title("Residual history from log.run")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "residual_history.png", dpi=200)
    plt.close(fig)


def plot_profiles(manifest: list[dict[str, str | float]]) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharey=True)
    axes = axes.flatten()

    for ax, item in zip(axes, manifest):
        data = np.loadtxt(ROOT / str(item["file"]), delimiter=",", skiprows=1)
        ax.plot(data[:, 3], data[:, 1], color="tab:blue")
        ax.set_title(f"x/c = {item['x_over_c']}")
        ax.set_xlabel("u [m/s]")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("y [m]")
    fig.suptitle("Vertical streamwise-velocity profiles")
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "velocity_profiles.png", dpi=200)
    plt.close(fig)


def plot_field_contours(fields: dict[str, np.ndarray]) -> None:
    coords = fields["coords"]
    u = fields["U"]
    p = fields["p"]
    x = coords[:, 0]
    y = coords[:, 1]
    speed = np.linalg.norm(u, axis=1)
    cp_field = (p - np.median(p[x < -0.75])) / Q_REF
    tri = mtri.Triangulation(x, y)

    for values, title, filename, cmap in [
        (speed, "Velocity magnitude", "velocity_contour.png", "viridis"),
        (cp_field, "Pressure coefficient field", "pressure_contour.png", "coolwarm"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 3.6))
        contour = ax.tricontourf(tri, values, levels=40, cmap=cmap)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(title)
        fig.colorbar(contour, ax=ax)
        fig.tight_layout()
        fig.savefig(DOCS_FIG / filename, dpi=200)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.triplot(tri, linewidth=0.1, color="black", alpha=0.75)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Mesh overview")
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "mesh_overview.png", dpi=200)
    plt.close(fig)

    zoom_mask = (x > -0.05) & (x < 0.5) & (y < 0.18)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    contour = ax.tricontourf(x[zoom_mask], y[zoom_mask], speed[zoom_mask], levels=40, cmap="viridis")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Hump-region velocity magnitude")
    fig.colorbar(contour, ax=ax)
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "hump_closeup_velocity.png", dpi=200)
    plt.close(fig)


def plot_wall_quantities(fields: dict[str, np.ndarray]) -> dict[str, float | None]:
    coords = fields["coords"]
    p = fields["p"]
    tau = fields["tau_wall"][:, 0]
    x_min = -0.9
    x_max = 0.67
    x_edges = np.linspace(x_min, x_max, len(tau) + 1)
    x = 0.5 * (x_edges[:-1] + x_edges[1:])

    p_wall_like = np.zeros(len(tau))
    for i in range(len(tau)):
        mask = (coords[:, 0] >= x_edges[i]) & (coords[:, 0] < x_edges[i + 1])
        if not np.any(mask):
            p_wall_like[i] = p_wall_like[i - 1] if i > 0 else p[0]
            continue
        local_coords = coords[mask]
        local_p = p[mask]
        min_y = local_coords[:, 1].min()
        near_wall = np.abs(local_coords[:, 1] - min_y) < 0.0025
        p_wall_like[i] = local_p[near_wall].mean()

    cp = (p_wall_like - p_wall_like[0]) / Q_REF
    cf = tau / Q_REF

    sep = None
    reattach = None
    for i in range(1, len(tau)):
        if sep is None and cf[i - 1] >= 0.0 and cf[i] < 0.0 and x[i] > 0.0:
            frac = -cf[i - 1] / (cf[i] - cf[i - 1]) if cf[i] != cf[i - 1] else 0.0
            sep = x[i - 1] + frac * (x[i] - x[i - 1])
        if cf[i - 1] < 0.0 and cf[i] >= 0.0 and x[i] > 0.0:
            frac = -cf[i - 1] / (cf[i] - cf[i - 1]) if cf[i] != cf[i - 1] else 0.0
            reattach = x[i - 1] + frac * (x[i] - x[i - 1])
            break

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(x, cp, color="tab:red")
    axes[0].set_ylabel("Cp")
    axes[0].set_title("Near-wall pressure coefficient")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(x, cf, color="tab:green")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_xlabel("x [m]")
    axes[1].set_ylabel("Cf")
    axes[1].set_title("Bottom-wall skin-friction coefficient")
    axes[1].grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(DOCS_FIG / "wall_coefficients.png", dpi=200)
    plt.close(fig)

    rows = np.column_stack((x, cp, cf, tau))
    save_csv(DOCS_DATA / "wall_coefficients.csv", ["x_m", "Cp_near_wall", "Cf", "tau_x_Pa"], rows)
    return {"separation_x_m": sep, "reattachment_x_m": reattach}


def write_summary(residuals: np.ndarray, indicators: dict[str, float | None], latest_name: str) -> None:
    summary = {
        "latest_iteration_directory": latest_name,
        "final_residuals": {
            "U": float(residuals[-1, 1]),
            "p": float(residuals[-1, 2]),
            "k": float(residuals[-1, 3]),
            "omega": float(residuals[-1, 4]),
        },
        "derived_indicators": indicators,
    }
    (DOCS_DATA / "summary.json").write_text(json.dumps(summary, indent=2))


def main() -> None:
    ensure_dirs()
    fields = get_solution_fields()
    residuals = parse_residuals(CASE_DIR / "log.run")
    save_csv(DOCS_DATA / "residual_history.csv", ["iteration", "U", "p", "k", "omega"], residuals)
    plot_residuals(residuals)
    manifest = build_profile_exports(fields)
    plot_profiles(manifest)
    plot_field_contours(fields)
    indicators = plot_wall_quantities(fields)
    write_summary(residuals, indicators, str(fields["latest_name"][0]))


if __name__ == "__main__":
    main()
