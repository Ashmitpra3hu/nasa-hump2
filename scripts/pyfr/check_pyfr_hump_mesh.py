#!/usr/bin/env python3
"""Basic sanity checks for the PASS 2 PyFR hump mesh."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import meshio
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = ROOT / "data" / "NASA_2DWMH_PyFR"
MESH_DIR = CASE_DIR / "meshes"


def triangle_area(points: np.ndarray, tri: np.ndarray) -> float:
    p0, p1, p2 = points[tri]
    return 0.5 * (
        (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["minimal", "medium", "promoted"], default="minimal")
    args = parser.parse_args()

    mesh_name = "nasa_hump_medium.msh" if args.variant in {"minimal", "medium"} else "nasa_hump_promoted.msh"
    path = MESH_DIR / mesh_name
    if not path.exists():
        raise FileNotFoundError(path)

    mesh = meshio.read(path)
    points = np.asarray(mesh.points[:, :2], dtype=float)
    tri_blocks = [block.data for block in mesh.cells if block.type == "triangle"]
    line_blocks = [block.data for block in mesh.cells if block.type == "line"]
    triangles = np.vstack(tri_blocks) if tri_blocks else np.empty((0, 3), dtype=int)
    lines = np.vstack(line_blocks) if line_blocks else np.empty((0, 2), dtype=int)

    tri_areas = np.array([triangle_area(points, tri) for tri in triangles], dtype=float) if len(triangles) else np.array([])
    duplicates = len(points) - len(np.unique(np.round(points, decimals=12), axis=0))
    degenerate = int(np.sum(np.abs(tri_areas) < 1.0e-12)) if len(tri_areas) else 0
    negative = int(np.sum(tri_areas < 0.0)) if len(tri_areas) else 0

    field_names = set()
    for key, data in mesh.cell_data.items():
        if key == "gmsh:physical":
            for arr in data:
                field_names.update(map(str, np.unique(arr).tolist()))

    summary = {
        "mesh_file": str(path),
        "num_points": int(points.shape[0]),
        "num_triangles": int(triangles.shape[0]),
        "num_lines": int(lines.shape[0]),
        "duplicate_points": int(duplicates),
        "degenerate_triangles": int(degenerate),
        "negative_oriented_triangles": int(negative),
        "xmin": float(points[:, 0].min()),
        "xmax": float(points[:, 0].max()),
        "ymin": float(points[:, 1].min()),
        "ymax": float(points[:, 1].max()),
        "gmsh_physical_ids_present": sorted(field_names),
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
