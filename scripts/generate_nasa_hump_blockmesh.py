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
Y_GRADING = env_float("NASA_HUMP_Y_GRADING", 18.0)

if len(X_SPLITS) != 4:
    raise ValueError(f"Expected 4 NASA_HUMP_X_SPLITS entries, found {len(X_SPLITS)}")

if len(X_CELLS) != 3:
    raise ValueError(f"Expected 3 NASA_HUMP_X_CELLS entries, found {len(X_CELLS)}")


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
    ({X_SPLITS[0]:.9f} {hump_height(X_SPLITS[0]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[1]:.9f} {hump_height(X_SPLITS[1]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[2]:.9f} {hump_height(X_SPLITS[2]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[3]:.9f} {hump_height(X_SPLITS[3]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[0]:.9f} {top_height(X_SPLITS[0]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[1]:.9f} {top_height(X_SPLITS[1]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[2]:.9f} {top_height(X_SPLITS[2]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[3]:.9f} {top_height(X_SPLITS[3]):.9f} {-THICKNESS / 2:.9f})
    ({X_SPLITS[0]:.9f} {hump_height(X_SPLITS[0]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[1]:.9f} {hump_height(X_SPLITS[1]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[2]:.9f} {hump_height(X_SPLITS[2]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[3]:.9f} {hump_height(X_SPLITS[3]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[0]:.9f} {top_height(X_SPLITS[0]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[1]:.9f} {top_height(X_SPLITS[1]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[2]:.9f} {top_height(X_SPLITS[2]):.9f} {THICKNESS / 2:.9f})
    ({X_SPLITS[3]:.9f} {top_height(X_SPLITS[3]):.9f} {THICKNESS / 2:.9f})
);

blocks
(
    hex (0 1 5 4 8 9 13 12) ({X_CELLS[0]} {Y_CELLS} 1) simpleGrading (1 {Y_GRADING:g} 1)
    hex (1 2 6 5 9 10 14 13) ({X_CELLS[1]} {Y_CELLS} 1) simpleGrading (1 {Y_GRADING:g} 1)
    hex (2 3 7 6 10 11 15 14) ({X_CELLS[2]} {Y_CELLS} 1) simpleGrading (1 {Y_GRADING:g} 1)
);

edges
(
    spline 1 2
    (
{format_bottom_points(X_SPLITS[1], X_SPLITS[2], -1.0)}
    )
    spline 9 10
    (
{format_bottom_points(X_SPLITS[1], X_SPLITS[2], 1.0)}
    )
    spline 4 5
    (
{format_top_points(X_SPLITS[0], X_SPLITS[1], -1.0)}
    )
    spline 5 6
    (
{format_top_points(X_SPLITS[1], X_SPLITS[2], -1.0)}
    )
    spline 6 7
    (
{format_top_points(X_SPLITS[2], X_SPLITS[3], -1.0)}
    )
    spline 12 13
    (
{format_top_points(X_SPLITS[0], X_SPLITS[1], 1.0)}
    )
    spline 13 14
    (
{format_top_points(X_SPLITS[1], X_SPLITS[2], 1.0)}
    )
    spline 14 15
    (
{format_top_points(X_SPLITS[2], X_SPLITS[3], 1.0)}
    )
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 8 12 4)
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            (3 7 15 11)
        );
    }}
    bottomWall
    {{
        type wall;
        faces
        (
            (0 1 9 8)
            (1 2 10 9)
            (2 3 11 10)
        );
    }}
    topWall
    {{
        type wall;
        faces
        (
            (4 12 13 5)
            (5 13 14 6)
            (6 14 15 7)
        );
    }}
    frontAndBack
    {{
        type empty;
        faces
        (
            (0 4 5 1)
            (1 5 6 2)
            (2 6 7 3)
            (8 9 13 12)
            (9 10 14 13)
            (10 11 15 14)
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
xCells      ({X_CELLS[0]} {X_CELLS[1]} {X_CELLS[2]});
yGrading    {Y_GRADING};
"""

(CASE_DIR / "caseDef").write_text(case_def)
