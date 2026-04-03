#!/usr/bin/env python3
"""Normalize the allowed NASA hump experimental wall data into local CSV files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "experimental" / "NASA_hump"
OUT_DIR = RAW_DIR


def load_numeric_table(path: Path, expected_cols: int) -> np.ndarray:
    rows: list[list[float]] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("variables"):
            continue
        parts = stripped.replace(",", " ").split()
        rows.append([float(value) for value in parts[:expected_cols]])
    return np.asarray(rows, dtype=float)


def write_csv(path: Path, header: list[str], data: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(data.tolist())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cp_raw = load_numeric_table(RAW_DIR / "noflow_cp.dat", expected_cols=2)
    cf_raw = load_numeric_table(RAW_DIR / "noflow_cf.dat", expected_cols=3)

    cp_csv = OUT_DIR / "noflow_cp.csv"
    cf_csv = OUT_DIR / "noflow_cf.csv"
    write_csv(cp_csv, ["x_over_c", "Cp"], cp_raw)
    write_csv(cf_csv, ["x_over_c", "Cf", "Cf_uncertainty"], cf_raw)

    summary = {
        "source_files": {
            "cp": "data/experimental/NASA_hump/noflow_cp.dat",
            "cf": "data/experimental/NASA_hump/noflow_cf.dat",
        },
        "normalized_files": {
            "cp": str(cp_csv.relative_to(ROOT)),
            "cf": str(cf_csv.relative_to(ROOT)),
        },
        "row_counts": {
            "cp": int(cp_raw.shape[0]),
            "cf": int(cf_raw.shape[0]),
        },
        "notes": [
            "Data copied only from the allowed NASA hump experimental-data resource.",
            "No tracing, digitization, or image-based extraction was used.",
            "Cp and Cf are preserved in machine-readable form for pass-four comparison plots.",
        ],
    }
    (OUT_DIR / "experimental_data_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
