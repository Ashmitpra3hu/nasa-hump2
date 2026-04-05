#!/usr/bin/env python3
"""Rewrite key numerical-control files for NASA hump experiment variants."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / os.environ.get("NASA_HUMP_CASE_DIR", "data/NASA_2DWMH")


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return default if value is None else float(value)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return default if value is None else int(value)


def write(path: Path, text: str) -> None:
    path.write_text(text)


def main() -> None:
    model = os.environ.get("NASA_HUMP_MODEL", "kOmegaSST").strip()
    scheme_mode = os.environ.get("NASA_HUMP_SCHEME_MODE", "stable").strip().lower()
    start_from = os.environ.get("NASA_HUMP_START_FROM", "startTime").strip()
    end_time = env_int("NASA_HUMP_END_TIME", 300)
    write_interval = env_int("NASA_HUMP_WRITE_INTERVAL", 50)
    grad_limit = env_float("NASA_HUMP_GRAD_LIMIT", 1.0)
    relax_p = env_float("NASA_HUMP_RELAX_P", 0.3)
    relax_ukw = env_float("NASA_HUMP_RELAX_UKW", 0.7)
    p_rel_tol = env_float("NASA_HUMP_P_RELTOL", 0.01)
    ukw_rel_tol = env_float("NASA_HUMP_UKW_RELTOL", 0.05)
    non_orth = env_int("NASA_HUMP_NON_ORTH", 1)
    ml_correction = os.environ.get("NASA_HUMP_ML_CORRECTION", "true").strip().lower() in {"1", "true", "yes", "on"}
    ml_amplitude = env_float("NASA_HUMP_ML_AMPLITUDE", 0.0)
    ml_factor_min = env_float("NASA_HUMP_ML_FACTOR_MIN", 0.85)
    ml_factor_max = env_float("NASA_HUMP_ML_FACTOR_MAX", 1.60)
    ml_chi0 = env_float("NASA_HUMP_ML_CHI0", 3.0)
    ml_chi_width = env_float("NASA_HUMP_ML_CHI_WIDTH", 1.0)
    ml_y_peak = env_float("NASA_HUMP_ML_Y_PEAK", 0.015)
    ml_y_width = env_float("NASA_HUMP_ML_Y_WIDTH", 0.010)

    if scheme_mode == "stable":
        k_div = "bounded Gauss upwind"
        omega_div = "bounded Gauss upwind"
    elif scheme_mode == "sharper":
        k_div = "bounded Gauss linearUpwind grad(k)"
        omega_div = "bounded Gauss linearUpwind grad(omega)"
    else:
        raise ValueError(f"Unsupported NASA_HUMP_SCHEME_MODE '{scheme_mode}'")

    coeff_block = ""
    if model == "kOmegaSSTML":
        coeff_block = f"""
kOmegaSSTMLCoeffs
{{
    mlCorrection    {'on' if ml_correction else 'off'};
    amplitude       {ml_amplitude:.10g};
    factorMin       {ml_factor_min:.10g};
    factorMax       {ml_factor_max:.10g};
    chi0            {ml_chi0:.10g};
    chiWidth        {ml_chi_width:.10g};
    yPeak           {ml_y_peak:.10g};
    yWidth          {ml_y_width:.10g};
}}
"""

    turbulence_text = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    location    "constant";
    object      turbulenceProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  RAS;

RAS
{{
    RASModel        {model};
    turbulence      on;
    printCoeffs     on;
}}{coeff_block}

// ************************************************************************* //
"""

    libs_block = ""
    if model == "kOmegaSSTML":
        libs_block = """
libs
(
    "libmlHumpTurbulenceModels.so"
);
"""

    control_text = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     simpleFoam;

startFrom       {start_from};

startTime       0;

stopAt          endTime;

endTime         {end_time};

deltaT          1;

writeControl    timeStep;

writeInterval   {write_interval};

purgeWrite      0;

writeFormat     ascii;

writePrecision  12;

writeCompression uncompressed;

timeFormat      general;

timePrecision   6;

runTimeModifiable yes;

{libs_block}

functions
{{
    #includeFunc singleGraph_xm214
    #includeFunc singleGraph_x065
    #includeFunc singleGraph_x080
    #includeFunc singleGraph_x090
    #includeFunc singleGraph_x100
    #includeFunc singleGraph_x110
    #includeFunc singleGraph_x120
    #includeFunc singleGraph_x130
}}

// ************************************************************************* //
"""

    schemes_text = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      fvSchemes;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

ddtSchemes
{{
    default         steadyState;
}}

gradSchemes
{{
    default         cellLimited Gauss linear {grad_limit:g};
}}

divSchemes
{{
    default                         none;
    div(phi,U)                      bounded Gauss linearUpwind grad(U);
    div(phi,k)                      {k_div};
    div(phi,omega)                  {omega_div};
    div((nuEff*dev2(T(grad(U)))))   Gauss linear;
}}

laplacianSchemes
{{
    default         Gauss linear corrected;
}}

interpolationSchemes
{{
    default         linear;
}}

snGradSchemes
{{
    default         corrected;
}}

wallDist
{{
    method          meshWave;
}}

fluxRequired
{{
    default         no;
    p               ;
}}

// ************************************************************************* //
"""

    solution_text = f"""/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      fvSolution;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{{
    p
    {{
        solver          GAMG;
        tolerance       1e-9;
        relTol          {p_rel_tol:g};
        smoother        DICGaussSeidel;
        nPreSweeps      1;
        nPostSweeps     2;
        cacheAgglomeration true;
        agglomerator    faceAreaPair;
        nCellsInCoarsestLevel 20;
        mergeLevels     1;
    }}

    "(U|k|omega|nuTilda)"
    {{
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          {ukw_rel_tol:g};
        nSweeps         1;
    }}
}}

SIMPLE
{{
    nNonOrthogonalCorrectors {non_orth};
    consistent      yes;
    pRefCell        0;
    pRefValue       0;

    residualControl
    {{
        p           1e-5;
        U           1e-6;
        k           1e-6;
        omega       1e-6;
        nuTilda     1e-6;
    }}
}}

relaxationFactors
{{
    fields
    {{
        p           {relax_p:g};
    }}
    equations
    {{
        U           {relax_ukw:g};
        k           {relax_ukw:g};
        omega       {relax_ukw:g};
        nuTilda     {relax_ukw:g};
    }}
}}

// ************************************************************************* //
"""

    write(CASE_DIR / "constant" / "turbulenceProperties", turbulence_text)
    write(CASE_DIR / "system" / "controlDict", control_text)
    write(CASE_DIR / "system" / "fvSchemes", schemes_text)
    write(CASE_DIR / "system" / "fvSolution", solution_text)


if __name__ == "__main__":
    main()
