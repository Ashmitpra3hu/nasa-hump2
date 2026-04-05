#!/usr/bin/env python3
"""Generate ML PASS 2 figures and comparison tables."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evaluate_nasa_hump_wall_metrics import wall_series


ROOT = Path(__file__).resolve().parents[1]
OUT_DATA = ROOT / "documentation_src" / "data_mlpass2"
OUT_FIG = ROOT / "documentation_src" / "figures_mlpass2"


def ml2_case(tag: str) -> Path:
    return ROOT / "data" / "NASA_2DWMH_mlpass2" / tag


def ml1_case(tag: str) -> Path:
    return ROOT / "data" / "NASA_2DWMH_mlpass1" / tag


def main() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)

    summary = json.loads((OUT_DATA / "mlpass2_summary.json").read_text())
    ml1 = json.loads((ROOT / "documentation_src" / "data_mlpass1" / "mlpass1_comparison_summary.json").read_text())

    baseline = summary["baseline_full"]
    corrected = summary["best_full"]
    ml1_nonzero = summary["mlpass1_best_nonzero"]
    pass4 = summary["pass4_best"]

    baseline_wall = pd.DataFrame(wall_series(ml1_case(baseline["tag"]), str(baseline["end_time"])))
    corrected_wall = pd.DataFrame(wall_series(ml2_case(corrected["tag"]), str(corrected["end_time"])))
    ml1_wall = pd.DataFrame(wall_series(ml1_case(ml1_nonzero["tag"]), str(ml1_nonzero["end_time"])))

    baseline_wall.to_csv(OUT_DATA / "baseline_wall_series.csv", index=False)
    corrected_wall.to_csv(OUT_DATA / "corrected_wall_series.csv", index=False)
    ml1_wall.to_csv(OUT_DATA / "mlpass1_wall_series.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 8.2), sharex=True)

    axes[0].plot(baseline_wall["x_over_c"], baseline_wall["Cp"], label="SST 800", linewidth=2.0)
    axes[0].plot(corrected_wall["x_over_c"], corrected_wall["Cp"], label="ML PASS 2", linewidth=2.0)
    axes[0].plot(ml1_wall["x_over_c"], ml1_wall["Cp"], label="ML PASS 1 nonzero", linewidth=1.6, linestyle="--")
    cp_exp = np.loadtxt(ROOT / "data" / "experimental" / "NASA_hump" / "noflow_cp.csv", delimiter=",", skiprows=1)
    axes[0].scatter(cp_exp[:, 0], cp_exp[:, 1], label="NASA Cp", s=14, color="black", alpha=0.7)
    axes[0].set_ylabel(r"$C_p$")
    axes[0].set_title("Cp comparison against official NASA data")
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False, ncol=2)

    axes[1].plot(baseline_wall["x_over_c"], baseline_wall["Cf"], label="SST 800", linewidth=2.0)
    axes[1].plot(corrected_wall["x_over_c"], corrected_wall["Cf"], label="ML PASS 2", linewidth=2.0)
    axes[1].plot(ml1_wall["x_over_c"], ml1_wall["Cf"], label="ML PASS 1 nonzero", linewidth=1.6, linestyle="--")
    cf_exp = np.loadtxt(ROOT / "data" / "experimental" / "NASA_hump" / "noflow_cf.csv", delimiter=",", skiprows=1)
    axes[1].scatter(cf_exp[:, 0], cf_exp[:, 1], label="NASA Cf", s=14, color="black", alpha=0.7)
    axes[1].axhline(0.0, color="0.4", linewidth=0.9)
    axes[1].set_ylabel(r"$C_f$")
    axes[1].set_xlabel(r"$x/c$")
    axes[1].set_title("Cf comparison against official NASA data")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False, ncol=2)

    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_cf_mlpass2.png", dpi=200)
    plt.close(fig)

    metrics = pd.DataFrame(
        [
            {
                "case": "PASS 4 best",
                "mae": pass4["mae"],
                "cp_mae": pass4["cp_mae"],
                "cf_mae": pass4["cf_mae"],
            },
            {
                "case": "SST 800",
                "mae": baseline["mae"],
                "cp_mae": baseline["cp_mae"],
                "cf_mae": baseline["cf_mae"],
            },
            {
                "case": "ML PASS 1 nonzero",
                "mae": ml1_nonzero["mae"],
                "cp_mae": ml1_nonzero["cp_mae"],
                "cf_mae": ml1_nonzero["cf_mae"],
            },
            {
                "case": "ML PASS 2 best",
                "mae": corrected["mae"],
                "cp_mae": corrected["cp_mae"],
                "cf_mae": corrected["cf_mae"],
            },
        ]
    )
    for column in ["mae", "cp_mae", "cf_mae"]:
        metrics[column] = pd.to_numeric(metrics[column])
    metrics.to_csv(OUT_DATA / "mlpass2_metric_table.csv", index=False)

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    x = range(len(metrics))
    width = 0.25
    ax.bar([i - width for i in x], metrics["mae"], width=width, label="Benchmark MAE")
    ax.bar(x, metrics["cp_mae"], width=width, label="Cp MAE")
    ax.bar([i + width for i in x], metrics["cf_mae"] * 1000.0, width=width, label="Cf MAE x1000")
    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics["case"], rotation=12, ha="right")
    ax.set_title("ML PASS 2 metric comparison")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "mlpass2_metric_comparison.png", dpi=200)
    plt.close(fig)

    rows = pd.DataFrame(summary["rows"])
    rows.to_csv(OUT_DATA / "optimization_history_table.csv", index=False)
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    cheap = rows[rows["stage"] == "cheap"].reset_index(drop=True)
    full = rows[rows["stage"] == "full"].reset_index(drop=True)
    if not cheap.empty:
        ax.plot(range(1, len(cheap) + 1), cheap["objective"], marker="o", label="Cheap stage")
    if not full.empty:
        start = len(cheap)
        ax.plot(range(start + 1, start + len(full) + 1), full["objective"], marker="s", label="Full stage")
    ax.set_xlabel("Evaluation index")
    ax.set_ylabel("Objective J")
    ax.set_title("ML PASS 2 optimization history")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "mlpass2_optimization_history.png", dpi=200)
    plt.close(fig)

    comparison = {
        "baseline": baseline,
        "corrected": corrected,
        "mlpass1_nonzero": ml1_nonzero,
        "pass4_best": pass4,
        "promote_corrected_model": summary["promote_corrected_model"],
        "figure_cp_cf": "documentation_src/figures_mlpass2/cp_cf_mlpass2.png",
        "figure_metrics": "documentation_src/figures_mlpass2/mlpass2_metric_comparison.png",
        "figure_history": "documentation_src/figures_mlpass2/mlpass2_optimization_history.png",
    }
    (OUT_DATA / "mlpass2_comparison_summary.json").write_text(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
