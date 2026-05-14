#!/usr/bin/env python3
"""Extract a more robust near-wall Cp series from a PyFR VTU using VTK via pvpython."""

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
HUMP_HEIGHT = 0.053


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return HUMP_HEIGHT * math.sin(math.pi * xi) ** 2


def read_grid(path: Path):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    return reader.GetOutput()


def load_exp_cp(path: Path) -> list[dict[str, float]]:
    rows = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({"x_over_c": float(row["x_over_c"]), "Cp_exp": float(row["Cp"])})
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_candidates(grid, pressure_name: str = "Pressure") -> list[dict[str, float]]:
    pdata = grid.GetPointData()
    p_arr = pdata.GetArray(pressure_name)
    if p_arr is None:
        raise RuntimeError(f"Point-data array '{pressure_name}' was not found")

    candidates = []
    for i in range(grid.GetNumberOfPoints()):
        x, y, _ = grid.GetPoint(i)
        p = float(p_arr.GetTuple1(i))
        yw = hump_height(x)
        dy = y - yw
        if dy < -1.0e-8:
            continue
        if dy > 7.5e-3:
            continue
        candidates.append({"x_m": x, "y_m": y, "y_wall_m": yw, "dy_m": dy, "pressure": p})
    return candidates


def pick_first_finite_layer(candidates: list[dict[str, float]]) -> list[dict[str, float]]:
    groups: dict[float, list[dict[str, float]]] = {}
    for row in candidates:
        groups.setdefault(round(row["x_m"], 5), []).append(row)

    wall_rows = []
    for _, rows in groups.items():
        rows.sort(key=lambda r: (r["dy_m"], abs(r["dy_m"])))
        chosen = next((r for r in rows if math.isfinite(r["pressure"])), None)
        if chosen is None:
            chosen = rows[0]
        wall_rows.append(chosen)
    wall_rows.sort(key=lambda r: r["x_m"])
    return wall_rows


def choose_reference_pressure(wall_rows: list[dict[str, float]]) -> float:
    upstream = [r["pressure"] for r in wall_rows if r["x_m"] <= -0.75 and math.isfinite(r["pressure"])]
    if upstream:
        return sum(upstream) / len(upstream)
    finite = [r["pressure"] for r in wall_rows if math.isfinite(r["pressure"])]
    if finite:
        return sum(finite[: max(1, min(20, len(finite)))]) / min(20, len(finite))
    return math.nan


def nearest_rows(exp_x: list[float], cfd_rows: list[dict[str, float]]) -> list[dict[str, float]]:
    cfd_x = [row["x_over_c"] for row in cfd_rows]
    out = []
    for x in exp_x:
        idx = min(range(len(cfd_rows)), key=lambda i: abs(cfd_x[i] - x))
        chosen = dict(cfd_rows[idx])
        chosen["target_x_over_c"] = x
        chosen["dx_over_c"] = chosen["x_over_c"] - x
        out.append(chosen)
    return out


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("Usage: extract_pyfr_wall_pressure_pass5.py <vtu> <exp_cp_csv> <raw_csv> <comparison_csv>")

    vtu_path = Path(sys.argv[1]).resolve()
    exp_cp_path = Path(sys.argv[2]).resolve()
    raw_csv = Path(sys.argv[3]).resolve()
    comparison_csv = Path(sys.argv[4]).resolve()

    grid = read_grid(vtu_path)
    candidates = build_candidates(grid)
    wall_rows = pick_first_finite_layer(candidates)
    p_ref = choose_reference_pressure(wall_rows)
    for row in wall_rows:
        row["x_over_c"] = row["x_m"] / CHORD
        row["Cp"] = (row["pressure"] - p_ref) / Q_REF if math.isfinite(row["pressure"]) and math.isfinite(p_ref) else math.nan
    write_csv(raw_csv, wall_rows, ["x_m", "x_over_c", "y_m", "y_wall_m", "dy_m", "pressure", "Cp"])

    exp_rows = load_exp_cp(exp_cp_path)
    matched = nearest_rows([r["x_over_c"] for r in exp_rows], wall_rows)
    comparison_rows = []
    for exp, cfd in zip(exp_rows, matched):
        cp_pyfr = cfd["Cp"]
        abs_err = abs(cp_pyfr - exp["Cp_exp"]) if math.isfinite(cp_pyfr) else math.nan
        comparison_rows.append(
            {
                "x_over_c": exp["x_over_c"],
                "Cp_exp": exp["Cp_exp"],
                "Cp_pyfr": cp_pyfr,
                "cfd_x_over_c": cfd["x_over_c"],
                "dy_m": cfd["dy_m"],
                "dx_over_c": cfd["dx_over_c"],
                "abs_error": abs_err,
            }
        )
    write_csv(comparison_csv, comparison_rows, ["x_over_c", "Cp_exp", "Cp_pyfr", "cfd_x_over_c", "dy_m", "dx_over_c", "abs_error"])

    finite_errors = [r["abs_error"] for r in comparison_rows if math.isfinite(r["abs_error"])]
    summary = {
        "p_ref": p_ref,
        "num_candidate_points": len(candidates),
        "num_wall_rows": len(wall_rows),
        "num_comparison_rows": len(comparison_rows),
        "finite_cp_matches": len(finite_errors),
        "cp_mae": sum(finite_errors) / len(finite_errors) if finite_errors else math.nan,
        "cp_rmse": math.sqrt(sum(err * err for err in finite_errors) / len(finite_errors)) if finite_errors else math.nan,
        "notes": "Geometry-aware near-wall extraction using the first finite layer above the hump wall. NASA targets were compared by nearest-CFD-sample matching only.",
    }
    comparison_csv.with_suffix(".json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
