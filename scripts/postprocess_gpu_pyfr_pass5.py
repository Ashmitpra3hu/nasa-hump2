#!/usr/bin/env python3
"""Postprocess GPU PyFR PASS 5 results and produce audit/validation artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "documentation_src" / "gpu_pyfr_pass5"
OUT_DATA = OUT_ROOT / "data"
OUT_FIG = OUT_ROOT / "figures"
PASS4_DATA = ROOT / "documentation_src" / "gpu_pyfr_pass4" / "data"
PASS4_RUN = ROOT / "runs" / "gpu_pyfr_pass4" / "long"


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


def choose_run_dir() -> tuple[str, Path]:
    promoted = ROOT / "runs" / "gpu_pyfr_pass5" / "promoted"
    diagnostic = ROOT / "runs" / "gpu_pyfr_pass5" / "diagnostic"
    if (promoted / "pseudo_stats.csv").exists():
        return "promoted", promoted
    if (diagnostic / "pseudo_stats.csv").exists():
        return "diagnostic", diagnostic
    return "pass4_reused", PASS4_RUN


def summarize_pseudo_stats(run_dir: Path) -> dict[str, object]:
    path = run_dir / "pseudo_stats.csv"
    summary: dict[str, object] = {
        "pseudo_rows": 0,
        "finite_rows": 0,
        "nan_rows": 0,
        "first_nan_row": None,
        "pseudo_final_time": None,
    }

    fig, ax = plt.subplots(figsize=(10, 4))
    if not path.exists():
        ax.text(0.5, 0.5, "No pseudo_stats.csv found for PASS 5.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / "pseudo_stat_history.png", dpi=220)
        plt.close(fig)
        return summary

    rows = load_csv(path)
    summary["pseudo_rows"] = len(rows)
    times = []
    series = {"p": [], "u": [], "v": []}
    nan_rows = 0
    first_nan = None
    finite_rows = 0

    for idx, row in enumerate(rows, start=1):
        try:
            tval = float(row["t"])
        except Exception:
            continue
        times.append(tval)
        row_has_finite = False
        row_has_nan = False
        for key in ("p", "u", "v"):
            value = row.get(key, "-")
            if value in {"-", ""}:
                series[key].append(np.nan)
            else:
                fval = float(value)
                series[key].append(fval)
                if math.isfinite(fval):
                    row_has_finite = True
                else:
                    row_has_nan = True
        if row_has_finite:
            finite_rows += 1
        if row_has_nan:
            nan_rows += 1
            if first_nan is None:
                first_nan = idx

    summary["finite_rows"] = finite_rows
    summary["nan_rows"] = nan_rows
    summary["first_nan_row"] = first_nan
    summary["pseudo_final_time"] = max(times) if times else None

    if times:
        arr_t = np.array(times, dtype=float)
        for key, label in (("p", "p"), ("u", "u"), ("v", "v")):
            arr = np.array(series[key], dtype=float)
            good = np.isfinite(arr)
            if np.any(good):
                ax.semilogy(arr_t[good], arr[good], marker="o", markersize=3, label=label)
    ax.set_xlabel("physical time")
    ax.set_ylabel("pseudo residual")
    ax.set_title("PASS 5 pseudo-stat history")
    ax.grid(True, alpha=0.3)
    if ax.lines:
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pseudo_stat_history.png", dpi=220)
    plt.close(fig)
    return summary


def plot_cp() -> dict[str, object]:
    cmp_json = OUT_DATA / "cp_metrics.json"
    cmp_csv = OUT_DATA / "cp_comparison.csv"
    source_json = cmp_json
    source_csv = cmp_csv
    if (OUT_DATA / "cp_comparison.json").exists():
        source_json = OUT_DATA / "cp_comparison.json"
    if not source_csv.exists():
        pass4_csv = PASS4_DATA / "pyfr_cp_comparison.csv"
        pass4_json = pass4_csv.with_suffix(".json")
        if pass4_csv.exists():
            source_csv = pass4_csv
        if pass4_json.exists() and not (OUT_DATA / "cp_comparison.json").exists():
            source_json = pass4_json
    if not source_csv.exists():
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No finite PASS 5 Cp comparison is available.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / "cp_comparison.png", dpi=220)
        plt.close(fig)
        return {"cp_available": False}

    rows = load_csv(source_csv)
    x = np.array([float(r["x_over_c"]) for r in rows], dtype=float)
    cp_exp = np.array([float(r["Cp_exp"]) for r in rows], dtype=float)
    cp_pyfr = np.array([float(r["Cp_pyfr"]) for r in rows], dtype=float)
    dx = np.array([float(r["dx_over_c"]) for r in rows], dtype=float)
    good = np.isfinite(cp_pyfr)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, cp_exp, "o-", label="NASA experimental Cp", markersize=3.5)
    if np.any(good):
        ax.plot(x[good], cp_pyfr[good], "s-", label="PyFR Cp", markersize=3)
    else:
        ax.text(0.5, 0.5, "PyFR Cp values remain non-finite.", ha="center", va="center", transform=ax.transAxes)
    ax.set_xlabel("x/c")
    ax.set_ylabel("Cp")
    ax.set_title("PASS 5 PyFR Cp comparison against NASA data")
    ax.grid(True, alpha=0.3)
    if np.any(good):
        ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_comparison.png", dpi=220)
    plt.close(fig)

    if source_json.exists():
        payload = json.loads(source_json.read_text())
        payload["cp_available"] = bool(payload.get("finite_cp_matches", 0)) and math.isfinite(float(payload.get("cp_mae", math.nan)))
        payload["max_nearest_distance_x_over_c"] = float(np.max(np.abs(dx))) if len(dx) else None
        payload["mean_nearest_distance_x_over_c"] = float(np.mean(np.abs(dx))) if len(dx) else None
        payload["finite_wall_point_count"] = int(np.count_nonzero(np.isfinite(cp_pyfr)))
        cmp_json.write_text(json.dumps(payload, indent=2))
        return payload
    return {"cp_available": bool(np.any(good))}


def plot_wall_diagnostic() -> None:
    raw_csv = OUT_DATA / "pyfr_wall_cp.csv"
    if not raw_csv.exists():
        pass4_raw = PASS4_DATA / "pyfr_wall_pressure_raw.csv"
        if pass4_raw.exists():
            raw_csv = pass4_raw
    fig, ax = plt.subplots(figsize=(10, 4))
    if not raw_csv.exists():
        ax.text(0.5, 0.5, "No wall extraction CSV found.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
    else:
        rows = load_csv(raw_csv)
        x = np.array([float(r["x_over_c"]) for r in rows], dtype=float)
        dy = np.array([float(r["dy_m"]) for r in rows], dtype=float)
        p = np.array([float(r["pressure"]) for r in rows], dtype=float)
        good = np.isfinite(p)
        ax.scatter(x[~good], dy[~good], s=6, label="non-finite pressure", alpha=0.5)
        if np.any(good):
            ax.scatter(x[good], dy[good], s=6, label="finite pressure", alpha=0.7)
        ax.set_xlabel("x/c")
        ax.set_ylabel("wall distance of chosen sample (m)")
        ax.set_title("PASS 5 lower-wall extraction diagnostic")
        ax.grid(True, alpha=0.3)
        if ax.collections:
            ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "wall_extraction_diagnostic.png", dpi=220)
    plt.close(fig)


def write_summary_table(run_name: str, run_dir: Path, pseudo: dict[str, object], cp_metrics: dict[str, object]) -> None:
    slurm_outs = sorted(run_dir.glob("slurm-*.out"))
    details = parse_slurm_out(slurm_outs[-1]) if slurm_outs else {}
    if run_name == "promoted":
        vtu_present = (run_dir / "pass5_promoted_latest.vtu").exists()
    elif run_name == "diagnostic":
        vtu_present = (run_dir / "pass5_diagnostic_latest.vtu").exists()
    else:
        vtu_present = (run_dir / "pass4_long_latest.vtu").exists()
    rows = [
        ("Run name", run_name),
        ("Run directory", str(run_dir.relative_to(ROOT))),
        ("VTU export present", str(vtu_present)),
        ("Pseudo rows", pseudo.get("pseudo_rows", 0)),
        ("Finite pseudo rows", pseudo.get("finite_rows", 0)),
        ("NaN pseudo rows", pseudo.get("nan_rows", 0)),
        ("First NaN row", pseudo.get("first_nan_row", "n/a")),
        ("Final pseudo time", pseudo.get("pseudo_final_time", "n/a")),
        ("Hostname", details.get("hostname", "n/a")),
        ("GPU line", details.get("gpu_line", "n/a")),
        ("Python", details.get("python_version", "n/a")),
        ("PyFR", details.get("pyfr_version", "n/a")),
        ("Cp available", cp_metrics.get("cp_available", False)),
        ("Cp MAE", cp_metrics.get("cp_mae", "unavailable")),
        ("Cp RMSE", cp_metrics.get("cp_rmse", "unavailable")),
        ("Finite wall point count", cp_metrics.get("finite_wall_point_count", "unavailable")),
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
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    run_name, run_dir = choose_run_dir()
    pseudo = summarize_pseudo_stats(run_dir)
    cp_metrics = plot_cp()
    plot_wall_diagnostic()

    payload = {"run_name": run_name, "run_dir": str(run_dir), "pseudo": pseudo, "cp_metrics": cp_metrics}
    (OUT_DATA / "pseudo_stats_summary.json").write_text(json.dumps(pseudo, indent=2))
    (OUT_DATA / "field_summary.json").write_text(json.dumps(payload, indent=2))
    if not (OUT_DATA / "cp_metrics.json").exists() and isinstance(cp_metrics, dict):
        (OUT_DATA / "cp_metrics.json").write_text(json.dumps(cp_metrics, indent=2))
    write_summary_table(run_name, run_dir, pseudo, cp_metrics)


if __name__ == "__main__":
    main()
