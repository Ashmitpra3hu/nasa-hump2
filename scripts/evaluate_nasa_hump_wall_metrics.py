#!/usr/bin/env python3
"""Evaluate NASA hump wall Cp/Cf agreement against the official experimental data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "data" / "experimental" / "NASA_hump"
CHORD = 0.42
U_REF = 34.6
RHO = 1.225
Q_REF = 0.5 * RHO * U_REF**2


def parse_internal_field(path: Path) -> np.ndarray:
    text = path.read_text().splitlines()
    start = None
    count = None
    for idx, line in enumerate(text):
        stripped = line.strip()
        if stripped.isdigit():
            count = int(stripped)
            start = idx + 2
            break
    if start is None or count is None:
        raise ValueError(f"Could not parse field size from {path}")

    rows = []
    for line in text[start:]:
        stripped = line.strip()
        if stripped in {")", ");"}:
            break
        if stripped.startswith("(") and stripped.endswith(")"):
            rows.append([float(val) for val in stripped[1:-1].split()])
        elif stripped:
            rows.append([float(stripped)])
    arr = np.asarray(rows, dtype=float)
    if arr.shape[0] != count:
        raise ValueError(f"Expected {count} rows in {path}, found {arr.shape[0]}")
    return arr


def parse_bottom_wall_shear(path: Path) -> np.ndarray:
    text = path.read_text().splitlines()
    start = None
    count = None
    for idx, line in enumerate(text):
        if line.strip() == "bottomWall":
            for j in range(idx, min(idx + 15, len(text))):
                stripped = text[j].strip()
                if stripped.isdigit():
                    count = int(stripped)
                    start = j + 2
                    break
            break
    if start is None or count is None:
        raise ValueError(f"Could not locate bottomWall data in {path}")
    rows = []
    for line in text[start:]:
        stripped = line.strip()
        if stripped in {")", ");"}:
            break
        if stripped.startswith("(") and stripped.endswith(")"):
            rows.append([float(val) for val in stripped[1:-1].split()])
    arr = np.asarray(rows, dtype=float)
    if arr.shape[0] != count:
        raise ValueError(f"Expected {count} vectors in {path}, found {arr.shape[0]}")
    return arr


def latest_numeric_dir(base: Path) -> Path:
    numeric_dirs = []
    for child in base.iterdir():
        if child.is_dir():
            try:
                numeric_dirs.append((float(child.name), child))
            except ValueError:
                continue
    if not numeric_dirs:
        raise FileNotFoundError(f"No numeric time directories found in {base}")
    return max(numeric_dirs, key=lambda item: item[0])[1]


def parse_case_def(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip().rstrip(";")
        if not stripped or stripped.startswith("//"):
            continue
        if stripped.startswith("xMin"):
            data["xMin"] = float(stripped.split()[-1])
        elif stripped.startswith("xMax"):
            data["xMax"] = float(stripped.split()[-1])
        elif stripped.startswith("chord"):
            data["chord"] = float(stripped.split()[-1])
        elif stripped.startswith("xCells"):
            values = stripped[stripped.index("(") + 1:stripped.index(")")].split()
            data["xCells"] = [int(v) for v in values]
    return data


def load_csv(path: Path, cols: int) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open() as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            rows.append([float(value) for value in row[:cols]])
    return np.asarray(rows, dtype=float)


def wall_series(case_dir: Path) -> dict[str, np.ndarray]:
    latest = latest_numeric_dir(case_dir)
    coords = parse_internal_field(case_dir / "0" / "C")
    p = parse_internal_field(latest / "p").ravel()
    tau = parse_bottom_wall_shear(latest / "wallShearStress")[:, 0]
    case_def = parse_case_def(case_dir / "caseDef")

    x_splits = np.array([float(case_def["xMin"]), 0.0, float(case_def["chord"]), float(case_def["xMax"])], dtype=float)
    x_cells = list(case_def["xCells"])
    x_centers = []
    for i, n_cells in enumerate(x_cells):
        edges = np.linspace(x_splits[i], x_splits[i + 1], n_cells + 1)
        x_centers.append(0.5 * (edges[:-1] + edges[1:]))
    x = np.concatenate(x_centers)
    if len(x) != len(tau):
        edges = np.linspace(float(np.min(coords[:, 0])), float(np.max(coords[:, 0])), len(tau) + 1)
        x = 0.5 * (edges[:-1] + edges[1:])

    p_wall = np.zeros(len(tau))
    for i in range(len(tau)):
        dx = max((x[1] - x[0]) * 1.5 if len(x) > 1 else 0.002, 0.002)
        mask = np.abs(coords[:, 0] - x[i]) <= dx
        local_coords = coords[mask]
        local_p = p[mask]
        if len(local_p) == 0:
            p_wall[i] = p_wall[i - 1] if i > 0 else p[0]
            continue
        min_y = float(local_coords[:, 1].min())
        near_wall = np.abs(local_coords[:, 1] - min_y) < 0.003
        p_wall[i] = float(local_p[near_wall].mean()) if np.any(near_wall) else float(local_p.mean())

    x_ref = -2.14 * CHORD
    ref_mask = (np.abs(coords[:, 0] - x_ref) < 0.01) & (coords[:, 1] > 0.04)
    if not np.any(ref_mask):
        ref_mask = np.abs(coords[:, 0] - x_ref) < 0.01
    p_ref = float(np.mean(p[ref_mask])) if np.any(ref_mask) else float(p[0])

    return {
        "x_over_c": x / CHORD,
        "Cp": (p_wall - p_ref) / Q_REF,
        "Cf": -tau / Q_REF,
    }


def evaluate(case_dir: Path) -> dict[str, object]:
    wall = wall_series(case_dir)
    cp_exp = load_csv(EXP_DIR / "noflow_cp.csv", 2)
    cf_exp = load_csv(EXP_DIR / "noflow_cf.csv", 3)

    cp_pred = np.interp(cp_exp[:, 0], wall["x_over_c"], wall["Cp"])
    cf_pred = np.interp(cf_exp[:, 0], wall["x_over_c"], wall["Cf"])

    cp_err = cp_pred - cp_exp[:, 1]
    cf_err = cf_pred - cf_exp[:, 1]

    return {
        "cp_rmse": float(np.sqrt(np.mean(cp_err**2))),
        "cp_mae": float(np.mean(np.abs(cp_err))),
        "cf_rmse": float(np.sqrt(np.mean(cf_err**2))),
        "cf_mae": float(np.mean(np.abs(cf_err))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    result = evaluate(args.case_dir.resolve())
    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
