#!/usr/bin/env python3
"""Run ML PASS 2: separation-aware SST production correction."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from evaluate_nasa_hump_case import evaluate as evaluate_case, latest_numeric_dir
from evaluate_nasa_hump_wall_metrics import evaluate as evaluate_wall


ROOT = Path(__file__).resolve().parents[1]
PASS4_BASE = ROOT / "data" / "NASA_2DWMH_backup_before_promotion"
SWEEP_ROOT = ROOT / "data" / "NASA_2DWMH_mlpass2"
OUT_DIR = ROOT / "documentation_src" / "data_mlpass2"
LOG_CSV = OUT_DIR / "optimization_history.csv"
LOG_JSON = OUT_DIR / "optimization_history.json"
SUMMARY_JSON = OUT_DIR / "mlpass2_summary.json"
SUMMARY_CSV = OUT_DIR / "mlpass2_summary.csv"


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=True)


def shell_quote(path: str) -> str:
    return "'" + path.replace("'", "'\"'\"'") + "'"


def build_model() -> None:
    run(["bash", "scripts/build_ml_hump_model.sh"])


def copy_full_case(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    keep_names = {
        "0",
        "650",
        "constant",
        "system",
        "caseDef",
        "fieldDef",
        "clean.sh",
        "run.sh",
        "postProcess.sh",
        "foam.foam",
    }
    for child in src.iterdir():
        if child.name not in keep_names:
            continue
        target = dst / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def configure_case(case_dir: Path, end_time: int, params: dict[str, float]) -> None:
    env = os.environ.copy()
    env["NASA_HUMP_CASE_DIR"] = str(case_dir.relative_to(ROOT))
    env["NASA_HUMP_MODEL"] = "kOmegaSSTML2"
    env["NASA_HUMP_START_FROM"] = "latestTime"
    env["NASA_HUMP_END_TIME"] = str(end_time)
    env["NASA_HUMP_WRITE_INTERVAL"] = "10"
    env["NASA_HUMP_SCHEME_MODE"] = "stable"
    env["NASA_HUMP_ML2_AMPLITUDE"] = f"{params['amplitude']:.12g}"
    env["NASA_HUMP_ML2_FACTOR_MIN"] = f"{params['factor_min']:.12g}"
    env["NASA_HUMP_ML2_FACTOR_MAX"] = f"{params['factor_max']:.12g}"
    env["NASA_HUMP_ML2_APG0"] = f"{params['apg0']:.12g}"
    env["NASA_HUMP_ML2_APG_WIDTH"] = f"{params['apg_width']:.12g}"
    env["NASA_HUMP_ML2_SHEAR0"] = f"{params['shear0']:.12g}"
    env["NASA_HUMP_ML2_SHEAR_WIDTH"] = f"{params['shear_width']:.12g}"
    env["NASA_HUMP_ML2_Y_PEAK"] = f"{params['y_peak']:.12g}"
    env["NASA_HUMP_ML2_Y_WIDTH"] = f"{params['y_width']:.12g}"
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


def bounded_params(params: dict[str, float]) -> dict[str, float]:
    return {
        "amplitude": max(0.0, min(0.90, float(params["amplitude"]))),
        "factor_min": max(0.8, min(1.2, float(params.get("factor_min", 1.0)))),
        "factor_max": max(1.0, min(2.5, float(params.get("factor_max", 1.80)))),
        "apg0": max(0.0, min(0.20, float(params["apg0"]))),
        "apg_width": max(0.005, min(0.50, float(params.get("apg_width", 0.02)))),
        "shear0": max(0.5, min(1.6, float(params["shear0"]))),
        "shear_width": max(0.05, min(2.0, float(params.get("shear_width", 0.20)))),
        "y_peak": max(0.010, min(0.030, float(params["y_peak"]))),
        "y_width": max(0.004, min(0.050, float(params.get("y_width", 0.012)))),
    }


def regularization(params: dict[str, float]) -> float:
    amp_term = 0.015 * (params["amplitude"] / 0.60) ** 2
    shear_term = 0.004 * ((params["shear0"] - 1.0) / 0.40) ** 2
    return float(amp_term + shear_term)


def objective_from_metrics(mae: float, cp_mae: float, cf_mae: float, penalty: float) -> float:
    return float(0.60 * mae + 0.25 * cp_mae + 0.15 * (cf_mae / 1.0e-3) + penalty)


def record_history(rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
        "apg0",
        "shear0",
        "y_peak",
        "notes",
    ]
    with LOG_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    LOG_JSON.write_text(json.dumps({"rows": rows}, indent=2))


def evaluate_candidate(tag: str, raw_params: dict[str, float], end_time: int, stage: str, history: list[dict[str, object]]) -> dict[str, object]:
    params = bounded_params(raw_params)
    case_dir = SWEEP_ROOT / tag
    copy_full_case(PASS4_BASE, case_dir)
    configure_case(case_dir, end_time, params)

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
        "apg0": params["apg0"],
        "shear0": params["shear0"],
        "y_peak": params["y_peak"],
        "notes": "stable" if stable else "solver failure",
    }

    if stable:
        time_name = latest_numeric_dir(case_dir).name
        mae_result = evaluate_case(case_dir, time_name)
        wall_result = evaluate_wall(case_dir, time_name)
        penalty = regularization(params)
        objective = objective_from_metrics(
            float(mae_result["score"]),
            float(wall_result["cp_mae"]),
            float(wall_result["cf_mae"]),
            penalty,
        )
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def select_best(rows: list[dict[str, object]]) -> dict[str, object]:
    return min(rows, key=lambda row: float(row["objective"]))


def same_signature(a: dict[str, object], b: dict[str, object]) -> bool:
    return (
        abs(float(a["amplitude"]) - float(b["amplitude"])) < 1.0e-12
        and abs(float(a["apg0"]) - float(b["apg0"])) < 1.0e-12
        and abs(float(a["shear0"]) - float(b["shear0"])) < 1.0e-12
        and abs(float(a["y_peak"]) - float(b["y_peak"])) < 1.0e-12
    )


def main() -> None:
    build_model()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SWEEP_ROOT.mkdir(parents=True, exist_ok=True)

    ml1_summary = load_json(ROOT / "documentation_src" / "data_mlpass1" / "mlpass1_summary.json")
    ml1_compare = load_json(ROOT / "documentation_src" / "data_mlpass1" / "mlpass1_comparison_summary.json")
    pass4_summary = load_json(ROOT / "documentation_src" / "data_pass4" / "pass4_experiment_summary.json")

    baseline_cheap = ml1_summary["baseline_cheap"]
    baseline_full = ml1_summary["baseline_full"]
    ml1_nonzero = ml1_compare["corrected"]
    pass4_best = next(row for row in pass4_summary["rows"] if row["tag"] == "pass4_uniform_sst_650")

    cheap_candidates = [
        {"tag": "mlpass2_opt_001", "params": {"amplitude": 0.35, "apg0": 0.030, "shear0": 0.90, "y_peak": 0.018}},
        {"tag": "mlpass2_opt_002", "params": {"amplitude": 0.60, "apg0": 0.020, "shear0": 0.80, "y_peak": 0.020}},
        {"tag": "mlpass2_opt_003", "params": {"amplitude": 0.20, "apg0": 0.050, "shear0": 1.10, "y_peak": 0.014}},
        {"tag": "mlpass2_opt_004", "params": {"amplitude": 0.15, "apg0": 0.010, "shear0": 1.00, "y_peak": 0.016}},
    ]

    history: list[dict[str, object]] = []
    cheap_rows: list[dict[str, object]] = []
    for candidate in cheap_candidates:
        cheap_rows.append(evaluate_candidate(candidate["tag"], candidate["params"], 720, "cheap", history))

    best_cheap = select_best(cheap_rows)
    focused_params = {
        "amplitude": float(best_cheap["amplitude"]) + 0.15,
        "apg0": float(best_cheap["apg0"]) - 0.010,
        "shear0": float(best_cheap["shear0"]) - 0.10,
        "y_peak": float(best_cheap["y_peak"]) + 0.002,
    }
    conservative_params = {
        "amplitude": max(0.05, float(best_cheap["amplitude"]) - 0.10),
        "apg0": float(best_cheap["apg0"]) + 0.010,
        "shear0": float(best_cheap["shear0"]) + 0.10,
        "y_peak": float(best_cheap["y_peak"]) - 0.002,
    }

    cheap_rows.append(evaluate_candidate("mlpass2_opt_005", focused_params, 720, "cheap", history))
    cheap_rows.append(evaluate_candidate("mlpass2_opt_006", conservative_params, 720, "cheap", history))

    unique_rows: list[dict[str, object]] = []
    for row in sorted(cheap_rows, key=lambda item: float(item["objective"])):
        if not any(same_signature(row, seen) for seen in unique_rows):
            unique_rows.append(row)

    shortlist = unique_rows[:2]
    full_rows = [
        evaluate_candidate(f"mlpass2_full_{idx:02d}", row, 800, "full", history)
        for idx, row in enumerate(shortlist, start=1)
    ]

    best_full = select_best(full_rows)
    promote = (
        float(best_full["mae"]) < float(baseline_full["mae"])
        and float(best_full["cp_mae"]) <= float(baseline_full["cp_mae"]) + 0.002
        and float(best_full["cf_mae"]) <= float(baseline_full["cf_mae"]) + 1.0e-4
        and bool(best_full["stable"])
    )

    summary = {
        "objective_definition": {
            "formula": "J = 0.60*benchmark_MAE + 0.25*Cp_MAE + 0.15*(Cf_MAE/1e-3) + penalty",
            "penalty": "0.015*(amplitude/0.6)^2 + 0.004*((shear0-1.0)/0.4)^2",
        },
        "optimizer": {
            "name": "pattern_search",
            "cheap_stage_end_time": 720,
            "full_stage_end_time": 800,
            "initial_candidates": len(cheap_candidates),
            "focused_candidates": 2,
        },
        "correction_design": {
            "model": "kOmegaSSTML2",
            "description": "Separation-aware bounded production correction acting on both Pk and omega production through an adverse-pressure-gradient and shear-layer sensor.",
            "parameters": {
                "amplitude": "[0.0, 0.9]",
                "apg0": "[0.0, 0.2]",
                "shear0": "[0.5, 1.6]",
                "y_peak": "[0.010, 0.030]",
            },
            "fixed": {
                "factorMin": 1.0,
                "factorMax": 1.8,
                "apgWidth": 0.02,
                "shearWidth": 0.20,
                "yWidth": 0.012,
            },
        },
        "pass4_best": pass4_best,
        "baseline_cheap": baseline_cheap,
        "baseline_full": baseline_full,
        "mlpass1_best_nonzero": ml1_nonzero,
        "best_cheap": best_cheap,
        "best_full": best_full,
        "promote_corrected_model": promote,
        "rows": history,
    }

    with SUMMARY_JSON.open("w") as handle:
        json.dump(summary, handle, indent=2)

    with SUMMARY_CSV.open("w", newline="") as handle:
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
                "apg0",
                "shear0",
                "y_peak",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(history)


if __name__ == "__main__":
    main()
