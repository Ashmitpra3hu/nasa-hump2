#!/usr/bin/env python3
"""Run ML PASS 1: a bounded, gradient-free SST correction study."""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from evaluate_nasa_hump_case import evaluate as evaluate_case, latest_numeric_dir
from evaluate_nasa_hump_wall_metrics import evaluate as evaluate_wall


ROOT = Path(__file__).resolve().parents[1]
PASS4_BASE = ROOT / "data" / "NASA_2DWMH_backup_before_promotion"
SWEEP_ROOT = ROOT / "data" / "NASA_2DWMH_mlpass1"
OUT_DIR = ROOT / "documentation_src" / "data_mlpass1"
LOG_CSV = OUT_DIR / "optimization_history.csv"
LOG_JSON = OUT_DIR / "optimization_history.json"
SUMMARY_JSON = OUT_DIR / "mlpass1_summary.json"
SUMMARY_CSV = OUT_DIR / "mlpass1_summary.csv"


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=True)


def shell_quote(path: str) -> str:
    return "'" + path.replace("'", "'\"'\"'") + "'"


def build_model() -> None:
    run(["bash", "scripts/build_ml_hump_model.sh"])


def copy_full_case(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def configure_case(case_dir: Path, model: str, end_time: int, ml_params: dict[str, float] | None = None) -> None:
    env = os.environ.copy()
    env["NASA_HUMP_CASE_DIR"] = str(case_dir.relative_to(ROOT))
    env["NASA_HUMP_MODEL"] = model
    env["NASA_HUMP_START_FROM"] = "latestTime"
    env["NASA_HUMP_END_TIME"] = str(end_time)
    env["NASA_HUMP_WRITE_INTERVAL"] = "10"
    env["NASA_HUMP_SCHEME_MODE"] = "stable"
    if ml_params is not None:
        env["NASA_HUMP_ML_CORRECTION"] = "true"
        env["NASA_HUMP_ML_AMPLITUDE"] = f"{ml_params['amplitude']:.12g}"
        env["NASA_HUMP_ML_CHI0"] = f"{ml_params['chi0']:.12g}"
        env["NASA_HUMP_ML_CHI_WIDTH"] = f"{ml_params['chi_width']:.12g}"
        env["NASA_HUMP_ML_Y_PEAK"] = f"{ml_params['y_peak']:.12g}"
        env["NASA_HUMP_ML_Y_WIDTH"] = f"{ml_params['y_width']:.12g}"
        env["NASA_HUMP_ML_FACTOR_MIN"] = "0.85"
        env["NASA_HUMP_ML_FACTOR_MAX"] = "1.60"
    run(["python3", "scripts/configure_nasa_hump_case.py"], env=env)


def run_case(case_dir: Path, end_time: int) -> tuple[bool, str]:
    rel_case = case_dir.relative_to(ROOT)
    cmd = (
        "export HOME=/home/openfoam; "
        "source /usr/lib/openfoam/openfoam2512/etc/bashrc; "
        f"cd /home/openfoam && simpleFoam -case {shell_quote(str(rel_case))} > {shell_quote(str(rel_case / 'log.run'))}; "
        f"simpleFoam -case {shell_quote(str(rel_case))} -postProcess -time {end_time} -func wallShearStress > {shell_quote(str(rel_case / f'log.wallShearStress.{end_time}'))}; "
        f"postProcess -case {shell_quote(str(rel_case))} -time {end_time} -func 'grad(U)' > {shell_quote(str(rel_case / f'log.gradU.{end_time}'))}; "
        f"postProcess -case {shell_quote(str(rel_case))} -time {end_time} -dict system/bottomValues > {shell_quote(str(rel_case / f'log.bottomValues.{end_time}'))}"
    )
    proc = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/home/openfoam",
            "--entrypoint",
            "/bin/bash",
            "opencfd/openfoam-default",
            "-lc",
            cmd,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0, proc.stderr + proc.stdout


def bounded_params(raw: np.ndarray) -> dict[str, float]:
    amplitude = float(np.clip(raw[0], 0.0, 0.80))
    chi0 = float(np.exp(np.clip(raw[1], math.log(1.5), math.log(20.0))))
    y_peak = float(np.clip(raw[2], 0.005, 0.035))
    return {
        "amplitude": amplitude,
        "chi0": chi0,
        "chi_width": 1.0,
        "y_peak": y_peak,
        "y_width": 0.010,
    }


def regularization(params: dict[str, float]) -> float:
    amp_term = 0.02 * (params["amplitude"] / 0.6) ** 2
    return float(amp_term)


def objective_from_metrics(mae: float, cp_mae: float, cf_mae: float, penalty: float) -> float:
    return float(0.55 * mae + 0.30 * cp_mae + 0.15 * (cf_mae / 1.0e-3) + penalty)


def record_history(rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tag",
                "stage",
                "end_time",
                "stable",
                "objective",
                "mae",
                "cp_mae",
                "cf_mae",
                "penalty",
                "runtime_minutes",
                "amplitude",
                "chi0",
                "chi_width",
                "y_peak",
                "y_width",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    LOG_JSON.write_text(json.dumps({"rows": rows}, indent=2))


def evaluate_candidate(tag: str, raw_params: np.ndarray, end_time: int, stage: str, history: list[dict[str, object]]) -> dict[str, object]:
    params = bounded_params(raw_params)
    case_dir = SWEEP_ROOT / tag
    copy_full_case(PASS4_BASE, case_dir)
    configure_case(case_dir, "kOmegaSSTML", end_time, params)

    start = time.time()
    stable, log_text = run_case(case_dir, end_time)
    runtime_minutes = (time.time() - start) / 60.0

    row: dict[str, object] = {
        "tag": tag,
        "stage": stage,
        "end_time": end_time,
        "stable": stable,
        "objective": None,
        "mae": None,
        "cp_mae": None,
        "cf_mae": None,
        "penalty": None,
        "runtime_minutes": runtime_minutes,
        "amplitude": params["amplitude"],
        "chi0": params["chi0"],
        "chi_width": params["chi_width"],
        "y_peak": params["y_peak"],
        "y_width": params["y_width"],
        "notes": "stable" if stable else "solver failure",
    }

    if stable:
        time_name = latest_numeric_dir(case_dir).name
        mae_result = evaluate_case(case_dir, time_name)
        wall_result = evaluate_wall(case_dir, time_name)
        penalty = regularization(params)
        objective = objective_from_metrics(float(mae_result["score"]), float(wall_result["cp_mae"]), float(wall_result["cf_mae"]), penalty)
        row.update(
            {
                "end_time": int(float(time_name)),
                "objective": objective,
                "mae": float(mae_result["score"]),
                "cp_mae": float(wall_result["cp_mae"]),
                "cf_mae": float(wall_result["cf_mae"]),
                "penalty": penalty,
            }
        )
    else:
        row.update(
            {
                "objective": 10.0,
                "mae": 10.0,
                "cp_mae": 10.0,
                "cf_mae": 10.0,
                "penalty": 1.0,
                "notes": log_text[-1200:],
            }
        )

    history.append(row)
    record_history(history)
    return row


def evaluate_baseline(tag: str, model: str, end_time: int, history: list[dict[str, object]]) -> dict[str, object]:
    case_dir = SWEEP_ROOT / tag
    copy_full_case(PASS4_BASE, case_dir)
    configure_case(case_dir, model, end_time, None)
    start = time.time()
    stable, log_text = run_case(case_dir, end_time)
    runtime_minutes = (time.time() - start) / 60.0
    row: dict[str, object] = {
        "tag": tag,
        "stage": "baseline",
        "end_time": end_time,
        "stable": stable,
        "objective": None,
        "mae": None,
        "cp_mae": None,
        "cf_mae": None,
        "penalty": 0.0,
        "runtime_minutes": runtime_minutes,
        "amplitude": 0.0,
        "chi0": None,
        "chi_width": None,
        "y_peak": None,
        "y_width": None,
        "notes": "baseline continuation" if stable else log_text[-1200:],
    }
    if stable:
        time_name = latest_numeric_dir(case_dir).name
        mae_result = evaluate_case(case_dir, time_name)
        wall_result = evaluate_wall(case_dir, time_name)
        row.update(
            {
                "end_time": int(float(time_name)),
                "objective": objective_from_metrics(float(mae_result["score"]), float(wall_result["cp_mae"]), float(wall_result["cf_mae"]), 0.0),
                "mae": float(mae_result["score"]),
                "cp_mae": float(wall_result["cp_mae"]),
                "cf_mae": float(wall_result["cf_mae"]),
            }
        )
    else:
        row.update({"objective": 10.0, "mae": 10.0, "cp_mae": 10.0, "cf_mae": 10.0})
    history.append(row)
    record_history(history)
    return row


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SWEEP_ROOT.mkdir(parents=True, exist_ok=True)
    build_model()

    history: list[dict[str, object]] = []
    cheap_end_time = 720
    full_end_time = 800
    baseline_cheap = evaluate_baseline(f"mlpass1_baseline_sst_{cheap_end_time}", "kOmegaSST", cheap_end_time, history)
    baseline_full = evaluate_baseline(f"mlpass1_baseline_sst_{full_end_time}", "kOmegaSST", full_end_time, history)

    x0 = np.array([0.25, math.log(4.0), 0.015], dtype=float)
    initial_simplex = np.array(
        [
            x0,
            np.array([0.10, math.log(3.0), 0.012], dtype=float),
            np.array([0.35, math.log(6.0), 0.015], dtype=float),
            np.array([0.25, math.log(8.0), 0.020], dtype=float),
        ]
    )

    cache: dict[tuple[float, float, float, float], dict[str, object]] = {}
    eval_counter = 0

    def objective(raw: np.ndarray) -> float:
        nonlocal eval_counter
        key = tuple(np.round(raw, 6).tolist())
        if key not in cache:
            eval_counter += 1
            result = evaluate_candidate(f"mlpass1_opt_{eval_counter:03d}", raw, cheap_end_time, "cheap", history)
            cache[key] = result
        return float(cache[key]["objective"])

    result = minimize(
        objective,
        x0,
        method="Nelder-Mead",
        options={
            "maxiter": 2,
            "maxfev": 6,
            "xatol": 0.01,
            "fatol": 5.0e-4,
            "initial_simplex": initial_simplex,
            "disp": True,
        },
    )

    cheap_rows = [row for row in history if row["stage"] == "cheap" and row["stable"]]
    cheap_rows.sort(key=lambda row: float(row["objective"]))
    shortlisted = cheap_rows[:2]

    full_rows: list[dict[str, object]] = []
    for idx, row in enumerate(shortlisted, start=1):
        raw = np.array(
            [
                float(row["amplitude"]),
                math.log(float(row["chi0"])),
                float(row["y_peak"]),
            ],
            dtype=float,
        )
        full_rows.append(evaluate_candidate(f"mlpass1_full_{idx:02d}", raw, full_end_time, "full", history))

    promoted = min(full_rows + [baseline_full], key=lambda row: float(row["objective"]))
    summary = {
        "objective_definition": {
            "formula": "J = 0.55*benchmark_MAE + 0.30*Cp_MAE + 0.15*(Cf_MAE/1e-3) + penalty",
            "penalty": "0.02*(amplitude/0.6)^2",
        },
        "optimizer": {
            "name": "Nelder-Mead",
            "stage1_end_time": cheap_end_time,
            "stage2_end_time": full_end_time,
            "scipy_success": bool(result.success),
            "message": result.message,
            "nfev": int(result.nfev),
        },
        "baseline_cheap": baseline_cheap,
        "baseline_full": baseline_full,
        "best_full_or_baseline": promoted,
        "promote_corrected_model": promoted["tag"] != baseline_full["tag"],
        "rows": history,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))

    with SUMMARY_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
