#!/usr/bin/env python3
"""Generate a reproducible blockMeshDict for the reconstructed NASA hump case."""

from __future__ import annotations

import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / os.environ.get("NASA_HUMP_CASE_DIR", "data/NASA_2DWMH")
OUTFILE = CASE_DIR / "system" / "blockMeshDict"


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return default if value is None else float(value)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return default if value is None else int(value)


def env_float_list(name: str, default: list[float]) -> list[float]:
    value = os.environ.get(name)
    if value is None:
        return default
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def env_int_list(name: str, default: list[int]) -> list[int]:
    value = os.environ.get(name)
    if value is None:
        return default
    return [int(item.strip()) for item in value.split(",") if item.strip()]


X_MIN = env_float("NASA_HUMP_X_MIN", -1.35)
X_MAX = env_float("NASA_HUMP_X_MAX", 0.84)
TOP_Z = env_float("NASA_HUMP_TOP_Z", 0.35)
THICKNESS = env_float("NASA_HUMP_THICKNESS", 0.02)
CHORD = env_float("NASA_HUMP_CHORD", 0.42)
HUMP_START = 0.0
HUMP_END = HUMP_START + CHORD
HUMP_HEIGHT = env_float("NASA_HUMP_HEIGHT", 0.053)
N_SPLINE = env_int("NASA_HUMP_N_SPLINE", 161)
TOP_CONTOUR_START = env_float("NASA_HUMP_TOP_CONTOUR_START", -0.25)
TOP_CONTOUR_END = env_float("NASA_HUMP_TOP_CONTOUR_END", 0.65)
TOP_CONTOUR_DIP = env_float("NASA_HUMP_TOP_CONTOUR_DIP", 0.02)

X_SPLITS = env_float_list("NASA_HUMP_X_SPLITS", [X_MIN, HUMP_START, HUMP_END, X_MAX])
Y_CELLS = env_int("NASA_HUMP_Y_CELLS", 220)
X_CELLS = env_int_list("NASA_HUMP_X_CELLS", [280, 320, 220])
X_GRADING = env_float_list("NASA_HUMP_X_GRADING", [1.0] * (len(X_SPLITS) - 1))
Y_GRADING = env_float("NASA_HUMP_Y_GRADING", 18.0)

if len(X_SPLITS) < 2:
    raise ValueError(f"Expected at least 2 NASA_HUMP_X_SPLITS entries, found {len(X_SPLITS)}")
if any(x1 <= x0 for x0, x1 in zip(X_SPLITS[:-1], X_SPLITS[1:])):
    raise ValueError("NASA_HUMP_X_SPLITS must be strictly increasing")
if len(X_CELLS) != len(X_SPLITS) - 1:
    raise ValueError(f"Expected {len(X_SPLITS) - 1} NASA_HUMP_X_CELLS entries, found {len(X_CELLS)}")
if len(X_GRADING) != len(X_SPLITS) - 1:
    raise ValueError(f"Expected {len(X_SPLITS) - 1} NASA_HUMP_X_GRADING entries, found {len(X_GRADING)}")


def hump_height(x: float) -> float:
    """Smooth cosine-squared hump with zero slope at both ends."""
    if x <= HUMP_START or x >= HUMP_END:
        return 0.0
    xi = (x - HUMP_START) / CHORD
    return HUMP_HEIGHT * math.sin(math.pi * xi) ** 2


def top_height(x: float) -> float:
    """Mild ceiling contour to reflect the webpage's blockage-guidance note."""
    if x <= TOP_CONTOUR_START or x >= TOP_CONTOUR_END:
        return TOP_Z
    xi = (x - TOP_CONTOUR_START) / (TOP_CONTOUR_END - TOP_CONTOUR_START)
    return TOP_Z - TOP_CONTOUR_DIP * math.sin(math.pi * xi) ** 2


def format_bottom_points(x0: float, x1: float, z_sign: float) -> str:
    lines = []
    for i in range(N_SPLINE):
        x = x0 + (x1 - x0) * i / (N_SPLINE - 1)
        y = hump_height(x)
        lines.append(f"        ({x:.9f} {y:.9f} {z_sign * THICKNESS / 2:.9f})")
    return "\n".join(lines)


def format_top_points(x0: float, x1: float, z_sign: float) -> str:
    lines = []
    for i in range(N_SPLINE):
        x = x0 + (x1 - x0) * i / (N_SPLINE - 1)
        y = top_height(x)
        lines.append(f"        ({x:.9f} {y:.9f} {z_sign * THICKNESS / 2:.9f})")
    return "\n".join(lines)


num_x = len(X_SPLITS)
lower_bottom = list(range(0, num_x))
lower_top = list(range(num_x, 2 * num_x))
upper_bottom = list(range(2 * num_x, 3 * num_x))
upper_top = list(range(3 * num_x, 4 * num_x))


