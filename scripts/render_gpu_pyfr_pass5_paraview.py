#!/usr/bin/env python3
"""Render PASS 5 ParaView screenshots from the exported VTU."""

from __future__ import annotations

from pathlib import Path
import sys

from paraview.simple import *  # noqa: F401,F403


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gpu_pyfr_pass5"
FIG_DIR = ROOT / "documentation_src" / "gpu_pyfr_pass5" / "paraview"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def vtu_path() -> Path:
    promoted = RUN_ROOT / "promoted" / "pass5_promoted_latest.vtu"
    diagnostic = RUN_ROOT / "diagnostic" / "pass5_diagnostic_latest.vtu"
    return promoted if promoted.exists() else diagnostic


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
    src = XMLUnstructuredGridReader(FileName=[str(vtu_path())])
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
    lut.RescaleTransferFunction(0.0, 45.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("pass5_velocity.png", view)


def render_pressure():
    view = make_view()
    src = reader()
    display = Show(src, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "Pressure"))
    lut = GetColorTransferFunction("Pressure")
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("pass5_pressure.png", view)


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
    save("pass5_mesh.png", view)


def render_streamline():
    view = make_view()
    src = reader()
    tracer = StreamTracer(Input=src, SeedType="Line")
    tracer.Vectors = ["POINTS", "Velocity"]
    tracer.MaximumStreamlineLength = 2.4
    tracer.SeedType.Point1 = [-1.10, 0.03, 0.0]
    tracer.SeedType.Point2 = [-1.10, 0.30, 0.0]
    tracer.SeedType.Resolution = 30
    UpdatePipeline(proxy=tracer)
    tracer_display = Show(tracer, view)
    tracer_display.LineWidth = 2.0
    ColorBy(tracer_display, ("POINTS", "Velocity", "Magnitude"))
    lut = GetColorTransferFunction("Velocity")
    lut.RescaleTransferFunction(0.0, 45.0)
    tracer_display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("pass5_streamlines.png", view)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: render_gpu_pyfr_pass5_paraview.py [velocity|pressure|mesh|streamlines]")
    mode = sys.argv[1]
    if mode == "velocity":
        render_velocity()
    elif mode == "pressure":
        render_pressure()
    elif mode == "mesh":
        render_mesh()
    elif mode == "streamlines":
        render_streamline()
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
