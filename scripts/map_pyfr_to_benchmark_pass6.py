#!/usr/bin/env python3
"""Map a finite PyFR VTU field to the local NASA hump benchmark points."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

try:
    import vtk  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment check
    raise SystemExit(
        "vtk is required to read the PyFR VTU. Run this script with pvpython "
        "or a Python environment that provides vtk."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
EVAL_POINTS = ROOT / "data" / "evaluation_points" / "NASA_2DWMH_points.csv"


def load_vtu_velocity(path: Path) -> tuple[np.ndarray, np.ndarray]:
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()

    vel_arr = grid.GetPointData().GetArray("Velocity")
    if vel_arr is None:
        raise RuntimeError(f"Velocity array missing from {path}")

    npts = grid.GetNumberOfPoints()
    coords = np.empty((npts, 2), dtype=float)
    velocity = np.empty((npts, 2), dtype=float)
    for i in range(npts):
        x, y, _ = grid.GetPoint(i)
        coords[i, :] = (x, y)
        tup = vel_arr.GetTuple(i)
        velocity[i, 0] = float(tup[0])
        velocity[i, 1] = float(tup[1])
    return coords, velocity


def load_eval_points() -> tuple[np.ndarray, np.ndarray]:
    raw = np.loadtxt(EVAL_POINTS, delimiter=",")
    query_xy = np.column_stack((raw[:, 0], raw[:, 2]))
    return raw, query_xy


def summarize_nearest_distances(mesh_xy: np.ndarray, query_xy: np.ndarray) -> np.ndarray:
    deltas = mesh_xy[:, None, :] - query_xy[None, :, :]
    dist = np.sqrt(np.sum(deltas * deltas, axis=2))
    return np.min(dist, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vtu", type=Path, required=True)
    parser.add_argument("--field-audit", type=Path, required=True)
    parser.add_argument("--prediction-csv", type=Path, required=True)
    parser.add_argument("--sample-csv", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    args = parser.parse_args()

    audit = json.loads(args.field_audit.read_text())
    point_arrays = {a["name"]: a for a in audit.get("point_arrays", [])}
    velocity_meta = point_arrays.get("Velocity")
    if velocity_meta is None:
        result = {"available": False, "reason": "Velocity array missing from VTU audit."}
        args.summary_json.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return

    finite_vx = int(velocity_meta["components"][0].get("finite_count", 0))
    finite_vy = int(velocity_meta["components"][1].get("finite_count", 0))
    if finite_vx == 0 or finite_vy == 0:
        result = {
            "available": False,
            "reason": "PyFR benchmark mapping unavailable because the VTU velocity field is globally non-finite.",
            "finite_velocity_x": finite_vx,
            "finite_velocity_y": finite_vy,
        }
        args.summary_json.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return

    mesh_xy, velocity_xy = load_vtu_velocity(args.vtu)
    finite_mask = np.all(np.isfinite(velocity_xy), axis=1) & np.all(np.isfinite(mesh_xy), axis=1)
    mesh_xy = mesh_xy[finite_mask]
    velocity_xy = velocity_xy[finite_mask]

    raw_eval, query_xy = load_eval_points()

    linear_u = LinearNDInterpolator(mesh_xy, velocity_xy[:, 0])
    linear_v = LinearNDInterpolator(mesh_xy, velocity_xy[:, 1])
    nearest_u = NearestNDInterpolator(mesh_xy, velocity_xy[:, 0])
    nearest_v = NearestNDInterpolator(mesh_xy, velocity_xy[:, 1])

    pred_u = linear_u(query_xy)
    pred_v = linear_v(query_xy)
    linear_nan = np.isnan(pred_u) | np.isnan(pred_v)
    if np.any(linear_nan):
        pred_u[linear_nan] = nearest_u(query_xy[linear_nan])
        pred_v[linear_nan] = nearest_v(query_xy[linear_nan])

    predictions = np.column_stack((pred_u, np.zeros_like(pred_u), pred_v))
    nearest_dist = summarize_nearest_distances(mesh_xy, query_xy)
    args.prediction_csv.parent.mkdir(parents=True, exist_ok=True)
    args.sample_csv.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)

    np.savetxt(args.prediction_csv, predictions, delimiter=",")
    with args.sample_csv.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "query_x_m",
                "query_y_m",
                "query_x_over_c",
                "pred_u_mps",
                "pred_v_mps",
                "nearest_distance_m",
                "used_nearest_fallback",
            ]
        )
        for (qx, qy), (u, _, v), dist, fallback in zip(query_xy, predictions, nearest_dist, linear_nan):
            writer.writerow([qx, qy, qx / 0.42, u, v, dist, int(bool(fallback))])

    result = {
        "available": True,
        "num_query_points": int(predictions.shape[0]),
        "finite_velocity_points_used": int(mesh_xy.shape[0]),
        "linear_fallback_count": int(np.count_nonzero(linear_nan)),
        "max_nearest_distance_m": float(np.max(nearest_dist)),
        "mean_nearest_distance_m": float(np.mean(nearest_dist)),
        "vtu": str(args.vtu.resolve().relative_to(ROOT)),
        "prediction_file": str(args.prediction_csv.resolve().relative_to(ROOT)),
        "sample_file": str(args.sample_csv.resolve().relative_to(ROOT)),
    }
    try:
        from closure_challenge.eval import evaluate_individual_case  # type: ignore

        result["score"] = float(evaluate_individual_case("NASA_2DWMH", predictions))
        result["score_available"] = True
    except ModuleNotFoundError:
        result["score_available"] = False
        result["score_unavailable_reason"] = (
            "closure_challenge is not available in this Python interpreter. "
            "The prediction CSV is still valid and can be scored by the repo's system Python."
        )
    args.summary_json.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