def vertex_lines() -> list[str]:
    lines: list[str] = []
    for z_sign in (-1.0, 1.0):
        z_val = z_sign * THICKNESS / 2.0
        for x in X_SPLITS:
            lines.append(f"    ({x:.9f} {hump_height(x):.9f} {z_val:.9f})")
        for x in X_SPLITS:
            lines.append(f"    ({x:.9f} {top_height(x):.9f} {z_val:.9f})")
    return lines


def block_lines() -> list[str]:
    lines: list[str] = []
    for i, (n_cells, x_grad) in enumerate(zip(X_CELLS, X_GRADING)):
        lines.append(
            "    "
            f"hex ({lower_bottom[i]} {lower_bottom[i + 1]} {lower_top[i + 1]} {lower_top[i]} "
            f"{upper_bottom[i]} {upper_bottom[i + 1]} {upper_top[i + 1]} {upper_top[i]}) "
            f"({n_cells} {Y_CELLS} 1) simpleGrading ({x_grad:g} {Y_GRADING:g} 1)"
        )
    return lines


def edge_lines() -> list[str]:
    lines: list[str] = []
    for i in range(len(X_SPLITS) - 1):
        lines.extend(
            [
                f"    spline {lower_bottom[i]} {lower_bottom[i + 1]}",
                "    (",
                format_bottom_points(X_SPLITS[i], X_SPLITS[i + 1], -1.0),
                "    )",
                f"    spline {upper_bottom[i]} {upper_bottom[i + 1]}",
                "    (",
                format_bottom_points(X_SPLITS[i], X_SPLITS[i + 1], 1.0),
                "    )",
                f"    spline {lower_top[i]} {lower_top[i + 1]}",
                "    (",
                format_top_points(X_SPLITS[i], X_SPLITS[i + 1], -1.0),
                "    )",
                f"    spline {upper_top[i]} {upper_top[i + 1]}",
                "    (",
                format_top_points(X_SPLITS[i], X_SPLITS[i + 1], 1.0),
                "    )",
            ]
        )
    return lines


def boundary_face_lines(face_builder) -> list[str]:
    return [f"            {face_builder(i)}" for i in range(len(X_SPLITS) - 1)]


content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Website:  https://openfoam.org                  |
|   \\\\  /    A nd           | Version:  7                                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

vertices
(
{chr(10).join(vertex_lines())}
);

blocks
(
{chr(10).join(block_lines())}
);

edges
(
{chr(10).join(edge_lines())}
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            ({lower_bottom[0]} {upper_bottom[0]} {upper_top[0]} {lower_top[0]})
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            ({lower_bottom[-1]} {lower_top[-1]} {upper_top[-1]} {upper_bottom[-1]})
        );
    }}
    bottomWall
    {{
        type wall;
        faces
        (
{chr(10).join(boundary_face_lines(lambda i: f'({lower_bottom[i]} {lower_bottom[i + 1]} {upper_bottom[i + 1]} {upper_bottom[i]})'))}
        );
    }}
    topWall
    {{
        type wall;
        faces
        (
{chr(10).join(boundary_face_lines(lambda i: f'({lower_top[i]} {upper_top[i]} {upper_top[i + 1]} {lower_top[i + 1]})'))}
        );
    }}
    frontAndBack
    {{
        type empty;
        faces
        (
{chr(10).join(boundary_face_lines(lambda i: f'({lower_bottom[i]} {lower_top[i]} {lower_top[i + 1]} {lower_bottom[i + 1]})'))}
{chr(10).join(boundary_face_lines(lambda i: f'({upper_bottom[i]} {upper_bottom[i + 1]} {upper_top[i + 1]} {upper_top[i]})'))}
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""

OUTFILE.write_text(content)

case_def = f"""// Reconstructed NASA hump case definition
xMin        {X_MIN};
xMax         {X_MAX};
zTop         {TOP_Z};
thickness    {THICKNESS};
chord        {CHORD};
uInf         34.6;
rho          1.225;
Re           936000;
nu           1.5534188034188036e-05;
humpHeight   {HUMP_HEIGHT};
profileZMax  {TOP_Z};
topContourStart {TOP_CONTOUR_START};
topContourEnd   {TOP_CONTOUR_END};
topContourDip   {TOP_CONTOUR_DIP};
yCells      {Y_CELLS};
xSplits     ({' '.join(f'{x:.9f}' for x in X_SPLITS)});
xCells      ({' '.join(str(x) for x in X_CELLS)});
xGrading    ({' '.join(f'{x:g}' for x in X_GRADING)});
yGrading    {Y_GRADING};
"""

(CASE_DIR / "caseDef").write_text(case_def)
