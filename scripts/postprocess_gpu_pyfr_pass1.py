#!/usr/bin/env python3
"""Postprocess local GPU PyFR PASS 1 outputs into plots and summary tables."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from closure_challenge.eval import evaluate_individual_case


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "gpu_pyfr_pass1"
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"
SAMPLE_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "sampling"
OUT_DATA = ROOT / "documentation_src" / "data_gpu_pyfr_pass1"
OUT_FIG = ROOT / "documentation_src" / "figures_gpu_pyfr_pass1"
CHORD = 0.42
U_REF = 34.6
RHO = 1.225
NU = 1.5534188034188036e-05
Q_REF = 0.5 * RHO * U_REF**2


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def latest_rows(path: Path) -> list[dict[str, str]]:
    rows = load_csv(path)
    if not rows:
        return []
    tmax = max(float(r["t"]) for r in rows)
    return [r for r in rows if abs(float(r["t"]) - tmax) < 1.0e-12]


def nearest_sample(x_query: np.ndarray, x_data: np.ndarray, values: np.ndarray) -> np.ndarray:
    indices = np.abs(x_data[:, None] - x_query[None, :]).argmin(axis=0)
    return values[indices]


def parse_eval_case(case: str) -> dict[str, object]:
    base = RUNS / case
    eval_rows = latest_rows(base / "evaluation.csv")
    if not eval_rows:
        raise FileNotFoundError(base / "evaluation.csv")
    pred = np.array([[float(r["u"]), 0.0, float(r["v"])] for r in eval_rows], dtype=float)
    score = float(evaluate_individual_case("NASA_2DWMH", pred))
    np.savetxt(OUT_DATA / f"{case}_predictions.csv", pred, delimiter=",")
    return {"benchmark_mae": score, "n_eval": int(pred.shape[0])}


def parse_wall_case(case: str) -> dict[str, object]:
    base = RUNS / case
    probe1 = latest_rows(base / "wall_probe1.csv")
    probe2 = latest_rows(base / "wall_probe2.csv")
    manifest = load_csv(SAMPLE_DIR / "wall_points.csv")
    cp_exp = np.asarray([[float(r["x_over_c"]), float(r["Cp"])] for r in load_csv(EXP_DIR / "noflow_cp.csv")], dtype=float)
    cf_exp = np.asarray([[float(r["x_over_c"]), float(r["Cf"]), float(r["Cf_uncertainty"])] for r in load_csv(EXP_DIR / "noflow_cf.csv")], dtype=float)

    field_rows = latest_rows(base / "field.csv")
    field = np.array([[float(r["x"]), float(r["y"]), float(r["p"])] for r in field_rows], dtype=float)
    x_ref = -2.14 * CHORD
    ref_mask = (np.abs(field[:, 0] - x_ref) < 0.02) & (field[:, 1] > 0.04)
    if not np.any(ref_mask):
        ref_mask = np.abs(field[:, 0] - x_ref) < 0.05
    p_ref = float(np.mean(field[ref_mask, 2])) if np.any(ref_mask) else 0.0

    rows = []
    for meta, r1, r2 in zip(manifest, probe1, probe2):
        xoc = float(meta["x_over_c"])
        tx = float(meta["tx"])
        ty = float(meta["ty"])
        dx = float(meta["x_probe2_m"]) - float(meta["x_probe1_m"])
        dy = float(meta["y_probe2_m"]) - float(meta["y_probe1_m"])
        dn = math.hypot(dx, dy)
        ut1 = float(r1["u"]) * tx + float(r1["v"]) * ty
        ut2 = float(r2["u"]) * tx + float(r2["v"]) * ty
        dudy = (ut2 - ut1) / max(dn, 1.0e-8)
        cf = NU * dudy / Q_REF
        cp = (float(r1["p"]) - p_ref) / Q_REF
        rows.append([xoc, float(meta["x_surface_m"]), cp, cf])
    wall = np.asarray(rows, dtype=float)
    write_csv(OUT_DATA / f"{case}_wall_series.csv", ["x_over_c", "x_m", "Cp", "Cf"], wall)

    cp_pred = nearest_sample(cp_exp[:, 0], wall[:, 0], wall[:, 2])
    cf_pred = nearest_sample(cf_exp[:, 0], wall[:, 0], wall[:, 3])
    cp_err = cp_pred - cp_exp[:, 1]
    cf_err = cf_pred - cf_exp[:, 1]

    cp_rows = np.column_stack((cp_exp[:, 0], cp_exp[:, 1], cp_pred, cp_err))
    cf_rows = np.column_stack((cf_exp[:, 0], cf_exp[:, 1], cf_exp[:, 2], cf_pred, cf_err))
    write_csv(OUT_DATA / f"{case}_cp_comparison.csv", ["x_over_c", "Cp_exp", "Cp_pyfr", "Cp_error"], cp_rows)
    write_csv(OUT_DATA / f"{case}_cf_comparison.csv", ["x_over_c", "Cf_exp", "Cf_unc", "Cf_pyfr", "Cf_error"], cf_rows)

    return {
        "cp_mae": float(np.mean(np.abs(cp_err))),
        "cp_rmse": float(np.sqrt(np.mean(cp_err**2))),
        "cf_mae": float(np.mean(np.abs(cf_err))),
        "cf_rmse": float(np.sqrt(np.mean(cf_err**2))),
        "wall_rows": int(wall.shape[0]),
    }


def write_csv(path: Path, header: list[str], arr: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(arr.tolist())


def plot_field(case: str) -> None:
    rows = latest_rows(RUNS / case / "field.csv")
    if not rows:
        return
    pts = np.array([[float(r["x"]), float(r["y"]), float(r["u"]), float(r["v"]), float(r["p"])] for r in rows], dtype=float)
    tri = mtri.Triangulation(pts[:, 0], pts[:, 1])
    speed = np.sqrt(pts[:, 2] ** 2 + pts[:, 3] ** 2)

    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    c1 = axes[0].tricontourf(tri, speed, levels=30, cmap="viridis")
    axes[0].set_title(f"{case} velocity magnitude")
    axes[0].set_xlabel("x [m]")
    axes[0].set_ylabel("y [m]")
    fig.colorbar(c1, ax=axes[0], label="|U| [m/s]")

    c2 = axes[1].tricontourf(tri, pts[:, 4], levels=30, cmap="coolwarm")
    axes[1].set_title(f"{case} pressure")
    axes[1].set_xlabel("x [m]")
    axes[1].set_ylabel("y [m]")
    fig.colorbar(c2, ax=axes[1], label="p [m^2/s^2]")
    fig.tight_layout()
    fig.savefig(OUT_FIG / f"{case}_field.png", dpi=200)
    plt.close(fig)


def plot_cp_cf(summary_rows: list[dict[str, object]]) -> None:
    cp_exp = np.asarray([[float(r["x_over_c"]), float(r["Cp"])] for r in load_csv(EXP_DIR / "noflow_cp.csv")], dtype=float)
    cf_exp = np.asarray([[float(r["x_over_c"]), float(r["Cf"]), float(r["Cf_uncertainty"])] for r in load_csv(EXP_DIR / "noflow_cf.csv")], dtype=float)

    fig, axes = plt.subplots(2, 1, figsize=(10, 9))
    axes[0].scatter(cp_exp[:, 0], cp_exp[:, 1], s=18, color="#d62728", label="NASA Cp")
    axes[1].errorbar(cf_exp[:, 0], cf_exp[:, 1], yerr=cf_exp[:, 2], fmt="o", markersize=3.5, capsize=2.0, color="#d62728", label="NASA Cf")

    for row in summary_rows:
        case = row["case"]
        wall = np.loadtxt(OUT_DATA / f"{case}_wall_series.csv", delimiter=",", skiprows=1)
        axes[0].plot(wall[:, 0], wall[:, 2], linewidth=1.8, label=f"{case} Cp")
        axes[1].plot(wall[:, 0], wall[:, 3], linewidth=1.8, label=f"{case} Cf")

    axes[0].set_ylabel("Cp")
    axes[0].set_xlabel("x/c")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].set_ylabel("Cf")
    axes[1].set_xlabel("x/c")
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_cf_vs_nasa_gpu_pyfr_pass1.png", dpi=200)
    plt.close(fig)


def plot_history(case: str) -> None:
    path = RUNS / case / "pseudo_stats.csv"
    if not path.exists():
        return
    rows = load_csv(path)
    if not rows:
        return
    t = np.array([float(r["t"]) for r in rows], dtype=float)
    rho = np.array([float(r["p"]) if r["p"] != "-" else np.nan for r in rows], dtype=float)
    u = np.array([float(r["u"]) if r["u"] != "-" else np.nan for r in rows], dtype=float)
    v = np.array([float(r["v"]) if r["v"] != "-" else np.nan for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.semilogy(t, rho, label="p residual")
    ax.semilogy(t, u, label="u residual")
    ax.semilogy(t, v, label="v residual")
    ax.set_xlabel("physical time")
    ax.set_ylabel("pseudo residual")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / f"{case}_pseudo_stats.png", dpi=200)
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    summary_rows = []
    for case in ["smoke_test", "medium", "promoted"]:
        case_dir = RUNS / case
        if not case_dir.exists():
            continue
        metrics = {"case": case}
        try:
            metrics |= parse_eval_case(case)
        except Exception as exc:
            metrics["benchmark_mae_error"] = str(exc)
        try:
            metrics |= parse_wall_case(case)
        except Exception as exc:
            metrics["wall_error"] = str(exc)
        plot_field(case)
        plot_history(case)
        summary_rows.append(metrics)

    if summary_rows:
        plot_cp_cf(summary_rows)

    with (OUT_DATA / "gpu_pyfr_pass1_summary.json").open("w") as handle:
        json.dump({"rows": summary_rows}, handle, indent=2)

    with (OUT_DATA / "gpu_pyfr_pass1_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({k for row in summary_rows for k in row.keys()}))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(json.dumps({"rows": summary_rows}, indent=2))


if __name__ == "__main__":
    main()
