#!/usr/bin/env python3
"""Render ParaView screenshots for the promoted finite PASS 6 PyFR VTU."""

from __future__ import annotations

from pathlib import Path
import sys

from paraview.simple import *  # noqa: F401,F403


ROOT = Path(__file__).resolve().parents[1]
PROMOTED_JSON = ROOT / "documentation_src" / "gpu_pyfr_pass6" / "data" / "promoted_case_summary.json"
FIG_DIR = ROOT / "documentation_src" / "gpu_pyfr_pass6" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def promoted_vtu() -> Path:
    import json

    data = json.loads(PROMOTED_JSON.read_text())
    case = data["config_name"]
    return ROOT / "runs" / "gpu_pyfr_pass6" / "stability" / case / f"{case}_latest.vtu"


def make_view():
    view = GetActiveViewOrCreate("RenderView")
    LoadPalette("WhiteBackground")
    view.ViewSize = [2400, 1100]
    view.CameraParallelProjection = 1
    view.OrientationAxesVisibility = 0
    return view


def save(name: str, view):
    SaveScreenshot(str(FIG_DIR / name), view, ImageResolution=view.ViewSize)


def set_camera(view, zoom: str):
    if zoom == "full":
        view.CameraPosition = [0.20, 0.17, 2.0]
        view.CameraFocalPoint = [0.20, 0.17, 0.0]
        view.CameraViewUp = [0.0, 1.0, 0.0]
        view.CameraParallelScale = 0.19
    elif zoom == "hump":
        view.CameraPosition = [0.20, 0.08, 2.0]
        view.CameraFocalPoint = [0.20, 0.08, 0.0]
        view.CameraViewUp = [0.0, 1.0, 0.0]
        view.CameraParallelScale = 0.09
    else:
        raise ValueError(f"Unknown zoom {zoom}")


def reader():
    src = XMLUnstructuredGridReader(FileName=[str(promoted_vtu())])
    src.PointArrayStatus = ["Velocity", "Pressure"]
    UpdatePipeline(proxy=src)
    return src


def render_velocity():
    view = make_view()
    src = reader()
    display = Show(src, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "Velocity", "Magnitude"))
    lut = GetColorTransferFunction("Velocity")
    lut.RescaleTransferFunction(0.0, 55.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("finite_field_velocity.png", view)


def render_pressure():
    view = make_view()
    src = reader()
    display = Show(src, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "Pressure"))
    lut = GetColorTransferFunction("Pressure")
    lut.RescaleTransferFunction(94500.0, 109700.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("finite_field_pressure.png", view)


def render_mesh():
    view = make_view()
    src = reader()
    display = Show(src, view)
    display.Representation = "Wireframe"
    display.LineWidth = 1.0
    display.AmbientColor = [0.1, 0.1, 0.1]
    display.DiffuseColor = [0.1, 0.1, 0.1]
    set_camera(view, "hump")
    Render()
    save("finite_field_mesh.png", view)


def render_streamlines():
    view = make_view()
    src = reader()
    seed = Line()
    seed.Point1 = [-0.55, 0.02, 0.0]
    seed.Point2 = [0.95, 0.18, 0.0]
    stream = StreamTracer(Input=src, SeedType="Line")
    stream.Vectors = ["POINTS", "Velocity"]
    stream.MaximumStreamlineLength = 2.0
    display = Show(stream, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "Velocity", "Magnitude"))
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("finite_field_streamlines.png", view)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: render_gpu_pyfr_pass6_paraview.py [velocity|pressure|mesh|streamlines]")

    mode = sys.argv[1]
    if mode == "velocity":
        render_velocity()
    elif mode == "pressure":
        render_pressure()
    elif mode == "mesh":
        render_mesh()
    elif mode == "streamlines":
        render_streamlines()
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
