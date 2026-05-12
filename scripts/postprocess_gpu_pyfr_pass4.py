#!/usr/bin/env python3
"""Postprocess PASS 4 PyFR results and build the first external Cp comparison package."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "gpu_pyfr_pass4" / "long"
OUT_ROOT = ROOT / "documentation_src" / "gpu_pyfr_pass4"
OUT_DATA = OUT_ROOT / "data"
OUT_FIG = OUT_ROOT / "figures"
OUT_PV = OUT_ROOT / "paraview"
EXP_CP = ROOT / "data" / "experimental" / "NASA_hump" / "noflow_cp.csv"
PV_PYTHON = Path("/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython")


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    OUT_PV.mkdir(parents=True, exist_ok=True)


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


def plot_pseudostats() -> dict[str, object]:
    path = RUN_DIR / "pseudo_stats.csv"
    meta: dict[str, object] = {"pseudo_rows": 0, "pseudo_final_time": None, "finite_rows": 0}

    if not path.exists():
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No pseudo_stats.csv found for PASS 4.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / "pyfr_pass4_pseudo_stats.png", dpi=220)
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
    ax.set_title("PASS 4 pseudo-stat history")
    ax.grid(True, alpha=0.3)
    if ax.lines:
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pyfr_pass4_pseudo_stats.png", dpi=220)
    plt.close(fig)
    return meta


def build_summary() -> dict[str, object]:
    summary = {
        "case": "pass4_long",
        "status": "completed" if (RUN_DIR / "pass4_long_latest.vtu").exists() else "missing_outputs",
        "job_id": "unknown",
        "partition": "a100-40gb",
        "notes": "Longer no-sampler PASS 4 PyFR run used for external wall-pressure extraction.",
    }
    slurm_outs = sorted(RUN_DIR.glob("slurm-*.out"))
    if slurm_outs:
        summary["job_id"] = slurm_outs[-1].stem.split("-")[-1]
        summary |= parse_slurm_out(slurm_outs[-1])
    summary |= plot_pseudostats()
    return summary


def run_wall_extraction() -> dict[str, object]:
    vtu_path = RUN_DIR / "pass4_long_latest.vtu"
    raw_csv = OUT_DATA / "pyfr_wall_pressure_raw.csv"
    cmp_csv = OUT_DATA / "pyfr_cp_comparison.csv"
    cmp_json = cmp_csv.with_suffix(".json")
    if not vtu_path.exists():
        return {"cp_available": False, "notes": "VTU export missing, so external wall-pressure extraction could not run."}

    if raw_csv.exists() and cmp_csv.exists() and cmp_json.exists():
        summary = json.loads(cmp_json.read_text())
        summary["cp_available"] = bool(summary.get("finite_cp_matches", 0)) and np.isfinite(summary.get("cp_mae", np.nan))
        if not summary["cp_available"]:
            summary["notes"] = "PASS 4 wall-pressure extraction ran, but the exported field did not contain enough finite wall pressure values for a defensible Cp comparison."
        return summary

    if not PV_PYTHON.exists():
        return {"cp_available": False, "notes": "pvpython was not found locally, so VTK-based wall-pressure extraction could not run."}

    subprocess.run(
        [
            str(PV_PYTHON),
            str(ROOT / "scripts" / "pyfr" / "extract_gpu_pyfr_pass4_wall_data.py"),
            str(vtu_path),
            str(EXP_CP),
            str(raw_csv),
            str(cmp_csv),
        ],
        check=True,
    )
    summary = json.loads(cmp_json.read_text())
    summary["cp_available"] = bool(summary.get("finite_cp_matches", 0)) and np.isfinite(summary.get("cp_mae", np.nan))
    if not summary["cp_available"]:
        summary["notes"] = "PASS 4 wall-pressure extraction ran, but the exported field did not contain enough finite wall pressure values for a defensible Cp comparison."
    return summary


def plot_cp_comparison(cp_summary: dict[str, object]) -> dict[str, object]:
    cmp_csv = OUT_DATA / "pyfr_cp_comparison.csv"
    if not cmp_csv.exists():
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "PASS 4 Cp comparison was unavailable.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / "pyfr_cp_comparison.png", dpi=220)
        plt.close(fig)
        return cp_summary

    rows = load_csv(cmp_csv)
    x = np.array([float(r["x_over_c"]) for r in rows], dtype=float)
    cp_exp = np.array([float(r["Cp_exp"]) for r in rows], dtype=float)
    cp_pyfr = np.array([float(r["Cp_pyfr"]) for r in rows], dtype=float)
    dx = np.array([float(r["dx_over_c"]) for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, cp_exp, "o-", label="NASA experimental Cp", markersize=3.5)
    good = np.isfinite(cp_pyfr)
    if np.any(good):
        ax.plot(x[good], cp_pyfr[good], "s-", label="PyFR external wall Cp", markersize=3.0)
    else:
        ax.text(0.5, 0.5, "No finite PyFR wall Cp values were available in this exported field.", ha="center", va="center", transform=ax.transAxes)
    ax.set_xlabel("x/c")
    ax.set_ylabel("Cp")
    ax.set_title("PASS 4 PyFR Cp comparison against NASA data")
    ax.grid(True, alpha=0.3)
    if np.any(good):
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pyfr_cp_comparison.png", dpi=220)
    plt.close(fig)

    cp_summary["cp_dx_abs_max"] = float(np.max(np.abs(dx))) if len(dx) else None
    cp_summary["cp_dx_abs_mean"] = float(np.mean(np.abs(dx))) if len(dx) else None
    return cp_summary


def write_summary_table(summary: dict[str, object], cp_summary: dict[str, object]) -> None:
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
        ("VTU export", "present" if (RUN_DIR / "pass4_long_latest.vtu").exists() else "missing"),
        ("Cp available", cp_summary.get("cp_available", False)),
        ("Cp MAE", cp_summary.get("cp_mae", "unavailable")),
        ("Max |dx/c|", cp_summary.get("cp_dx_abs_max", "unavailable")),
        ("Cf available", "False"),
        ("Benchmark MAE available", "False"),
    ]
    with (OUT_DATA / "summary_table.tex").open("w") as handle:
        handle.write("\\begin{tabular}{ll}\n\\toprule\nMetric & Value\\\\\n\\midrule\n")
        for key, value in rows:
            safe = str(value).replace("_", "\\_")
            handle.write(f"{key} & {safe}\\\\\n")
        handle.write("\\bottomrule\n\\end{tabular}\n")


def main() -> None:
    ensure_dirs()
    summary = build_summary()
    cp_summary = run_wall_extraction()
    cp_summary = plot_cp_comparison(cp_summary)
    payload = {"summary": summary, "cp_summary": cp_summary}
    (OUT_DATA / "pyfr_pass4_summary.json").write_text(json.dumps(payload, indent=2))
    with (OUT_DATA / "pyfr_pass4_summary.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for section_name, section in payload.items():
            for key, value in section.items():
                writer.writerow([f"{section_name}.{key}", value])
    write_summary_table(summary, cp_summary)


if __name__ == "__main__":
    main()
