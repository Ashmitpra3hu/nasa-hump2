#!/usr/bin/env python3
"""Evaluate a NASA hump case directory against the local benchmark metric."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from closure_challenge.eval import evaluate_individual_case
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator


ROOT = Path(__file__).resolve().parents[1]
EVAL_POINTS = ROOT / "data" / "evaluation_points" / "NASA_2DWMH_points.csv"


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


def select_time_dir(base: Path, time_name: str | None) -> Path:
    if time_name is None:
        return latest_numeric_dir(base)
    candidate = base / time_name
    if not candidate.is_dir():
        raise FileNotFoundError(f"Requested time directory {candidate} does not exist")
    return candidate


def evaluate(case_dir: Path, time_name: str | None = None) -> dict[str, object]:
    latest = select_time_dir(case_dir, time_name)
    coords = parse_internal_field(case_dir / "0" / "C")
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
    score = float(evaluate_individual_case("NASA_2DWMH", predictions))
    return {
        "case_dir": str(case_dir.relative_to(ROOT)),
        "time_directory": latest.name,
        "num_points": int(predictions.shape[0]),
        "score": score,
        "predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--time", type=str)
    parser.add_argument("--prediction-csv", type=Path)
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    result = evaluate(args.case_dir.resolve(), args.time)
    predictions = result.pop("predictions")
    if args.prediction_csv:
        args.prediction_csv.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(args.prediction_csv, predictions, delimiter=",")
        result["prediction_file"] = str(args.prediction_csv.resolve().relative_to(ROOT))

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
