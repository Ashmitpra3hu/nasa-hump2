#!/usr/bin/env python3
"""Generate reproducible Gmsh meshes for GPU PyFR PASS 1."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import gmsh


ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = ROOT / "data" / "NASA_2DWMH_PyFR"
MESH_DIR = CASE_DIR / "meshes"
CHORD = 0.42
X_MIN = -1.35
X_MAX = 0.84
TOP_Z = 0.35
HUMP_HEIGHT = 0.053
TOP_CONTOUR_START = -0.25
TOP_CONTOUR_END = 0.65
TOP_CONTOUR_DIP = 0.02
X_SPLITS = [X_MIN, 0.0, CHORD, X_MAX]


def hump_height(x: float) -> float:
    if x <= 0.0 or x >= CHORD:
        return 0.0
    xi = x / CHORD
    return HUMP_HEIGHT * math.sin(math.pi * xi) ** 2


def top_height(x: float) -> float:
    if x <= TOP_CONTOUR_START or x >= TOP_CONTOUR_END:
        return TOP_Z
    xi = (x - TOP_CONTOUR_START) / (TOP_CONTOUR_END - TOP_CONTOUR_START)
    return TOP_Z - TOP_CONTOUR_DIP * math.sin(math.pi * xi) ** 2


def add_spline(x0: float, x1: float, fn, nctrl: int) -> tuple[int, int, int]:
    tags = []
    for i in range(nctrl):
        x = x0 + (x1 - x0) * i / (nctrl - 1)
        tags.append(gmsh.model.geo.addPoint(x, fn(x), 0.0))
    return tags[0], gmsh.model.geo.addSpline(tags), tags[-1]


def set_curve(curve: int, npts: int, progression: float = 1.0) -> None:
    if abs(progression - 1.0) < 1e-12:
        gmsh.model.mesh.setTransfiniteCurve(curve, npts)
    else:
        gmsh.model.mesh.setTransfiniteCurve(curve, npts, "Progression", progression)


def build_smoke(path: Path) -> None:
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.model.add("pyfr-smoke")

    nx, ny = 48, 28
    x0, x1, y0, y1 = 0.0, 1.0, 0.0, 0.2
    p1 = gmsh.model.geo.addPoint(x0, y0, 0.0)
    p2 = gmsh.model.geo.addPoint(x1, y0, 0.0)
    p3 = gmsh.model.geo.addPoint(x1, y1, 0.0)
    p4 = gmsh.model.geo.addPoint(x0, y1, 0.0)
    c1 = gmsh.model.geo.addLine(p1, p2)
    c2 = gmsh.model.geo.addLine(p2, p3)
    c3 = gmsh.model.geo.addLine(p3, p4)
    c4 = gmsh.model.geo.addLine(p4, p1)
    loop = gmsh.model.geo.addCurveLoop([c1, c2, c3, c4])
    surf = gmsh.model.geo.addPlaneSurface([loop])
    gmsh.model.geo.synchronize()

    set_curve(c1, nx + 1)
    set_curve(c3, nx + 1)
    set_curve(c2, ny + 1)
    set_curve(c4, ny + 1)
    gmsh.model.mesh.setTransfiniteSurface(surf, "Left", [p1, p2, p3, p4])
    gmsh.model.mesh.setRecombine(2, surf)

    gmsh.model.addPhysicalGroup(1, [c4], name="inlet")
    gmsh.model.addPhysicalGroup(1, [c2], name="outlet")
    gmsh.model.addPhysicalGroup(1, [c1], name="bottomWall")
    gmsh.model.addPhysicalGroup(1, [c3], name="topWall")
    gmsh.model.addPhysicalGroup(2, [surf], name="fluid")

    gmsh.model.mesh.generate(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    gmsh.write(str(path))
    gmsh.finalize()


def build_hump(path: Path, xcells: list[int], ycells: int, order: int) -> None:
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.model.add(f"nasa-hump-p{order}")

    bottom_curves = []
    top_curves = []
    lower_pts = []
    upper_pts = []

    for i, (x0, x1) in enumerate(zip(X_SPLITS[:-1], X_SPLITS[1:])):
        p0, cb, p1 = add_spline(x0, x1, hump_height, 41)
        q0, ct, q1 = add_spline(x0, x1, top_height, 41)
        if i == 0:
            lower_pts.append(p0)
            upper_pts.append(q0)
        lower_pts.append(p1)
        upper_pts.append(q1)
        bottom_curves.append(cb)
        top_curves.append(ct)

    verticals = [gmsh.model.geo.addLine(pb, pt) for pb, pt in zip(lower_pts, upper_pts)]

    surfaces = []
    for i in range(3):
        loop = gmsh.model.geo.addCurveLoop(
            [
                bottom_curves[i],
                verticals[i + 1],
                -top_curves[i],
                -verticals[i],
            ]
        )
        surf = gmsh.model.geo.addPlaneSurface([loop])
        surfaces.append(surf)

    gmsh.model.geo.synchronize()

    x_progress = [1.15, 1.0, 0.9]
    for i in range(3):
        set_curve(bottom_curves[i], xcells[i] + 1, x_progress[i])
        set_curve(top_curves[i], xcells[i] + 1, x_progress[i])
    for idx, curve in enumerate(verticals):
        progression = 1.0 if idx in {0, len(verticals) - 1} else 1.06
        set_curve(curve, ycells + 1, progression)

    for surf, p1, p2, p3, p4 in zip(surfaces, lower_pts[:-1], lower_pts[1:], upper_pts[1:], upper_pts[:-1]):
        gmsh.model.mesh.setTransfiniteSurface(surf, "Left", [p1, p2, p3, p4])
        gmsh.model.mesh.setRecombine(2, surf)

    gmsh.model.addPhysicalGroup(1, [verticals[0]], name="inlet")
    gmsh.model.addPhysicalGroup(1, [verticals[-1]], name="outlet")
    gmsh.model.addPhysicalGroup(1, bottom_curves, name="bottomWall")
    gmsh.model.addPhysicalGroup(1, top_curves, name="topWall")
    gmsh.model.addPhysicalGroup(2, surfaces, name="fluid")

    gmsh.model.mesh.generate(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    gmsh.write(str(path))
    gmsh.finalize()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=["smoke", "medium", "promoted"])
    args = parser.parse_args()

    MESH_DIR.mkdir(parents=True, exist_ok=True)
    if args.variant == "smoke":
        build_smoke(MESH_DIR / "smoke_rect.msh")
    elif args.variant == "medium":
        build_hump(MESH_DIR / "nasa_hump_medium.msh", [84, 96, 72], 68, 2)
    elif args.variant == "promoted":
        build_hump(MESH_DIR / "nasa_hump_promoted.msh", [120, 140, 96], 92, 2)


if __name__ == "__main__":
    main()
