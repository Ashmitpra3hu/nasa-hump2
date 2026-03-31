#!/usr/bin/env python3
"""Evaluate the currently available NASA hump solution for the second-pass package."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from closure_challenge.eval import evaluate_individual_case
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "data" / "NASA_2DWMH"
EVAL_POINTS = ROOT / "data" / "evaluation_points" / "NASA_2DWMH_points.csv"
OUT_DIR = ROOT / "documentation_src" / "data_second_pass"
PRED_CSV = OUT_DIR / "reconstructed_nasa_predictions_second_pass.csv"
SUMMARY_JSON = OUT_DIR / "reconstructed_nasa_score_second_pass.json"
FIRST_PASS_JSON = ROOT / "docs" / "data" / "reconstructed_nasa_score.json"


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
        raise ValueError(f"Could not parse field size from {path}")

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


def latest_numeric_dir(base: Path) -> Path:
    numeric_dirs = []
    for child in base.iterdir():
        if child.is_dir():
            try:
                numeric_dirs.append((float(child.name), child))
            except ValueError:
                continue
    if not numeric_dirs:
        raise FileNotFoundError(f"No numeric time directories found in {base}")
    return max(numeric_dirs, key=lambda item: item[0])[1]


def load_first_pass_score() -> float | None:
    if not FIRST_PASS_JSON.exists():
        return None
    return float(json.loads(FIRST_PASS_JSON.read_text()).get("score"))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest = latest_numeric_dir(CASE_DIR)
    coords = parse_internal_field(CASE_DIR / "0" / "C")
    U = parse_internal_field(latest / "U")
    eval_points = np.loadtxt(EVAL_POINTS, delimiter=",")

    mesh_points = np.column_stack((coords[:, 0], coords[:, 1]))
    query_points = np.column_stack((eval_points[:, 0], eval_points[:, 2]))

    linear_u = LinearNDInterpolator(mesh_points, U[:, 0])
    linear_v = LinearNDInterpolator(mesh_points, U[:, 1])
    nearest_u = NearestNDInterpolator(mesh_points, U[:, 0])
    nearest_v = NearestNDInterpolator(mesh_points, U[:, 1])

    pred_u = linear_u(query_points)
    pred_v = linear_v(query_points)

    nan_mask = np.isnan(pred_u) | np.isnan(pred_v)
    if np.any(nan_mask):
        pred_u[nan_mask] = nearest_u(query_points[nan_mask])
        pred_v[nan_mask] = nearest_v(query_points[nan_mask])

    predictions = np.column_stack((pred_u, np.zeros_like(pred_u), pred_v))
    np.savetxt(PRED_CSV, predictions, delimiter=",")

    score = float(evaluate_individual_case("NASA_2DWMH", predictions))
    first_pass_score = load_first_pass_score()
    summary = {
        "case": "NASA_2DWMH",
        "time_directory": latest.name,
        "prediction_file": str(PRED_CSV.relative_to(ROOT)),
        "num_points": int(predictions.shape[0]),
        "score": score,
        "first_pass_score_reference": first_pass_score,
        "score_delta_vs_first_pass": None if first_pass_score is None else score - first_pass_score,
        "score_improvement_vs_first_pass": None if first_pass_score is None else first_pass_score - score,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
