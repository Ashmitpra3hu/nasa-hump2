#!/usr/bin/env python3
"""Summarize GPU PyFR PASS 6 stability and validation results."""

from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gpu_pyfr_pass6" / "stability"
CFG_DIR = ROOT / "data" / "NASA_2DWMH_PyFR" / "configs"
OUT_ROOT = ROOT / "documentation_src" / "gpu_pyfr_pass6"
OUT_DATA = OUT_ROOT / "data"
OUT_FIG = OUT_ROOT / "figures"
AUDIT_DIR = OUT_DATA / "stability_audits"
CP_CASE_DIR = OUT_DATA / "cp_cases"
BENCH_CASE_DIR = OUT_DATA / "benchmark_cases"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def slurm_meta(run_dir: Path) -> dict[str, object]:
    out_files = sorted(run_dir.glob("slurm-*.out"))
    err_files = sorted(run_dir.glob("slurm-*.err"))
    data: dict[str, object] = {
        "job_id": None,
        "hostname": None,
        "gpu_line": None,
        "out_file": None,
        "err_file": None,
        "slurm_state_hint": None,
    }
    if out_files:
        out_file = out_files[-1]
        data["out_file"] = out_file.name
        data["job_id"] = out_file.stem.split("-")[-1]
        lines = out_file.read_text(errors="ignore").splitlines()
        if lines:
            data["hostname"] = lines[0].strip()
        for line in lines:
            if "NVIDIA A100" in line and data["gpu_line"] is None:
                data["gpu_line"] = line.strip()
            if "Traceback" in line and data["slurm_state_hint"] is None:
                data["slurm_state_hint"] = "traceback_in_stdout"
    if err_files:
        data["err_file"] = err_files[-1].name
        err_text = err_files[-1].read_text(errors="ignore").strip()
        if err_text and data["slurm_state_hint"] is None:
            data["slurm_state_hint"] = "stderr_nonempty"
    return data


def pseudo_meta(run_dir: Path) -> dict[str, object]:
    path = run_dir / "pseudo_stats.csv"
    meta: dict[str, object] = {
        "pseudo_rows": 0,
        "finite_rows": 0,
        "first_nonfinite_row": None,
        "final_time": None,
        "vtu_exists": any(run_dir.glob("*.vtu")),
    }
    if not path.exists():
        return meta
    rows = load_csv(path)
    meta["pseudo_rows"] = len(rows)
    value_keys = [k for k in rows[0].keys() if k not in {"n", "t", "i"}] if rows else []
    times = []
    finite_rows = 0
    first_nonfinite = None
    for idx, row in enumerate(rows, start=1):
        try:
            times.append(float(row["t"]))
        except Exception:
            pass
        vals = []
        for key in value_keys:
            raw = row.get(key, "-")
            if raw in {"-", ""}:
                vals.append(np.nan)
            else:
                vals.append(float(raw))
        if all(np.isfinite(vals)):
            finite_rows += 1
        elif first_nonfinite is None:
            first_nonfinite = idx
    meta["finite_rows"] = finite_rows
    meta["first_nonfinite_row"] = first_nonfinite
    meta["final_time"] = max(times) if times else None
    return meta


def audit_meta(case_name: str) -> dict[str, object]:
    path = AUDIT_DIR / f"{case_name}.json"
    if not path.exists():
        return {"audit_exists": False}
    obj = json.loads(path.read_text())
    point_arrays = {a["name"]: a for a in obj.get("point_arrays", [])}
    vel = point_arrays.get("Velocity", {"components": [{}, {}]}).get("components", [{}, {}])
    return {
        "audit_exists": True,
        "num_points": obj.get("num_points"),
        "num_cells": obj.get("num_cells"),
        "finite_density": point_arrays.get("Density", {"components": [{}]})["components"][0].get("finite_count"),
        "finite_velocity_x": vel[0].get("finite_count") if len(vel) > 0 else None,
        "finite_velocity_y": vel[1].get("finite_count") if len(vel) > 1 else None,
        "finite_pressure": point_arrays.get("Pressure", {"components": [{}]})["components"][0].get("finite_count"),
    }


def cp_meta(case_name: str) -> dict[str, object]:
    path = CP_CASE_DIR / f"{case_name}_cp.json"
    if not path.exists():
        return {"cp_available": False, "cp_mae": None, "cp_rmse": None, "finite_cp_matches": 0}
    data = json.loads(path.read_text())
    return {
        "cp_available": bool(data.get("finite_cp_matches", 0)),
        "cp_mae": data.get("cp_mae"),
        "cp_rmse": data.get("cp_rmse"),
        "finite_cp_matches": data.get("finite_cp_matches", 0),
    }


