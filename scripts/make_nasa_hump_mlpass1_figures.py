#!/usr/bin/env python3
"""Generate ML PASS 1 comparison figures."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from evaluate_nasa_hump_wall_metrics import wall_series


ROOT = Path(__file__).resolve().parents[1]
OUT_DATA = ROOT / "documentation_src" / "data_mlpass1"
OUT_FIG = ROOT / "documentation_src" / "figures_mlpass1"
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"


def load_csv(path: Path, cols: int) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open() as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            rows.append([float(value) for value in row[:cols]])
    return np.asarray(rows, dtype=float)


def case_dir_from_tag(tag: str) -> Path:
    return ROOT / "data" / "NASA_2DWMH_mlpass1" / tag


def write_series_csv(path: Path, wall: dict[str, np.ndarray], name_cp: str, name_cf: str) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x_over_c", name_cp, name_cf])
        for x, cp, cf in zip(wall["x_over_c"], wall["Cp"], wall["Cf"]):
            writer.writerow([x, cp, cf])


def main() -> None:
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    summary = json.loads((OUT_DATA / "mlpass1_summary.json").read_text())

    baseline = summary["baseline_full"]
    corrected_candidates = [
        row for row in summary["rows"]
        if row["stage"] == "full" and row["stable"] and float(row["amplitude"]) > 1.0e-8
    ]
    corrected = min(corrected_candidates, key=lambda row: float(row["objective"])) if corrected_candidates else None

    cp_exp = load_csv(EXP_DIR / "noflow_cp.csv", 2)
    cf_exp = load_csv(EXP_DIR / "noflow_cf.csv", 3)
    baseline_wall = wall_series(case_dir_from_tag(str(baseline["tag"])), str(baseline["end_time"]))
    corrected_wall = wall_series(case_dir_from_tag(str(corrected["tag"])), str(corrected["end_time"])) if corrected else baseline_wall

    write_series_csv(OUT_DATA / "baseline_wall_series.csv", baseline_wall, "Cp_baseline", "Cf_baseline")
    write_series_csv(OUT_DATA / "corrected_wall_series.csv", corrected_wall, "Cp_corrected", "Cf_corrected")

    fig, axes = plt.subplots(2, 1, figsize=(10, 9))
    axes[0].plot(baseline_wall["x_over_c"], baseline_wall["Cp"], label="Baseline SST", linewidth=2.0, color="#1f77b4")
    axes[0].plot(corrected_wall["x_over_c"], corrected_wall["Cp"], label="Corrected SST", linewidth=2.0, color="#ff7f0e")
    axes[0].scatter(cp_exp[:, 0], cp_exp[:, 1], label="NASA experiment", color="#d62728", s=18)
    axes[0].set_ylabel("Cp")
    axes[0].set_title("ML PASS 1 Cp comparison")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(baseline_wall["x_over_c"], baseline_wall["Cf"], label="Baseline SST", linewidth=2.0, color="#1f77b4")
    axes[1].plot(corrected_wall["x_over_c"], corrected_wall["Cf"], label="Corrected SST", linewidth=2.0, color="#ff7f0e")
    axes[1].errorbar(cf_exp[:, 0], cf_exp[:, 1], yerr=cf_exp[:, 2], fmt="o", label="NASA experiment", color="#d62728", markersize=3.5, capsize=2.0)
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.6)
    axes[1].set_xlabel("x/c")
    axes[1].set_ylabel("Cf")
    axes[1].set_title("ML PASS 1 Cf comparison")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_cf_mlpass1.png", dpi=200)
    plt.close(fig)

    labels = ["PASS4 baseline", "Baseline SST@1000", "Best corrected@1000"]
    mae_values = [
        0.1659136747,
        float(baseline["mae"]),
        float(corrected["mae"]) if corrected else float(baseline["mae"]),
    ]
    cp_values = [
        0.1711800326,
        float(baseline["cp_mae"]),
        float(corrected["cp_mae"]) if corrected else float(baseline["cp_mae"]),
    ]
    cf_values = [
        0.0008476129,
        float(baseline["cf_mae"]),
        float(corrected["cf_mae"]) if corrected else float(baseline["cf_mae"]),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    axes[0].bar(labels, mae_values, color="#1f77b4")
    axes[0].set_ylabel("Benchmark MAE")
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[1].bar(labels, cp_values, color="#ff7f0e")
    axes[1].set_ylabel("Cp MAE")
    axes[1].grid(True, axis="y", alpha=0.3)
    axes[2].bar(labels, cf_values, color="#2ca02c")
    axes[2].set_ylabel("Cf MAE")
    axes[2].grid(True, axis="y", alpha=0.3)
    axes[2].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "mlpass1_metric_comparison.png", dpi=200)
    plt.close(fig)

    comparison = {
        "baseline": baseline,
        "corrected": corrected,
        "promote_corrected_model": bool(corrected and float(corrected["objective"]) < float(baseline["objective"])),
        "figure_cp_cf": "documentation_src/figures_mlpass1/cp_cf_mlpass1.png",
        "figure_metrics": "documentation_src/figures_mlpass1/mlpass1_metric_comparison.png",
    }
    (OUT_DATA / "mlpass1_comparison_summary.json").write_text(json.dumps(comparison, indent=2))
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
