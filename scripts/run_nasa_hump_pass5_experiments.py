#!/usr/bin/env python3
"""Run a focused pass-five NASA hump experiment set."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

from run_nasa_hump_experiment_sweep import (
    copy_from_container,
    copy_template,
    copy_to_container,
    docker_exec,
    local_generate,
    run_case_in_container,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_CASE = ROOT / "data" / "NASA_2DWMH"
SWEEP_ROOT = ROOT / "data" / "NASA_2DWMH_sweep_pass5"
OUT_DIR = ROOT / "documentation_src" / "data_pass5"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd or ROOT, check=True, text=True, capture_output=True)


def copy_full_case(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def configure_existing_case(case_dir: Path, env_overrides: dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(env_overrides)
    env["NASA_HUMP_CASE_DIR"] = str(case_dir.relative_to(ROOT))
    subprocess.run(["python3", "scripts/configure_nasa_hump_case.py"], cwd=ROOT, env=env, check=True, text=True, capture_output=True)
    subprocess.run(["python3", "scripts/write_nasa_hump_inlet_profile.py"], cwd=ROOT, env=env, check=True, text=True, capture_output=True)
    subprocess.run(["python3", "scripts/prepare_nasa_hump_model_fields.py"], cwd=ROOT, env=env, check=True, text=True, capture_output=True)


def run_continuation_in_container(case_dir: Path) -> None:
    remote_case = f"/home/openfoam/{case_dir.relative_to(ROOT)}"
    copy_to_container(case_dir)
    docker_exec(
        "set -euo pipefail; "
        f"simpleFoam -case '{remote_case}' > '{remote_case}/log.run'; "
        f"simpleFoam -case '{remote_case}' -postProcess -latestTime -func wallShearStress > '{remote_case}/log.wallShearStress'; "
        f"postProcess -case '{remote_case}' -latestTime -func 'grad(U)' > '{remote_case}/log.gradU'; "
        f"postProcess -case '{remote_case}' -latestTime -dict system/bottomValues > '{remote_case}/log.bottomValues'"
    )
    copy_from_container(case_dir)


def ensure_checkpoint_wall_shear(case_dir: Path, checkpoints: tuple[str, ...]) -> None:
    missing = [time_name for time_name in checkpoints if not (case_dir / time_name / "wallShearStress").exists()]
    if not missing:
        return
    rel_case = case_dir.relative_to(ROOT)
    cmd = (
        "set -euo pipefail; "
        + " ".join(
            [
                f"simpleFoam -case {rel_case} -postProcess -time {time_name} -func wallShearStress > {rel_case}/log.wallShearStress.{time_name};"
                for time_name in missing
            ]
        )
    )
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/home/openfoam",
            "-w",
            "/home/openfoam",
            "--entrypoint",
            "/bin/bash",
            "opencfd/openfoam-default",
            "-lc",
            cmd,
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def evaluate_checkpoint(case_dir: Path, tag: str, time_name: str) -> dict[str, object]:
    pred_csv = OUT_DIR / f"{tag}_{time_name}_predictions.csv"
    score_json = OUT_DIR / f"{tag}_{time_name}_score.json"
    wall_json = OUT_DIR / f"{tag}_{time_name}_wall.json"

    score = json.loads(
        run(
            [
                "python3",
                "scripts/evaluate_nasa_hump_case.py",
                str(case_dir),
                "--time",
                time_name,
                "--prediction-csv",
                str(pred_csv),
                "--summary-json",
                str(score_json),
            ]
        ).stdout
    )
    wall = json.loads(
        run(
            [
                "python3",
                "scripts/evaluate_nasa_hump_wall_metrics.py",
                str(case_dir),
                "--time",
                time_name,
                "--summary-json",
                str(wall_json),
            ]
        ).stdout
    )

    return {
        "tag": tag,
        "time": time_name,
        "mae": float(score["score"]),
        "cp_mae": float(wall["cp_mae"]),
        "cf_mae": float(wall["cf_mae"]),
        "cp_rmse": float(wall["cp_rmse"]),
        "cf_rmse": float(wall["cf_rmse"]),
    }


def write_summary(rows: list[dict[str, object]], notes: dict[str, str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "pass5_experiment_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tag",
                "time",
                "mae",
                "cp_mae",
                "cf_mae",
                "cp_rmse",
                "cf_rmse",
                "changes",
                "convergence_notes",
                "diagnosis",
            ],
        )
        writer.writeheader()
        for row in rows:
            merged = dict(row)
            merged["changes"] = notes[row["tag"] + ":changes"]
            merged["convergence_notes"] = notes[row["tag"] + ":convergence"]
            merged["diagnosis"] = notes[row["tag"] + ":diagnosis"]
            writer.writerow(merged)

    (OUT_DIR / "pass5_experiment_summary.json").write_text(json.dumps({"rows": rows, "notes": notes}, indent=2))


def main() -> None:
    SWEEP_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    notes: dict[str, str] = {}

    baseline = evaluate_checkpoint(BASE_CASE, "baseline_pass4", "650")
    rows.append(baseline)
    notes["baseline_pass4:changes"] = "Promoted pass-four SST baseline at 650 iterations"
    notes["baseline_pass4:convergence"] = "Reference checkpoint before pass-five continuation and geometry tests."
    notes["baseline_pass4:diagnosis"] = "Front-half suction still weak and Cf recovery still slightly low against the official experiment."

    continuation_case = SWEEP_ROOT / "pass5_continue_sst_1200"
    if not (continuation_case / "1200").exists():
        copy_full_case(BASE_CASE, continuation_case)
        configure_existing_case(
            continuation_case,
            {
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_START_FROM": "latestTime",
                "NASA_HUMP_END_TIME": "1200",
                "NASA_HUMP_WRITE_INTERVAL": "50",
                "NASA_HUMP_SCHEME_MODE": "stable",
            },
        )
        run_continuation_in_container(continuation_case)
    ensure_checkpoint_wall_shear(continuation_case, ("800", "1000", "1200"))
    for checkpoint in ("650", "800", "1000", "1200"):
        rows.append(evaluate_checkpoint(continuation_case, "pass5_continue_sst_1200", checkpoint))
    notes["pass5_continue_sst_1200:changes"] = "Continue the pass-four SST winner from 650 to 1200 iterations without changing physics."
    notes["pass5_continue_sst_1200:convergence"] = "Continuation case preserves the promoted mesh and fields and writes checkpoints every 50 iterations."
    notes["pass5_continue_sst_1200:diagnosis"] = "Primary test of whether the current winner is still under-converged."

    official_grid_env = {
        "NASA_HUMP_MODEL": "kOmegaSST",
        "NASA_HUMP_START_FROM": "startTime",
        "NASA_HUMP_END_TIME": "800",
        "NASA_HUMP_WRITE_INTERVAL": "50",
        "NASA_HUMP_SCHEME_MODE": "stable",
        "NASA_HUMP_X_SPLITS": "-1.35,-0.58,-0.10,0.08,0.22,0.42,0.72,0.84",
        "NASA_HUMP_X_CELLS": "110,120,110,140,160,150,30",
        "NASA_HUMP_X_GRADING": "1.15,0.9,0.8,1.1,1.05,1.0,1.0",
        "NASA_HUMP_Y_CELLS": "240",
        "NASA_HUMP_Y_GRADING": "20",
        "NASA_HUMP_N_SPLINE": "321",
        "NASA_HUMP_TOP_CONTOUR_START": "-0.58",
        "NASA_HUMP_TOP_CONTOUR_END": "0.82",
        "NASA_HUMP_TOP_CONTOUR_DIP": "0.03",
    }

    grid_sst_case = SWEEP_ROOT / "pass5_gridfit_sst_800"
    if not (grid_sst_case / "800").exists():
        copy_template(grid_sst_case)
        local_generate(grid_sst_case, official_grid_env)
        copy_to_container(grid_sst_case)
        run_case_in_container(grid_sst_case)
        copy_from_container(grid_sst_case)
    rows.append(evaluate_checkpoint(grid_sst_case, "pass5_gridfit_sst_800", "800"))
    notes["pass5_gridfit_sst_800:changes"] = "Broaden the top-wall blockage contour and redistribute streamwise blocks to resemble the official no-plenum structured-grid emphasis."
    notes["pass5_gridfit_sst_800:convergence"] = "Fresh run from startTime to 800 iterations on an official-grid-inspired targeted mesh."
    notes["pass5_gridfit_sst_800:diagnosis"] = "Direct geometry-fidelity test aimed at the front-half suction and separation/recovery placement."

    grid_sa_case = SWEEP_ROOT / "pass5_gridfit_sa_800"
    if not (grid_sa_case / "800").exists():
        copy_template(grid_sa_case)
        sa_env = dict(official_grid_env)
        sa_env["NASA_HUMP_MODEL"] = "SpalartAllmaras"
        local_generate(grid_sa_case, sa_env)
        copy_to_container(grid_sa_case)
        run_case_in_container(grid_sa_case)
        copy_from_container(grid_sa_case)
    rows.append(evaluate_checkpoint(grid_sa_case, "pass5_gridfit_sa_800", "800"))
    notes["pass5_gridfit_sa_800:changes"] = "Use the same official-grid-inspired mesh and blockage contour as the SST geometry test, but switch to SpalartAllmaras."
    notes["pass5_gridfit_sa_800:convergence"] = "Fresh run from startTime to 800 iterations; SA-RC was not available in the local OpenFOAM installation."
    notes["pass5_gridfit_sa_800:diagnosis"] = "Separated-shear-layer model screen against the improved-geometry SST baseline."

    write_summary(rows, notes)
    print(json.dumps({"rows": rows, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