def bench_meta(case_name: str) -> dict[str, object]:
    path = BENCH_CASE_DIR / f"{case_name}_metrics.json"
    if not path.exists():
        return {"benchmark_available": False, "benchmark_score": None}
    data = json.loads(path.read_text())
    return {
        "benchmark_available": bool(data.get("score_available")),
        "benchmark_score": data.get("score"),
        "linear_fallback_count": data.get("linear_fallback_count"),
        "max_nearest_distance_m": data.get("max_nearest_distance_m"),
        "mean_nearest_distance_m": data.get("mean_nearest_distance_m"),
    }


def promoted_case(rows: list[dict[str, object]]) -> dict[str, object]:
    scored = [r for r in rows if r.get("benchmark_available")]
    if not scored:
        raise RuntimeError("No benchmark-mappable PASS 6 cases were found.")

    def sort_key(row: dict[str, object]) -> tuple[float, float]:
        score = float(row.get("benchmark_score") or np.inf)
        cp = row.get("cp_mae")
        cp_val = float(cp) if cp is not None and math.isfinite(float(cp)) else np.inf
        return (score, cp_val)

    return min(scored, key=sort_key)


def copy_promoted_artifacts(case_name: str) -> None:
    shutil.copy2(AUDIT_DIR / f"{case_name}.json", OUT_DATA / "finite_field_audit.json")
    shutil.copy2(CP_CASE_DIR / f"{case_name}_wall.csv", OUT_DATA / "pyfr_wall_cp.csv")
    shutil.copy2(CP_CASE_DIR / f"{case_name}_cp.csv", OUT_DATA / "cp_comparison.csv")
    shutil.copy2(CP_CASE_DIR / f"{case_name}_cp.json", OUT_DATA / "cp_metrics.json")
    shutil.copy2(BENCH_CASE_DIR / f"{case_name}_samples.csv", OUT_DATA / "pyfr_benchmark_samples.csv")
    shutil.copy2(BENCH_CASE_DIR / f"{case_name}_metrics.json", OUT_DATA / "pyfr_benchmark_metrics.json")


def write_tables(rows: list[dict[str, object]], best: dict[str, object]) -> None:
    with (OUT_DATA / "stability_sweep_table.tex").open("w") as handle:
        handle.write("\\begin{tabular}{llllll}\n\\toprule\n")
        handle.write("Case & dt & final time & finite vel-x & Cp MAE & benchmark MAE\\\\\n\\midrule\n")
        for row in rows:
            handle.write(
                f"{str(row['config_name']).replace('_', '\\_')} & "
                f"{row['dt']} & {row['final_time_target']} & "
                f"{row.get('finite_velocity_x')} & "
                f"{row.get('cp_mae')} & {row.get('benchmark_score')}\\\\\n"
            )
        handle.write("\\bottomrule\n\\end{tabular}\n")

    best_rows = [
        ("Promoted case", best["config_name"]),
        ("Benchmark MAE", best["benchmark_score"]),
        ("Cp MAE", best["cp_mae"]),
        ("Cp RMSE", best["cp_rmse"]),
        ("Finite pressure count", best["finite_pressure"]),
        ("Finite velocity x count", best["finite_velocity_x"]),
        ("Linear fallback count", best["linear_fallback_count"]),
        ("Max nearest distance (m)", best["max_nearest_distance_m"]),
    ]
    with (OUT_DATA / "finite_field_table.tex").open("w") as handle:
        handle.write("\\begin{tabular}{ll}\n\\toprule\nMetric & Value\\\\\n\\midrule\n")
        for key, value in best_rows:
            handle.write(f"{key} & {str(value).replace('_', '\\_')}\\\\\n")
        handle.write("\\bottomrule\n\\end{tabular}\n")


def plot_stability(rows: list[dict[str, object]]) -> None:
    labels = [str(r["config_name"]) for r in rows]
    x = np.arange(len(labels))
    finite_pressure = [float(r.get("finite_pressure") or 0) for r in rows]
    benchmark = [float(r["benchmark_score"]) if r.get("benchmark_score") is not None else np.nan for r in rows]

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.bar(x, finite_pressure, color="#4c78a8", alpha=0.7)
    ax1.set_ylabel("finite pressure point count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha="right")
    ax1.grid(True, axis="y", alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, benchmark, "o-", color="#d62728", label="benchmark MAE")
    ax2.set_ylabel("benchmark MAE")
    ax1.set_title("PASS 6 stability sweep: finite-field success and benchmark score")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "stability_sweep_summary.png", dpi=220)
    plt.close(fig)


