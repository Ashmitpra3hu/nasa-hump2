#!/usr/bin/env python3
"""Render ParaView screenshots from the successful PASS 3 PyFR VTU export."""

from __future__ import annotations

from pathlib import Path
import sys

from paraview.simple import *  # noqa: F401,F403


ROOT = Path(__file__).resolve().parents[1]
VTU_FILE = ROOT / "runs" / "gpu_pyfr_pass3" / "minimal" / "pass3_minimal_latest.vtu"
FIG_DIR = ROOT / "documentation_src" / "figures_gpu_pyfr_pass3"
FIG_DIR.mkdir(parents=True, exist_ok=True)


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
    src = XMLUnstructuredGridReader(FileName=[str(VTU_FILE)])
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
    save("pass3_velocity.png", view)


def render_pressure():
    view = make_view()
    src = reader()
    display = Show(src, view)
    display.Representation = "Surface"
    ColorBy(display, ("POINTS", "Pressure"))
    lut = GetColorTransferFunction("Pressure")
    lut.RescaleTransferFunction(-5.0, 5.0)
    display.SetScalarBarVisibility(view, True)
    set_camera(view, "full")
    Render()
    save("pass3_pressure.png", view)


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
    save("pass3_mesh.png", view)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: render_gpu_pyfr_pass3_paraview.py [velocity|pressure|mesh]")

    mode = sys.argv[1]
    if mode == "velocity":
        render_velocity()
    elif mode == "pressure":
        render_pressure()
    elif mode == "mesh":
        render_mesh()
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
