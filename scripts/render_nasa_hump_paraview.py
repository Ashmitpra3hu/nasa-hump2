#!/usr/bin/env python3
"""Render ParaView screenshots for the reconstructed NASA hump case."""

from pathlib import Path

from paraview.simple import *  # noqa: F401,F403


ROOT = Path(__file__).resolve().parents[1]
VTK_DIR = ROOT / "data" / "NASA_2DWMH" / "VTK" / "NASA_2DWMH_80"
FIG_DIR = ROOT / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def reset_view():
    view = GetActiveViewOrCreate("RenderView")
    view.ViewSize = [1800, 900]
    view.OrientationAxesVisibility = 0
    view.Background = [1.0, 1.0, 1.0]
    return view


def save(name: str, view):
    SaveScreenshot(str(FIG_DIR / name), view, ImageResolution=view.ViewSize)


def common_camera(view):
    view.CameraPosition = [-0.12, 0.17, 2.5]
    view.CameraFocalPoint = [-0.12, 0.17, 0.0]
    view.CameraViewUp = [0.0, 1.0, 0.0]
    view.CameraParallelScale = 0.42


def render_velocity():
    view = reset_view()
    reader = XMLUnstructuredGridReader(FileName=[str(VTK_DIR / "internal.vtu")])
    reader.CellArrayStatus = ["U", "p", "k", "omega", "nut"]
    c2p = CellDatatoPointData(Input=reader)
    display = Show(c2p, view)
    ColorBy(display, ("POINTS", "U", "Magnitude"))
    lut = GetColorTransferFunction("U")
    lut.RescaleTransferFunction(0.0, 40.0)
    display.SetScalarBarVisibility(view, True)
    common_camera(view)
    Render()
    save("paraview_velocity.png", view)
    Hide(c2p, view)
    Delete(c2p)
    Delete(reader)


def render_pressure():
    view = reset_view()
    reader = XMLUnstructuredGridReader(FileName=[str(VTK_DIR / "internal.vtu")])
    reader.CellArrayStatus = ["U", "p", "k", "omega", "nut"]
    c2p = CellDatatoPointData(Input=reader)
    display = Show(c2p, view)
    ColorBy(display, ("POINTS", "p"))
    lut = GetColorTransferFunction("p")
    lut.RescaleTransferFunction(-50.0, 250.0)
    display.SetScalarBarVisibility(view, True)
    common_camera(view)
    Render()
    save("paraview_pressure.png", view)
    Hide(c2p, view)
    Delete(c2p)
    Delete(reader)


def render_streamlines():
    view = reset_view()
    reader = XMLUnstructuredGridReader(FileName=[str(VTK_DIR / "internal.vtu")])
    reader.CellArrayStatus = ["U", "p", "k", "omega", "nut"]
    c2p = CellDatatoPointData(Input=reader)
    tracer = StreamTracer(Input=c2p, SeedType="Line")
    tracer.Vectors = ["POINTS", "U"]
    tracer.MaximumStreamlineLength = 1.6
    tracer.SeedType.Point1 = [-0.88, 0.02, 0.0]
    tracer.SeedType.Point2 = [-0.88, 0.30, 0.0]
    tracer.SeedType.Resolution = 36
    tracerDisplay = Show(tracer, view)
    ColorBy(tracerDisplay, ("POINTS", "U", "Magnitude"))
    lut = GetColorTransferFunction("U")
    lut.RescaleTransferFunction(0.0, 40.0)
    tracerDisplay.SetScalarBarVisibility(view, True)
    common_camera(view)
    Render()
    save("paraview_streamlines.png", view)
    Hide(tracer, view)
    Delete(tracer)
    Delete(c2p)
    Delete(reader)


def render_wall_shear():
    view = reset_view()
    reader = XMLPolyDataReader(FileName=[str(VTK_DIR / "boundary" / "bottomWall.vtp")])
    display = Show(reader, view)
    ColorBy(display, ("POINTS", "wallShearStress", "Magnitude"))
    lut = GetColorTransferFunction("wallShearStress")
    lut.RescaleTransferFunction(0.0, 8.0)
    display.SetScalarBarVisibility(view, True)
    common_camera(view)
    view.CameraParallelScale = 0.22
    Render()
    save("paraview_wall_shear.png", view)
    Hide(reader, view)
    Delete(reader)


def main():
    render_velocity()
    render_pressure()
    render_streamlines()
    render_wall_shear()


if __name__ == "__main__":
    main()
