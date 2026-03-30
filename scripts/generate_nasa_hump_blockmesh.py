#!/usr/bin/env python3
"""Generate a reproducible blockMeshDict for the reconstructed NASA hump case."""

from __future__ import annotations

import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "data" / "NASA_2DWMH"
OUTFILE = CASE_DIR / "system" / "blockMeshDict"


X_MIN = -0.90
X_MAX = 0.67
TOP_Z = 0.35
THICKNESS = 0.02
CHORD = 0.42
HUMP_START = 0.0
HUMP_END = HUMP_START + CHORD
HUMP_HEIGHT = 0.053
N_SPLINE = 161


def hump_height(x: float) -> float:
    """Smooth cosine-squared hump with zero slope at both ends."""
    if x <= HUMP_START or x >= HUMP_END:
        return 0.0
    xi = (x - HUMP_START) / CHORD
    return HUMP_HEIGHT * math.sin(math.pi * xi) ** 2


def format_points(z_sign: float) -> str:
    lines = []
    for i in range(N_SPLINE):
        x = X_MIN + (X_MAX - X_MIN) * i / (N_SPLINE - 1)
        z = hump_height(x)
        lines.append(f"        ({x:.9f} {z:.9f} {z_sign * THICKNESS / 2:.9f})")
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
    ({X_MIN:.9f} 0.000000000 {-THICKNESS / 2:.9f})
    ({X_MAX:.9f} 0.000000000 {-THICKNESS / 2:.9f})
    ({X_MAX:.9f} {TOP_Z:.9f} {-THICKNESS / 2:.9f})
    ({X_MIN:.9f} {TOP_Z:.9f} {-THICKNESS / 2:.9f})
    ({X_MIN:.9f} 0.000000000 {THICKNESS / 2:.9f})
    ({X_MAX:.9f} 0.000000000 {THICKNESS / 2:.9f})
    ({X_MAX:.9f} {TOP_Z:.9f} {THICKNESS / 2:.9f})
    ({X_MIN:.9f} {TOP_Z:.9f} {THICKNESS / 2:.9f})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (520 180 1) simpleGrading (3 12 1)
);

edges
(
    spline 0 1
    (
{format_points(-1.0)}
    )
    spline 4 5
    (
{format_points(1.0)}
    )
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    bottomWall
    {{
        type wall;
        faces
        (
            (0 1 5 4)
        );
    }}
    topWall
    {{
        type wall;
        faces
        (
            (3 7 6 2)
        );
    }}
    frontAndBack
    {{
        type empty;
        faces
        (
            (0 3 2 1)
            (4 5 6 7)
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""

OUTFILE.write_text(content)
