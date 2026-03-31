#!/usr/bin/env python3
"""Render a single ParaView screenshot from the NASA hump .foam case."""

from __future__ import annotations

import sys
from pathlib import Path

from paraview.simple import *  # noqa: F401,F403


ROOT = Path(__file__).resolve().parents[1]
FOAM_FILE = ROOT / "data" / "NASA_2DWMH" / "foam.foam"
FIG_DIR = ROOT / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def latest_time() -> float:
    numeric_dirs = []
    for child in (ROOT / "data" / "NASA_2DWMH").iterdir():
        if child.is_dir():
            try:
                numeric_dirs.append(float(child.name))
            except ValueError:
                continue
    if not numeric_dirs:
        raise FileNotFoundError("No numeric OpenFOAM time directories found.")
    return max(numeric_dirs)


LATEST_TIME = latest_time()


def make_view():
    view = GetActiveViewOrCreate("RenderView")
    LoadPalette("WhiteBackground")
    view.ViewSize = [2600, 1200]
    view.CameraParallelProjection = 1
    view.OrientationAxesVisibility = 0
    return view


def save(name: str, view):
    SaveScreenshot(str(FIG_DIR / name), view, ImageResolution=view.ViewSize)


def set_camera(view, zoom: str):
    if zoom == "full":
        view.CameraPosition = [-0.25, 0.17, 2.0]
        view.CameraFocalPoint = [-0.25, 0.17, 0.0]
        view.CameraViewUp = [0.0, 1.0, 0.0]
        view.CameraParallelScale = 0.19
    elif zoom == "hump":
        view.CameraPosition = [0.20, 0.085, 2.0]
        view.CameraFocalPoint = [0.20, 0.085, 0.0]
        view.CameraViewUp = [0.0, 1.0, 0.0]
        view.CameraParallelScale = 0.085
    else:
        raise ValueError(f"Unknown zoom '{zoom}'")


def foam_reader(regions: list[str]):
    reader = OpenFOAMReader(FileName=str(FOAM_FILE))
    reader.MeshRegions = regions
    reader.CellArrays = ["U", "k", "nut", "omega", "p"]
    reader.SkipZeroTime = 1
    UpdatePipeline(time=LATEST_TIME, proxy=reader)
    return reader


def internal_point_data():
    reader = foam_reader(["internalMesh"])
    c2p = CellDatatoPointData(Input=reader)
    UpdatePipeline(time=LATEST_TIME, proxy=c2p)
    return c2p


def bottom_wall_point_data():
    reader = foam_reader(["patch/bottomWall"])
    c2p = CellDatatoPointData(Input=reader)
    UpdatePipeline(time=LATEST_TIME, proxy=c2p)
    return c2p


def render_velocity(filename: str, zoom: str):
    view = make_view()
    data = internal_point_data()
    display = Show(data, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "U", "Magnitude"))
    lut = GetColorTransferFunction("U")
    lut.RescaleTransferFunction(0.0, 45.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, zoom)
    Render()
    save(filename, view)


def render_pressure(filename: str, zoom: str):
    view = make_view()
    data = internal_point_data()
    display = Show(data, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "p"))
    lut = GetColorTransferFunction("p")
    lut.RescaleTransferFunction(-100.0, 250.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, zoom)
    Render()
    save(filename, view)


def render_streamlines():
    view = make_view()
    data = internal_point_data()

    outline = Show(data, view)
    outline.Representation = "Outline"
    outline.AmbientColor = [0.55, 0.55, 0.55]
    outline.DiffuseColor = [0.55, 0.55, 0.55]

    tracer = StreamTracer(Input=data, SeedType="Line")
    tracer.Vectors = ["POINTS", "U"]
    tracer.MaximumStreamlineLength = 2.4
    tracer.SeedType.Point1 = [-1.15, 0.02, 0.0]
    tracer.SeedType.Point2 = [-1.15, 0.30, 0.0]
    tracer.SeedType.Resolution = 40
    UpdatePipeline(time=LATEST_TIME, proxy=tracer)

    tracer_display = Show(tracer, view)
    tracer_display.LineWidth = 2.0
    ColorBy(tracer_display, ("POINTS", "U", "Magnitude"))
    lut = GetColorTransferFunction("U")
    lut.RescaleTransferFunction(0.0, 45.0)
    tracer_display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("paraview_streamlines.png", view)


def render_mesh_wireframe():
    view = make_view()
    reader = foam_reader(["internalMesh"])
    display = Show(reader, view)
    display.Representation = "Wireframe"
    display.AmbientColor = [0.1, 0.1, 0.1]
    display.DiffuseColor = [0.1, 0.1, 0.1]
    display.LineWidth = 1.0
    set_camera(view, "hump")
    Render()
    save("paraview_mesh_wireframe.png", view)


def render_wall_patch():
    view = make_view()
    data = bottom_wall_point_data()
    display = Show(data, view)
    display.Representation = "Wireframe"
    display.LineWidth = 6.0
    ColorBy(display, ("POINTS", "p"))
    lut = GetColorTransferFunction("p")
    lut.RescaleTransferFunction(-100.0, 250.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "hump")
    view.CameraParallelScale = 0.05
    Render()
    save("paraview_wall_shear.png", view)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: render_nasa_hump_paraview.py "
            "[velocity|velocity_surface|pressure|pressure_surface|streamlines|mesh_wireframe|wall_patch]"
        )

    mode = sys.argv[1]
    if mode == "velocity":
        render_velocity("paraview_velocity.png", "full")
    elif mode == "velocity_surface":
        render_velocity("paraview_velocity_surface.png", "hump")
    elif mode == "pressure":
        render_pressure("paraview_pressure.png", "full")
    elif mode == "pressure_surface":
        render_pressure("paraview_pressure_surface.png", "hump")
    elif mode == "streamlines":
        render_streamlines()
    elif mode == "mesh_wireframe":
        render_mesh_wireframe()
    elif mode == "wall_patch":
        render_wall_patch()
    else:
        raise SystemExit(f"Unknown render mode: {mode}")


if __name__ == "__main__":
    main()
