#!/usr/bin/env python3
"""Run a focused pass-four experiment loop scored by MAE and official Cp/Cf agreement."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from run_nasa_hump_experiment_sweep import (
    BASE_CASE,
    SWEEP_ROOT,
    copy_from_container,
    copy_template,
    copy_to_container,
    evaluate_case,
    local_generate,
    run_case_in_container,
)
from evaluate_nasa_hump_wall_metrics import evaluate as evaluate_wall


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "documentation_src" / "data_pass4"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    baseline_mae = json.loads((ROOT / "documentation_src" / "data_second_pass" / "reconstructed_nasa_score_second_pass.json").read_text())["score"]
    baseline_wall = evaluate_wall(BASE_CASE)

    experiments = [
        {
            "tag": "pass4_uniform_sst_650",
            "changes": "Keep the current best pass-three SST setup but extend the run to 650 iterations",
            "env": {
                "NASA_HUMP_INLET_MODE": "uniform",
                "NASA_HUMP_END_TIME": "650",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "stable",
            },
        },
        {
            "tag": "pass4_tbl35_sst_500",
            "changes": "Use a 35 mm analytic turbulent-boundary-layer inlet to match the NASA description more closely",
            "env": {
                "NASA_HUMP_INLET_MODE": "tbl",
                "NASA_HUMP_INLET_DELTA": "0.035",
                "NASA_HUMP_INLET_TI_EDGE": "0.004",
                "NASA_HUMP_INLET_TI_PEAK": "0.060",
                "NASA_HUMP_END_TIME": "500",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "stable",
            },
        },
    ]

    rows: list[dict[str, object]] = [
        {
            "tag": "baseline_pass3",
            "changes": "Current best pass-three baseline",
            "mae": float(baseline_mae),
            **baseline_wall,
        }
    ]

    for experiment in experiments:
        case_dir = SWEEP_ROOT / experiment["tag"]
        copy_template(case_dir)
        local_generate(case_dir, experiment["env"])
        copy_to_container(case_dir)
        run_case_in_container(case_dir)
        copy_from_container(case_dir)

        mae_result = evaluate_case(case_dir, experiment["tag"])
        wall_result = evaluate_wall(case_dir)
        row = {
            "tag": experiment["tag"],
            "changes": experiment["changes"],
            "mae": float(mae_result["score"]),
            **wall_result,
        }
        rows.append(row)

    csv_path = OUT_DIR / "pass4_experiment_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["tag", "changes", "mae", "cp_rmse", "cp_mae", "cf_rmse", "cf_mae"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {"rows": rows}
    (OUT_DIR / "pass4_experiment_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
