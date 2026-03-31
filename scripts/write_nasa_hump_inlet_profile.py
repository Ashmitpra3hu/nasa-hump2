#!/usr/bin/env python3
"""Write physically motivated inlet profiles for the reconstructed NASA hump case."""

from __future__ import annotations

import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / os.environ.get("NASA_HUMP_CASE_DIR", "data/NASA_2DWMH")
U_PATH = CASE_DIR / "0" / "U"
K_PATH = CASE_DIR / "0" / "k"
OMEGA_PATH = CASE_DIR / "0" / "omega"


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return default if value is None else float(value)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return default if value is None else int(value)


def read_text(path: Path) -> str:
    return path.read_text()


def replace_block(text: str, start_marker: str, end_marker: str, new_block: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + new_block + text[end:]


def format_scalar_list(values: list[float]) -> str:
    rows = "\n".join(f"            {value:.10g}" for value in values)
    return f"""nonuniform List<scalar>
        {len(values)}
        (
{rows}
        )"""


def format_vector_list(values: list[tuple[float, float, float]]) -> str:
    rows = "\n".join(f"            ({u:.10g} {v:.10g} {w:.10g})" for u, v, w in values)
    return f"""nonuniform List<vector>
        {len(values)}
        (
{rows}
        )"""


def patch_block(field_name: str, value_text: str, inlet_type: str = "fixedValue") -> str:
    return f"""    inlet
    {{
        type            {inlet_type};
        value           {value_text};
    }}

"""


def main() -> None:
    mode = os.environ.get("NASA_HUMP_INLET_MODE", "uniform").strip().lower()
    u_inf = env_float("NASA_HUMP_U_INF", 34.6)
    top_z = env_float("NASA_HUMP_TOP_Z", 0.35)
    y_cells = env_int("NASA_HUMP_Y_CELLS", 220)

    u_text = read_text(U_PATH)
    k_text = read_text(K_PATH)
    omega_text = read_text(OMEGA_PATH)

    if mode == "uniform":
        u_block = patch_block("U", f"uniform ({u_inf:.10g} 0 0)")
        k_block = patch_block("k", f"uniform {env_float('NASA_HUMP_K_UNIFORM', 0.179574):.10g}")
        omega_block = patch_block("omega", f"uniform {env_float('NASA_HUMP_OMEGA_UNIFORM', 316.0):.10g}")
    elif mode == "tbl":
        delta = env_float("NASA_HUMP_INLET_DELTA", 0.028)
        power = env_float("NASA_HUMP_INLET_POWER", 7.0)
        ti_edge = env_float("NASA_HUMP_INLET_TI_EDGE", 0.005)
        ti_peak = env_float("NASA_HUMP_INLET_TI_PEAK", 0.085)
        delta99_scale = env_float("NASA_HUMP_INLET_DELTA99_SCALE", 1.0)
        ell_outer = env_float("NASA_HUMP_INLET_LENGTH_SCALE", 0.07)
        cmu_quarter = 0.09 ** 0.25

        dy = top_z / y_cells
        y_faces = [(i + 0.5) * dy for i in range(y_cells)]
        vectors: list[tuple[float, float, float]] = []
        k_values: list[float] = []
        omega_values: list[float] = []

        for y in y_faces:
            eta = min(max(y / max(delta * delta99_scale, 1e-8), 0.0), 4.0)
            if eta < 1.0:
                u_ratio = eta ** (1.0 / power)
                ti = ti_edge + (ti_peak - ti_edge) * (1.0 - eta) ** 2
            else:
                u_ratio = 1.0
                ti = ti_edge

            u_val = u_inf * min(max(u_ratio, 0.0), 1.0)
            k_val = max(1.0e-8, 1.5 * (max(u_val, 0.1) * ti) ** 2)
            mixing_length = max(min(0.41 * max(y, 1.0e-6), ell_outer * delta), 1.0e-5)
            omega_val = max(1.0, math.sqrt(k_val) / (cmu_quarter * mixing_length))

            vectors.append((u_val, 0.0, 0.0))
            k_values.append(k_val)
            omega_values.append(omega_val)

        u_block = patch_block("U", format_vector_list(vectors))
        k_block = patch_block("k", format_scalar_list(k_values))
        omega_block = patch_block("omega", format_scalar_list(omega_values))
    else:
        raise ValueError(f"Unsupported NASA_HUMP_INLET_MODE '{mode}'")

    U_PATH.write_text(replace_block(u_text, "    inlet\n", "    outlet\n", u_block))
    K_PATH.write_text(replace_block(k_text, "    inlet\n", "    outlet\n", k_block))
    OMEGA_PATH.write_text(replace_block(omega_text, "    inlet\n", "    outlet\n", omega_block))


if __name__ == "__main__":
    main()
