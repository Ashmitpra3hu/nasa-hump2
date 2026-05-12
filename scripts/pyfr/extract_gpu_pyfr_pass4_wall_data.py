#!/usr/bin/env python3
"""Extract lower-wall pressure data from a PASS 4 VTU using VTK via pvpython."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import vtk


CHORD = 0.42
U_REF = 34.6
RHO = 1.225
Q_REF = 0.5 * RHO * U_REF**2
X_REF = -2.14 * CHORD


def read_grid(path: Path):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    return reader.GetOutput()


def point_arrays(grid) -> tuple[list[tuple[float, float]], list[float]]:
    points = []
    pressures = []
    pdata = grid.GetPointData()
    p_arr = pdata.GetArray("Pressure")
    if p_arr is None:
        raise RuntimeError("Pressure point array was not found in the VTU export.")
    for i in range(grid.GetNumberOfPoints()):
        x, y, _ = grid.GetPoint(i)
        points.append((x, y))
        pressures.append(float(p_arr.GetTuple1(i)))
    return points, pressures


def build_wall_series(points: list[tuple[float, float]], pressures: list[float]) -> tuple[list[dict[str, float]], float]:
    x_groups: dict[float, list[tuple[float, float, float]]] = {}
    for (x, y), p in zip(points, pressures):
        key = round(x, 5)
        x_groups.setdefault(key, []).append((x, y, p))

    series: list[dict[str, float]] = []
    ref_pool: list[float] = []
    for items in x_groups.values():
        x_avg = sum(item[0] for item in items) / len(items)
        min_y = min(item[1] for item in items)
        wall_items = [item for item in items if abs(item[1] - min_y) <= 1.0e-4]
        if not wall_items:
            continue
        finite_pressures = [item[2] for item in wall_items if math.isfinite(item[2])]
        p_avg = sum(finite_pressures) / len(finite_pressures) if finite_pressures else math.nan
        series.append(
            {
                "x_m": x_avg,
                "x_over_c": x_avg / CHORD,
                "y_wall_m": min_y,
                "pressure": p_avg,
            }
        )
        if abs(x_avg - X_REF) <= 0.02 and min_y > 0.02 and math.isfinite(p_avg):
            ref_pool.append(p_avg)

    series.sort(key=lambda row: row["x_m"])
    if not ref_pool:
        upstream = [row["pressure"] for row in series if row["x_m"] <= -0.75 and math.isfinite(row["pressure"])]
        ref_pool = upstream if upstream else [series[0]["pressure"]]
    p_ref = sum(ref_pool) / len(ref_pool)

    for row in series:
        row["Cp"] = (row["pressure"] - p_ref) / Q_REF
    return series, p_ref


def nearest_rows(exp_x: list[float], cfd_rows: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    cfd_x = [row["x_over_c"] for row in cfd_rows]
    for x in exp_x:
        idx = min(range(len(cfd_rows)), key=lambda i: abs(cfd_x[i] - x))
        chosen = dict(cfd_rows[idx])
        chosen["target_x_over_c"] = x
        chosen["dx_over_c"] = chosen["x_over_c"] - x
        out.append(chosen)
    return out


def load_exp_cp(path: Path) -> list[dict[str, float]]:
    rows = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({"x_over_c": float(row["x_over_c"]), "Cp_exp": float(row["Cp"])})
    return rows


def write_csv(path: Path, rows: list[dict[str, float]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("Usage: extract_gpu_pyfr_pass4_wall_data.py <vtu> <exp_cp_csv> <raw_csv> <comparison_csv>")

    vtu_path = Path(sys.argv[1]).resolve()
    exp_cp_path = Path(sys.argv[2]).resolve()
    raw_csv = Path(sys.argv[3]).resolve()
    comparison_csv = Path(sys.argv[4]).resolve()

    grid = read_grid(vtu_path)
    points, pressures = point_arrays(grid)
    wall_rows, p_ref = build_wall_series(points, pressures)
    write_csv(raw_csv, wall_rows, ["x_m", "x_over_c", "y_wall_m", "pressure", "Cp"])

    exp_rows = load_exp_cp(exp_cp_path)
    matched = nearest_rows([row["x_over_c"] for row in exp_rows], wall_rows)
    comparison_rows = []
    for exp, cfd in zip(exp_rows, matched):
        comparison_rows.append(
            {
                "x_over_c": exp["x_over_c"],
                "Cp_exp": exp["Cp_exp"],
                "Cp_pyfr": cfd["Cp"],
                "cfd_x_over_c": cfd["x_over_c"],
                "dx_over_c": cfd["dx_over_c"],
                "abs_error": abs(cfd["Cp"] - exp["Cp_exp"]),
            }
        )
    write_csv(comparison_csv, comparison_rows, ["x_over_c", "Cp_exp", "Cp_pyfr", "cfd_x_over_c", "dx_over_c", "abs_error"])

    finite_errors = [row["abs_error"] for row in comparison_rows if math.isfinite(row["abs_error"])]
    mae = sum(finite_errors) / len(finite_errors) if finite_errors else math.nan
    summary = {
        "p_ref": p_ref,
        "num_wall_rows": len(wall_rows),
        "num_comparison_rows": len(comparison_rows),
        "cp_mae": mae,
        "finite_cp_matches": len(finite_errors),
        "notes": "Nearest-CFD-sample comparison against official NASA Cp data. No target interpolation or wall-sampler plugin was used.",
    }
    summary_path = comparison_csv.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
