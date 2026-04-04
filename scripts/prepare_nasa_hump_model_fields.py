#!/usr/bin/env python3
"""Prepare model-specific initial fields for the NASA hump case."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / os.environ.get("NASA_HUMP_CASE_DIR", "data/NASA_2DWMH")


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return default if value is None else float(value)


def write_spalart_allmaras_field() -> None:
    nu_tilda = env_float("NASA_HUMP_NUTILDA_INLET", 4.7e-5)
    text = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    class       volScalarField;
    location    "0";
    object      nuTilda;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -1 0 0 0 0];

internalField   uniform {nu_tilda:.10g};

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform {nu_tilda:.10g};
    }}
    outlet
    {{
        type            zeroGradient;
    }}
    bottomWall
    {{
        type            fixedValue;
        value           uniform 0;
    }}
    topWall
    {{
        type            zeroGradient;
    }}
    frontAndBack
    {{
        type            empty;
    }}
}}

// ************************************************************************* //
"""
    (CASE_DIR / "0" / "nuTilda").write_text(text)


def main() -> None:
    model = os.environ.get("NASA_HUMP_MODEL", "kOmegaSST").strip()
    if model == "SpalartAllmaras":
        write_spalart_allmaras_field()


if __name__ == "__main__":
    main()
