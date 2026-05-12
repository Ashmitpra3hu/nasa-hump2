#!/usr/bin/env python3
"""Summarize the first successful PASS 3 PyFR hump GPU run."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "gpu_pyfr_pass3" / "minimal"
OUT_DATA = ROOT / "documentation_src" / "data_gpu_pyfr_pass3"
OUT_FIG = ROOT / "documentation_src" / "figures_gpu_pyfr_pass3"


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def parse_slurm_out(path: Path) -> dict[str, str | None]:
    details: dict[str, str | None] = {
        "hostname": None,
        "start_line": None,
        "gpu_line": None,
        "python_version": None,
        "pyfr_version": None,
    }
    if not path.exists():
        return details

    lines = path.read_text(errors="ignore").splitlines()
    for idx, line in enumerate(lines):
        if idx == 0:
            details["hostname"] = line.strip() or None
        elif idx == 1:
            details["start_line"] = line.strip() or None
        if "NVIDIA A100" in line and details["gpu_line"] is None:
            details["gpu_line"] = line.strip()
        if line.startswith("Python "):
            details["python_version"] = line.strip()
        if line.startswith("pyfr "):
            details["pyfr_version"] = line.strip()
    return details


def build_status() -> dict[str, object]:
    status = {
        "case": "pass3_minimal",
        "status": "completed" if (RUN_DIR / "pass3_minimal_latest.vtu").exists() else "missing_outputs",
        "job_id": "10702409",
        "partition": "a100-40gb",
        "walltime": "00:05:00",
        "notes": "First successful no-sampler PyFR NASA hump GPU execution on Gilbreth.",
    }
    status |= parse_slurm_out(RUN_DIR / "slurm-10702409.out")
    return status


def plot_pseudostats() -> dict[str, object]:
    path = RUN_DIR / "pseudo_stats.csv"
    meta: dict[str, object] = {"pseudo_rows": 0, "pseudo_final_time": None, "finite_rows": 0}

    if not path.exists():
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No pseudo_stats.csv found for PASS 3.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / "pass3_pseudo_stats.png", dpi=220)
        plt.close(fig)
        return meta

    rows = load_csv(path)
    meta["pseudo_rows"] = len(rows)
    t = []
    p = []
    u = []
    v = []
    for row in rows:
        try:
            tval = float(row["t"])
        except Exception:
            continue
        t.append(tval)
        for dest, key in ((p, "p"), (u, "u"), (v, "v")):
            value = row.get(key, "-")
            dest.append(np.nan if value in {"-", "nan", "NaN"} else float(value))

    if t:
        meta["pseudo_final_time"] = max(t)
    finite_mask = np.isfinite(np.array(p, dtype=float)) | np.isfinite(np.array(u, dtype=float)) | np.isfinite(np.array(v, dtype=float))
    meta["finite_rows"] = int(np.count_nonzero(finite_mask))

    fig, ax = plt.subplots(figsize=(10, 4))
    if t:
        arr_t = np.array(t, dtype=float)
        for series, label in ((p, "p"), (u, "u"), (v, "v")):
            arr = np.array(series, dtype=float)
            good = np.isfinite(arr)
            if np.any(good):
                ax.semilogy(arr_t[good], arr[good], marker="o", label=label)
    ax.set_xlabel("physical time")
    ax.set_ylabel("pseudo residual")
    ax.set_title("PASS 3 pseudo-stat history")
    ax.grid(True, alpha=0.3)
    if ax.lines:
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pass3_pseudo_stats.png", dpi=220)
    plt.close(fig)
    return meta


def write_summary_table(summary: dict[str, object]) -> None:
    rows = [
        ("Run name", summary["case"]),
        ("Status", summary["status"]),
        ("Job ID", summary["job_id"]),
        ("Partition", summary["partition"]),
        ("Hostname", summary.get("hostname", "n/a")),
        ("GPU line", summary.get("gpu_line", "n/a")),
        ("Python", summary.get("python_version", "n/a")),
        ("PyFR", summary.get("pyfr_version", "n/a")),
        ("Pseudo rows", summary.get("pseudo_rows", 0)),
        ("Finite pseudo rows", summary.get("finite_rows", 0)),
        ("Final pseudo time", summary.get("pseudo_final_time", "n/a")),
        ("VTU export", "present" if (RUN_DIR / "pass3_minimal_latest.vtu").exists() else "missing"),
    ]
    with (OUT_DATA / "summary_table.tex").open("w") as handle:
        handle.write("\\begin{tabular}{ll}\n\\toprule\nMetric & Value\\\\\n\\midrule\n")
        for key, value in rows:
            safe = str(value).replace("_", "\\_")
            handle.write(f"{key} & {safe}\\\\\n")
        handle.write("\\bottomrule\n\\end{tabular}\n")


def main() -> None:
    ensure_dirs()
    summary = build_status()
    summary |= plot_pseudostats()
    (RUN_DIR / "status.json").write_text(json.dumps(summary, indent=2))
    (OUT_DATA / "gpu_pyfr_pass3_summary.json").write_text(json.dumps(summary, indent=2))
    with (OUT_DATA / "gpu_pyfr_pass3_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)
    write_summary_table(summary)


if __name__ == "__main__":
    main()
