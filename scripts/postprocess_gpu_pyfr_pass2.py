#!/usr/bin/env python3
"""Postprocess PASS 2 PyFR outputs without relying on PyFR samplers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    import meshio
except ImportError:  # pragma: no cover - local fallback when meshio is unavailable
    meshio = None


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "gpu_pyfr_pass2"
OUT_DATA = ROOT / "documentation_src" / "data_gpu_pyfr_pass2"
OUT_FIG = ROOT / "documentation_src" / "figures_gpu_pyfr_pass2"
PASS5_SUMMARY = ROOT / "documentation_src" / "data_pass5" / "pass5_comparison_summary.json"


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def parse_pseudostats(case_dir: Path) -> dict[str, object]:
    path = case_dir / "pseudo_stats.csv"
    if not path.exists():
        return {"pseudo_rows": 0, "pseudo_final_time": None}
    rows = load_csv(path)
    times = []
    for row in rows:
        try:
            times.append(float(row["t"]))
        except Exception:
            continue
    return {
        "pseudo_rows": len(rows),
        "pseudo_final_time": max(times) if times else None,
    }


def find_latest_vtu(case_dir: Path) -> Path | None:
    vtus = sorted(case_dir.glob("*.vtu"))
    return vtus[-1] if vtus else None


def plot_pseudo(case: str, case_dir: Path) -> None:
    path = case_dir / "pseudo_stats.csv"
    if not path.exists():
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"No pseudo_stats.csv found for {case}.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / f"{case}_pseudo_stats.png", dpi=220)
        plt.close(fig)
        return
    rows = load_csv(path)
    if not rows:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"pseudo_stats.csv for {case} was empty.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / f"{case}_pseudo_stats.png", dpi=220)
        plt.close(fig)
        return

    t = np.array([float(r["t"]) for r in rows if r["t"] not in {"-", "nan", "NaN"}], dtype=float)
    if t.size == 0:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"pseudo_stats.csv for {case} had no finite time rows.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / f"{case}_pseudo_stats.png", dpi=220)
        plt.close(fig)
        return

    def col(name: str) -> np.ndarray:
        vals = []
        for r in rows:
            value = r.get(name, "-")
            vals.append(np.nan if value in {"-", "nan", "NaN"} else float(value))
        return np.array(vals, dtype=float)

    p = col("p")
    u = col("u")
    v = col("v")

    fig, ax = plt.subplots(figsize=(10, 4))
    if len(p) == len(t):
        ax.semilogy(t, p, label="p")
    if len(u) == len(t):
        ax.semilogy(t, u, label="u")
    if len(v) == len(t):
        ax.semilogy(t, v, label="v")
    ax.set_xlabel("physical time")
    ax.set_ylabel("pseudo residual")
    ax.set_title(f"{case} pseudo-stat history")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / f"{case}_pseudo_stats.png", dpi=220)
    plt.close(fig)


def plot_vtu(case: str, vtu_path: Path) -> dict[str, object]:
    if meshio is None:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"meshio is not installed locally, so {case} VTU could not be parsed in this environment.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / f"{case}_field.png", dpi=220)
        plt.close(fig)
        return {"field_plot": None, "point_fields": []}

    mesh = meshio.read(vtu_path)
    points = np.asarray(mesh.points[:, :2], dtype=float)

    cell_blocks = [block.data for block in mesh.cells if block.type in {"triangle", "quad"}]
    if not cell_blocks:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"{case} VTU had no triangle/quad cells.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(OUT_FIG / f"{case}_field.png", dpi=220)
        plt.close(fig)
        return {"field_plot": None}

    cell_data = mesh.point_data
    scalar_keys = list(cell_data.keys())
    velocity = None
    pressure = None
    for key, arr in cell_data.items():
        arr = np.asarray(arr)
        if arr.ndim == 2 and arr.shape[1] >= 2 and velocity is None:
            velocity = arr[:, :2]
        elif arr.ndim == 1 and pressure is None:
            pressure = arr

    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    tri_blocks = [block.data for block in mesh.cells if block.type == "triangle"]
    if tri_blocks:
        tri = np.vstack(tri_blocks)
        if velocity is not None:
            speed = np.sqrt(velocity[:, 0] ** 2 + velocity[:, 1] ** 2)
            c1 = axes[0].tricontourf(points[:, 0], points[:, 1], tri, speed, levels=30, cmap="viridis")
            fig.colorbar(c1, ax=axes[0], label="|U|")
            axes[0].set_title(f"{case} velocity magnitude")
        else:
            axes[0].text(0.5, 0.5, f"No vector point field found.\nAvailable keys: {scalar_keys}", ha="center", va="center", transform=axes[0].transAxes)
        if pressure is not None:
            c2 = axes[1].tricontourf(points[:, 0], points[:, 1], tri, pressure, levels=30, cmap="coolwarm")
            fig.colorbar(c2, ax=axes[1], label="scalar")
            axes[1].set_title(f"{case} pressure-like scalar")
        else:
            axes[1].text(0.5, 0.5, f"No scalar point field found.\nAvailable keys: {scalar_keys}", ha="center", va="center", transform=axes[1].transAxes)
    else:
        for ax in axes:
            ax.text(0.5, 0.5, "PASS 2 VTU export did not contain triangle cells usable by this lightweight plotter.", ha="center", va="center", transform=ax.transAxes)

    for ax in axes:
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
    fig.tight_layout()
    fig.savefig(OUT_FIG / f"{case}_field.png", dpi=220)
    plt.close(fig)
    return {"field_plot": str(OUT_FIG / f"{case}_field.png"), "point_fields": scalar_keys}


def plot_status(rows: list[dict[str, object]]) -> None:
    labels = [r["case"] for r in rows]
    ypos = np.arange(len(rows))
    colors = ["#2ca02c" if r["status"] == "completed" else "#d62728" for r in rows]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.barh(ypos, np.ones(len(rows)), color=colors, alpha=0.85)
    for y, row in zip(ypos, rows):
        ax.text(0.02, y, row["notes"], va="center", ha="left", fontsize=8.5, color="white" if row["status"] == "failed" else "black")
    ax.set_yticks(ypos, labels)
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks([])
    ax.invert_yaxis()
    ax.set_title("GPU PyFR PASS 2 run status")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "gpu_pyfr_pass2_status.png", dpi=220)
    plt.close(fig)


def placeholder_field(case: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT_FIG / f"{case}_field.png", dpi=220)
    plt.close(fig)


def summary_row(case: str) -> dict[str, object]:
    case_dir = RUNS / case
    row: dict[str, object] = {"case": case, "status": "missing", "notes": "case directory missing"}
    status_path = case_dir / "status.json"
    if not case_dir.exists():
        if status_path.exists():
            row.update(json.loads(status_path.read_text()))
        placeholder_field(case, f"{row['notes']}")
        plot_pseudo(case, case_dir)
        return row

    if status_path.exists():
        row.update(json.loads(status_path.read_text()))

    latest_vtu = find_latest_vtu(case_dir)
    if latest_vtu:
        row["status"] = "completed"
        row["notes"] = "solution export present"
    elif row.get("status") in {"pending", "queued", "submitted", "not_submitted"}:
        row.setdefault("notes", "valid Slurm submission exists but no VTU export is available yet")
        placeholder_field(case, f"{row['notes']}")
    else:
        row["status"] = "failed"
        row["notes"] = "no VTU export found"
        placeholder_field(case, f"{row['notes']}")
    row |= parse_pseudostats(case_dir)

    slurm_errs = sorted(case_dir.glob("slurm-*.err"))
    if slurm_errs:
        row["last_err_file"] = slurm_errs[-1].name
        err_text = slurm_errs[-1].read_text(errors="ignore")
        if "Traceback" in err_text:
            row["notes"] = err_text.strip().splitlines()[-1]

    if latest_vtu:
        row["vtu_file"] = latest_vtu.name
        row |= plot_vtu(case, latest_vtu)
    plot_pseudo(case, case_dir)
    return row


def main() -> None:
    ensure_dirs()
    rows = [summary_row(case) for case in ["minimal", "field_only", "sparse_wall", "full_wall"]]
    plot_status(rows)

    with (OUT_DATA / "gpu_pyfr_pass2_summary.json").open("w") as handle:
        json.dump({"rows": rows}, handle, indent=2)

    with (OUT_DATA / "gpu_pyfr_pass2_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({k for row in rows for k in row.keys()}))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "\\begin{tabular}{p{2.2cm} p{1.3cm} p{1.9cm} p{6.5cm}}",
        "\\toprule",
        "Case & Status & Final pseudo time & Notes\\\\",
        "\\midrule",
    ]
    for row in rows:
        final_time = row.get("pseudo_final_time")
        tfmt = "--" if final_time is None else f"{float(final_time):.4f}"
        lines.append(
            f"{row['case'].replace('_', '\\_')} & {str(row['status']).replace('_', '\\_')} & {tfmt} & {str(row['notes']).replace('_', '\\_')}\\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    (OUT_DATA / "summary_table.tex").write_text("\n".join(lines))

    print(json.dumps({"rows": rows}, indent=2))


if __name__ == "__main__":
    main()
