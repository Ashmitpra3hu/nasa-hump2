#!/usr/bin/env python3
"""Inspect PyFR VTU arrays and near-wall field quality using VTK via pvpython."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import vtk


CHORD = 0.42
HUMP_HEIGHT = 0.053


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return HUMP_HEIGHT * math.sin(math.pi * xi) ** 2


def finite_stats(values: list[float]) -> dict[str, float | int | None]:
    finite = [v for v in values if math.isfinite(v)]
    return {
        "count": len(values),
        "finite_count": len(finite),
        "nan_count": sum(math.isnan(v) for v in values),
        "inf_count": sum(math.isinf(v) for v in values),
        "min": min(finite) if finite else None,
        "max": max(finite) if finite else None,
        "mean": statistics.fmean(finite) if finite else None,
    }


def read_grid(path: Path):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    return reader.GetOutput()


def array_summary(arr) -> dict[str, object]:
    ncomp = arr.GetNumberOfComponents()
    ntup = arr.GetNumberOfTuples()
    summary: dict[str, object] = {
        "name": arr.GetName(),
        "num_components": ncomp,
        "num_tuples": ntup,
        "components": [],
    }
    for j in range(ncomp):
        vals = [float(arr.GetComponent(i, j)) for i in range(ntup)]
        summary["components"].append(finite_stats(vals))
    return summary


def near_wall_audit(grid, pressure_arr_name: str = "Pressure") -> dict[str, object]:
    pdata = grid.GetPointData()
    p_arr = pdata.GetArray(pressure_arr_name)
    if p_arr is None:
        return {"pressure_array_found": False}

    exact_vals = []
    band_vals = []
    layer_rows = []
    for i in range(grid.GetNumberOfPoints()):
        x, y, _ = grid.GetPoint(i)
        yw = hump_height(x)
        p = float(p_arr.GetTuple1(i))
        dy = y - yw
        if -1.0e-8 <= dy <= 5.0e-5:
            exact_vals.append(p)
            layer_rows.append({"x_m": x, "y_m": y, "y_wall_m": yw, "dy_m": dy, "pressure": p, "region": "exact"})
        if 5.0e-5 < dy <= 5.0e-3:
            band_vals.append(p)
            layer_rows.append({"x_m": x, "y_m": y, "y_wall_m": yw, "dy_m": dy, "pressure": p, "region": "band"})

    return {
        "pressure_array_found": True,
        "exact_wall_stats": finite_stats(exact_vals),
        "near_wall_band_stats": finite_stats(band_vals),
        "sample_rows": layer_rows[:2000],
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: inspect_pyfr_vtu_fields.py <vtu> <output_json>")
    vtu_path = Path(sys.argv[1]).resolve()
    out_json = Path(sys.argv[2]).resolve()

    grid = read_grid(vtu_path)
    payload: dict[str, object] = {
        "file": str(vtu_path),
        "num_points": grid.GetNumberOfPoints(),
        "num_cells": grid.GetNumberOfCells(),
        "point_arrays": [],
        "cell_arrays": [],
    }

    pdata = grid.GetPointData()
    for i in range(pdata.GetNumberOfArrays()):
        payload["point_arrays"].append(array_summary(pdata.GetArray(i)))

    cdata = grid.GetCellData()
    for i in range(cdata.GetNumberOfArrays()):
        payload["cell_arrays"].append(array_summary(cdata.GetArray(i)))

    payload["near_wall_pressure_audit"] = near_wall_audit(grid)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