def plot_pseudo_history(case_name: str) -> None:
    rows = load_csv(RUN_ROOT / case_name / "pseudo_stats.csv")
    t = np.array([float(r["t"]) for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    for key in ("rho", "rhou", "rhov", "E"):
        arr = np.array([np.nan if r[key] in {"-", ""} else float(r[key]) for r in rows], dtype=float)
        good = np.isfinite(arr)
        if np.any(good):
            ax.semilogy(t[good], arr[good], marker="o", markersize=2, label=key)
    ax.set_xlabel("physical time")
    ax.set_ylabel("pseudo residual")
    ax.set_title(f"PASS 6 pseudo-stat history: {case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "pseudo_stat_history.png", dpi=220)
    plt.close(fig)


def plot_cp(case_name: str) -> None:
    rows = load_csv(CP_CASE_DIR / f"{case_name}_cp.csv")
    x = np.array([float(r["x_over_c"]) for r in rows], dtype=float)
    cp_exp = np.array([float(r["Cp_exp"]) for r in rows], dtype=float)
    cp_pyfr = np.array([float(r["Cp_pyfr"]) for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, cp_exp, "o-", label="NASA experimental Cp", markersize=3)
    ax.plot(x, cp_pyfr, "s-", label="PyFR Cp", markersize=3)
    ax.set_xlabel("x/c")
    ax.set_ylabel("Cp")
    ax.set_title(f"PASS 6 PyFR Cp comparison: {case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "cp_comparison.png", dpi=220)
    plt.close(fig)


def plot_wall_diagnostic(case_name: str) -> None:
    rows = load_csv(CP_CASE_DIR / f"{case_name}_wall.csv")
    x = np.array([float(r["x_over_c"]) for r in rows], dtype=float)
    dy = np.array([float(r["dy_m"]) for r in rows], dtype=float)
    cp = np.array([float(r["Cp"]) for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(x, dy, c=cp, s=6, cmap="viridis")
    ax.set_xlabel("x/c")
    ax.set_ylabel("wall sample height above geometry (m)")
    ax.set_title(f"PASS 6 wall extraction diagnostic: {case_name}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "wall_extraction_diagnostic.png", dpi=220)
    plt.close(fig)


def plot_benchmark_coverage(case_name: str) -> None:
    rows = load_csv(BENCH_CASE_DIR / f"{case_name}_samples.csv")
    x = np.array([float(r["query_x_over_c"]) for r in rows], dtype=float)
    dist = np.array([float(r["nearest_distance_m"]) for r in rows], dtype=float)
    fallback = np.array([int(r["used_nearest_fallback"]) for r in rows], dtype=int)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, dist, ".", label="nearest query distance")
    if np.any(fallback):
        ax.scatter(x[fallback > 0], dist[fallback > 0], color="red", s=10, label="nearest fallback points")
    ax.set_xlabel("query x/c")
    ax.set_ylabel("nearest CFD point distance (m)")
    ax.set_title(f"PASS 6 benchmark sample coverage: {case_name}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "benchmark_sample_coverage.png", dpi=220)
    plt.close(fig)


def main() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)

    rows_out: list[dict[str, object]] = []
    for manifest_path in sorted(CFG_DIR.glob("pass6_*_manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        case_name = manifest["name"]
        run_dir = RUN_ROOT / case_name
        row: dict[str, object] = {
            "config_name": case_name,
            "system": manifest["system"],
            "mesh": manifest["mesh"],
            "final_time_target": manifest["tend"],
            "dt": manifest["dt"],
            "notes": manifest["notes"],
        }
        row.update(slurm_meta(run_dir))
        row.update(pseudo_meta(run_dir))
        row.update(audit_meta(case_name))
        row.update(cp_meta(case_name))
        row.update(bench_meta(case_name))
        rows_out.append(row)

    best = promoted_case(rows_out)
    copy_promoted_artifacts(str(best["config_name"]))

    (OUT_DATA / "stability_sweep_summary.json").write_text(json.dumps(rows_out, indent=2))
    with (OUT_DATA / "stability_sweep_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    (OUT_DATA / "promoted_case_summary.json").write_text(json.dumps(best, indent=2))

    write_tables(rows_out, best)
    plot_stability(rows_out)
    plot_pseudo_history(str(best["config_name"]))
    plot_cp(str(best["config_name"]))
    plot_wall_diagnostic(str(best["config_name"]))
    plot_benchmark_coverage(str(best["config_name"]))


if __name__ == "__main__":
    main()
