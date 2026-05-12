#!/usr/bin/env python3
"""Generate honest PASS 1 summaries for the GPU PyFR hump workflow."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "gpu_pyfr_pass1"
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"
SAMPLE_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "sampling"
OUT_DATA = ROOT / "documentation_src" / "data_gpu_pyfr_pass1"
OUT_FIG = ROOT / "documentation_src" / "figures_gpu_pyfr_pass1"
PASS4_SUMMARY = ROOT / "documentation_src" / "data_pass4" / "pass4_comparison_summary.json"
PASS5_SUMMARY = ROOT / "documentation_src" / "data_pass5" / "pass5_comparison_summary.json"
MLPASS1_SUMMARY = ROOT / "documentation_src" / "data_mlpass1" / "mlpass1_summary.json"
PASS5_CP = ROOT / "documentation_src" / "data_pass5" / "cp_comparison_pass5.csv"
PASS5_CF = ROOT / "documentation_src" / "data_pass5" / "cf_comparison_pass5.csv"

CHORD = 0.42
X_MIN = -1.35
X_MAX = 0.84
TOP_Z = 0.35
TOP_CONTOUR_START = -0.25
TOP_CONTOUR_END = 0.65
TOP_CONTOUR_DIP = 0.02


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return 0.053 * math.sin(math.pi * xi) ** 2


def top_height(x: float) -> float:
    if x <= TOP_CONTOUR_START or x >= TOP_CONTOUR_END:
        return TOP_Z
    xi = (x - TOP_CONTOUR_START) / (TOP_CONTOUR_END - TOP_CONTOUR_START)
    return TOP_Z - TOP_CONTOUR_DIP * math.sin(math.pi * xi) ** 2


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def load_float_csv(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open() as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            rows.append([float(v) for v in row])
    return np.asarray(rows, dtype=float)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def summarize_openfoam_baselines() -> list[dict[str, object]]:
    pass4 = load_json(PASS4_SUMMARY)
    pass5 = load_json(PASS5_SUMMARY)
    mlpass1 = load_json(MLPASS1_SUMMARY)
    baseline_800 = mlpass1["baseline_full"]

    return [
        {
            "case": "openfoam_pass4_best",
            "display_case": "OF PASS4",
            "method": "OpenFOAM SST",
            "job_id": "-",
            "status": "completed",
            "mesh_variant": "PASS 4 promoted",
            "gpu_model": "-",
            "benchmark_mae": 0.16591367469306545,
            "cp_mae": float(pass4["comparison_metrics"]["cp_mae"]),
            "cf_mae": float(pass4["comparison_metrics"]["cf_mae"]),
            "notes": "Best PASS 4 continuation to 650 iterations.",
        },
        {
            "case": "openfoam_sst_800",
            "display_case": "OF SST800",
            "method": "OpenFOAM SST",
            "job_id": "-",
            "status": "completed",
            "mesh_variant": "PASS 5 continuation",
            "gpu_model": "-",
            "benchmark_mae": float(baseline_800["mae"]),
            "cp_mae": float(baseline_800["cp_mae"]),
            "cf_mae": float(baseline_800["cf_mae"]),
            "notes": "Strongest existing plain-SST baseline entering PyFR PASS 1.",
        },
        {
            "case": "openfoam_pass5_1200",
            "display_case": "OF PASS5",
            "method": "OpenFOAM SST",
            "job_id": "-",
            "status": "completed",
            "mesh_variant": "PASS 5 promoted",
            "gpu_model": "-",
            "benchmark_mae": 0.13589016762007924,
            "cp_mae": float(pass5["comparison_metrics"]["cp_mae"]),
            "cf_mae": float(pass5["comparison_metrics"]["cf_mae"]),
            "notes": "Best local OpenFOAM benchmark after later continuation to 1200 iterations.",
        },
    ]


def summarize_pyfr_runs() -> list[dict[str, object]]:
    return [
        {
            "case": "pyfr_smoke_10696809",
            "display_case": "PyFR smoke",
            "method": "PyFR ac-navier-stokes",
            "job_id": "10696809",
            "status": "completed",
            "mesh_variant": "rectangular smoke mesh",
            "gpu_model": "A100-40GB",
            "benchmark_mae": None,
            "cp_mae": None,
            "cf_mae": None,
            "notes": "CUDA backend smoke test completed through Slurm; no NASA hump metrics expected.",
        },
        {
            "case": "pyfr_medium_quad_10696811",
            "display_case": "PyFR curved",
            "method": "PyFR ac-navier-stokes",
            "job_id": "10696811",
            "status": "failed",
            "mesh_variant": "curved structured hump mesh",
            "gpu_model": "A100-40GB",
            "benchmark_mae": None,
            "cp_mae": None,
            "cf_mae": None,
            "notes": "Failed during interface face-point sorting inside PyFR element/intersection setup.",
        },
        {
            "case": "pyfr_medium_tri_10696812",
            "display_case": "PyFR tri",
            "method": "PyFR ac-navier-stokes",
            "job_id": "10696812",
            "status": "failed",
            "mesh_variant": "structured triangular hump mesh",
            "gpu_model": "A100-40GB",
            "benchmark_mae": None,
            "cp_mae": None,
            "cf_mae": None,
            "notes": "Structured triangle variant still failed in interface ordering before marching.",
        },
        {
            "case": "pyfr_medium_lineartri_10696817",
            "display_case": "PyFR linear tri",
            "method": "PyFR ac-navier-stokes",
            "job_id": "10696817",
            "status": "failed",
            "mesh_variant": "piecewise-linear triangular hump mesh",
            "gpu_model": "A100-40GB",
            "benchmark_mae": None,
            "cp_mae": None,
            "cf_mae": None,
            "notes": "Solver advanced beyond import/setup, but sampler plugin failed before evaluation and wall CSV export.",
        },
    ]


def write_summary_files(rows: list[dict[str, object]]) -> None:
    with (OUT_DATA / "gpu_pyfr_pass1_summary.json").open("w") as handle:
        json.dump({"rows": rows}, handle, indent=2)

    fieldnames = [
        "case",
        "display_case",
        "method",
        "job_id",
        "status",
        "mesh_variant",
        "gpu_model",
        "benchmark_mae",
        "cp_mae",
        "cf_mae",
        "notes",
    ]
    with (OUT_DATA / "gpu_pyfr_pass1_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "\\begin{tabular}{p{1.8cm} p{1.25cm} p{1.45cm} p{1.35cm} p{1.35cm} p{6.0cm}}",
        "\\toprule",
        "Case & Status & Benchmark MAE & Cp MAE & Cf MAE & Notes\\\\",
        "\\midrule",
    ]
    for row in rows:
        def fmt(val: object) -> str:
            if val is None:
                return "--"
            if isinstance(val, (float, int)):
                return f"{float(val):.6f}"
            return str(val)

        lines.append(
            f"{str(row.get('display_case', row['case'])).replace('_', '\\_')} & "
            f"{row['status']} & "
            f"{fmt(row.get('benchmark_mae'))} & "
            f"{fmt(row.get('cp_mae'))} & "
            f"{fmt(row.get('cf_mae'))} & "
            f"{str(row['notes']).replace('_', '\\_')}\\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    (OUT_DATA / "summary_table.tex").write_text("\n".join(lines))


def plot_geometry_and_sampling() -> None:
    xs = np.linspace(X_MIN, X_MAX, 500)
    bottom = np.array([hump_height(x) for x in xs])
    top = np.array([top_height(x) for x in xs])
    wall_rows = load_csv(SAMPLE_DIR / "wall_points.csv")
    field_rows = load_csv(SAMPLE_DIR / "field_points.csv")

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(xs / CHORD, bottom / CHORD, color="#2f4b7c", linewidth=2.2, label="reconstructed hump wall")
    ax.plot(xs / CHORD, top / CHORD, color="#bc5090", linewidth=2.0, label="contoured upper wall")

    wall_x = np.array([float(r["x_probe1_m"]) / CHORD for r in wall_rows], dtype=float)
    wall_y = np.array([float(r["y_probe1_m"]) / CHORD for r in wall_rows], dtype=float)
    ax.scatter(wall_x, wall_y, s=10, color="#ff7c43", alpha=0.8, label="wall probe points")

    field_x = np.array([float(r["x_m"]) / CHORD for r in field_rows[::40]], dtype=float)
    field_y = np.array([float(r["y_m"]) / CHORD for r in field_rows[::40]], dtype=float)
    ax.scatter(field_x, field_y, s=5, color="#7a5195", alpha=0.35, label="field sample subset")

    ax.set_xlabel("x/c")
    ax.set_ylabel("y/c")
    ax.set_title("PyFR PASS 1 geometry reconstruction and sampling layout")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pyfr_geometry_sampling.png", dpi=220)
    plt.close(fig)


def plot_attempt_status(rows: list[dict[str, object]]) -> None:
    pyfr_rows = [r for r in rows if str(r["method"]).startswith("PyFR")]
    labels = [f"{r['job_id']} {r['case'].replace('pyfr_', '')}" for r in pyfr_rows]
    ypos = np.arange(len(pyfr_rows))
    color_map = {"completed": "#2ca02c", "failed": "#d62728"}
    colors = [color_map.get(str(r["status"]), "#7f7f7f") for r in pyfr_rows]

    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.barh(ypos, np.ones(len(pyfr_rows)), color=colors, alpha=0.85)
    for y, row in zip(ypos, pyfr_rows):
        ax.text(
            0.02,
            y,
            row["notes"],
            va="center",
            ha="left",
            fontsize=8.5,
            color="white" if row["status"] == "failed" else "black",
        )
    ax.set_yticks(ypos, labels)
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_title("PyFR PASS 1 Slurm run outcomes on Gilbreth")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pyfr_attempt_status.png", dpi=220)
    plt.close(fig)


def plot_cp_cf_reference() -> None:
    cp_exp = load_float_csv(EXP_DIR / "noflow_cp.csv")
    cf_exp = load_float_csv(EXP_DIR / "noflow_cf.csv")
    cp_of = load_float_csv(PASS5_CP)
    cf_of = load_float_csv(PASS5_CF)

    fig, axes = plt.subplots(2, 1, figsize=(10, 9))
    axes[0].scatter(cp_exp[:, 0], cp_exp[:, 1], s=14, color="#d62728", label="NASA experimental Cp")
    axes[0].plot(cp_of[:, 0], cp_of[:, 2], color="#1f77b4", linewidth=2.0, label="OpenFOAM SST 1200 baseline")
    axes[0].set_ylabel("Cp")
    axes[0].set_xlabel("x/c")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="best")
    axes[0].text(
        0.02,
        0.05,
        "PyFR PASS 1 wall Cp series unavailable:\nmedium hump job 10696817 failed in sampler refinement\nbefore wall/evaluation CSV export.",
        transform=axes[0].transAxes,
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )

    axes[1].errorbar(
        cf_exp[:, 0],
        cf_exp[:, 1],
        yerr=cf_exp[:, 2],
        fmt="o",
        markersize=3.0,
        capsize=2.0,
        color="#d62728",
        label="NASA experimental Cf",
    )
    axes[1].plot(cf_of[:, 0], cf_of[:, 3], color="#1f77b4", linewidth=2.0, label="OpenFOAM SST 1200 baseline")
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_ylabel("Cf")
    axes[1].set_xlabel("x/c")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="best")
    axes[1].text(
        0.02,
        0.08,
        "No PyFR wall-friction distribution was generated in PASS 1,\nso the figure preserves the official data and the\nexisting OpenFOAM baseline for honest comparison.",
        transform=axes[1].transAxes,
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )

    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_cf_vs_nasa_gpu_pyfr_pass1.png", dpi=220)
    plt.close(fig)


def plot_smoke_force() -> None:
    path = RUNS / "smoke_test" / "fluidforce_bottomWall.csv"
    rows = load_csv(path)
    finite = [
        (
            float(r["t"]),
            float(r["px"]),
            float(r["py"]),
        )
        for r in rows
        if r["px"].lower() != "nan" and r["py"].lower() != "nan"
    ]

    fig, ax = plt.subplots(figsize=(10, 4))
    if finite:
        arr = np.asarray(finite, dtype=float)
        ax.plot(arr[:, 0], arr[:, 1], marker="o", label="px")
        ax.plot(arr[:, 0], arr[:, 2], marker="s", label="py")
        ax.legend()
    else:
        ax.text(
            0.5,
            0.5,
            "Smoke-test force plugin produced only startup/NaN rows.\nThis is enough to confirm plugin execution,\nbut not enough for a meaningful aerodynamic history plot.",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=10,
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
        )
    ax.set_xlabel("physical time")
    ax.set_ylabel("integrated wall force")
    ax.set_title("PyFR smoke-test force output")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "smoke_force_history.png", dpi=220)
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    rows = summarize_openfoam_baselines() + summarize_pyfr_runs()
    write_summary_files(rows)
    plot_geometry_and_sampling()
    plot_attempt_status(rows)
    plot_cp_cf_reference()
    plot_smoke_force()
    print(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
