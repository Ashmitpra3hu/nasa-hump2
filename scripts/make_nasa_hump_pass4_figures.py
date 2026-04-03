#!/usr/bin/env python3
"""Generate pass-four NASA hump figures with official experimental Cp/Cf comparisons."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from make_nasa_hump_second_pass_figures import (
    build_wall_series,
    ensure_dirs as ensure_pass2_dirs,
    get_solution_fields,
    latest_numeric_dir,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "data" / "NASA_2DWMH"
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"
OUT_DATA = ROOT / "documentation_src" / "data_pass4"
OUT_FIG = ROOT / "documentation_src" / "figures_pass4"
PASS2_FIG = ROOT / "documentation_src" / "figures_second_pass"
PASS2_DATA = ROOT / "documentation_src" / "data_second_pass"


def ensure_dirs() -> None:
    ensure_pass2_dirs()
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path, expected_cols: int) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open() as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(header) < expected_cols:
            raise ValueError(f"{path} expected at least {expected_cols} columns")
        for row in reader:
            rows.append([float(value) for value in row[:expected_cols]])
    return np.asarray(rows, dtype=float)


def write_csv(path: Path, header: list[str], rows: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows.tolist())


def nearest_sample(x_query: np.ndarray, x_data: np.ndarray, values: np.ndarray) -> np.ndarray:
    indices = np.abs(x_data[:, None] - x_query[None, :]).argmin(axis=0)
    return values[indices]


def make_cp_cf_comparison(wall: dict[str, np.ndarray | float | None]) -> dict[str, float]:
    cp_exp = load_csv(EXP_DIR / "noflow_cp.csv", 2)
    cf_exp = load_csv(EXP_DIR / "noflow_cf.csv", 3)

    x_over_c = np.asarray(wall["x_over_c"], dtype=float)
    cp_cfd = np.asarray(wall["cp"], dtype=float)
    cf_cfd = np.asarray(wall["cf"], dtype=float)

    # Use the nearest resolved wall-sample location for the comparison so the
    # pass-four pipeline does not rely on interpolating either the published
    # experiment tables or the CFD wall series.
    cp_pred = nearest_sample(cp_exp[:, 0], x_over_c, cp_cfd)
    cf_pred = nearest_sample(cf_exp[:, 0], x_over_c, cf_cfd)

    cp_rows = np.column_stack((cp_exp[:, 0], cp_exp[:, 1], cp_pred, cp_pred - cp_exp[:, 1]))
    cf_rows = np.column_stack((cf_exp[:, 0], cf_exp[:, 1], cf_exp[:, 2], cf_pred, cf_pred - cf_exp[:, 1]))

    write_csv(
        OUT_DATA / "cp_comparison_pass4.csv",
        ["x_over_c", "Cp_exp", "Cp_cfd", "Cp_error"],
        cp_rows,
    )
    write_csv(
        OUT_DATA / "cf_comparison_pass4.csv",
        ["x_over_c", "Cf_exp", "Cf_uncertainty", "Cf_cfd", "Cf_error"],
        cf_rows,
    )

    cp_rmse = float(np.sqrt(np.mean((cp_rows[:, 3]) ** 2)))
    cf_rmse = float(np.sqrt(np.mean((cf_rows[:, 4]) ** 2)))
    cp_mae = float(np.mean(np.abs(cp_rows[:, 3])))
    cf_mae = float(np.mean(np.abs(cf_rows[:, 4])))

    fig, axes = plt.subplots(2, 1, figsize=(10, 9), sharex=False)

    axes[0].plot(x_over_c, cp_cfd, color="#1f77b4", linewidth=2.0, label="OpenFOAM")
    axes[0].scatter(cp_exp[:, 0], cp_exp[:, 1], color="#d62728", s=20, label="NASA experiment")
    axes[0].set_ylabel("Cp")
    axes[0].set_title(f"Cp comparison, RMSE={cp_rmse:.4f}, MAE={cp_mae:.4f}")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(x_over_c, cf_cfd, color="#1f77b4", linewidth=2.0, label="OpenFOAM")
    axes[1].errorbar(
        cf_exp[:, 0],
        cf_exp[:, 1],
        yerr=cf_exp[:, 2],
        fmt="o",
        color="#d62728",
        markersize=3.5,
        capsize=2.0,
        label="NASA experiment",
    )
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    axes[1].set_xlabel("x/c")
    axes[1].set_ylabel("Cf")
    axes[1].set_title(f"Cf comparison, RMSE={cf_rmse:.5f}, MAE={cf_mae:.5f}")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_cf_vs_nasa_pass4.png", dpi=200)
    plt.close(fig)

    return {
        "cp_rmse": cp_rmse,
        "cp_mae": cp_mae,
        "cf_rmse": cf_rmse,
        "cf_mae": cf_mae,
    }


def copy_paraview_images() -> None:
    for path in PASS2_FIG.glob("paraview_*.png"):
        shutil.copy2(path, OUT_FIG / path.name)


def copy_reference_outputs() -> None:
    for path in PASS2_DATA.glob("*"):
        if path.is_file():
            shutil.copy2(path, OUT_DATA / path.name)
    for path in PASS2_FIG.glob("*"):
        if path.is_file() and not path.name.startswith("paraview_"):
            shutil.copy2(path, OUT_FIG / path.name)


def main() -> None:
    ensure_dirs()
    fields = get_solution_fields()
    wall = build_wall_series(fields)
    copy_reference_outputs()
    copy_paraview_images()

    wall_metrics = make_cp_cf_comparison(wall)

    summary = {
        "latest_time_directory": latest_numeric_dir(CASE_DIR).name,
        "score_file": "documentation_src/data_second_pass/reconstructed_nasa_score_second_pass.json",
        "official_experiment_files": {
            "cp": "data/experimental/NASA_hump/noflow_cp.csv",
            "cf": "data/experimental/NASA_hump/noflow_cf.csv",
        },
        "comparison_metrics": wall_metrics,
        "figure_file": "documentation_src/figures_pass4/cp_cf_vs_nasa_pass4.png",
    }
    (OUT_DATA / "pass4_comparison_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
