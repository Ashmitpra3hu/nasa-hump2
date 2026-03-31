#!/usr/bin/env python3
"""Run a small, documented NASA hump experiment sweep inside the running openfoam container."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_CASE = ROOT / "data" / "NASA_2DWMH"
SWEEP_ROOT = ROOT / "data" / "NASA_2DWMH_sweep"
OUT_ROOT = ROOT / "documentation_src" / "data_second_pass"
SUMMARY_CSV = OUT_ROOT / "experiment_sweep_summary.csv"
SUMMARY_JSON = OUT_ROOT / "experiment_sweep_summary.json"
NOTES_MD = ROOT / "documentation_src" / "MAE_EXPERIMENT_NOTES.md"
CONTAINER = os.environ.get("NASA_HUMP_CONTAINER", "openfoam")


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd or ROOT, env=env, check=True, text=True, capture_output=True)


def clean_case_dir(case_dir: Path) -> None:
    for child in case_dir.iterdir():
        if child.is_dir() and child.name != "0" and child.name.replace(".", "", 1).isdigit():
            shutil.rmtree(child)
    for rel in ["constant/polyMesh", "postProcessing", "VTK"]:
        path = case_dir / rel
        if path.exists():
            shutil.rmtree(path)
    for path in case_dir.glob("log.*"):
        path.unlink()
    foam_file = case_dir / "foam.foam"
    if foam_file.exists():
        foam_file.unlink()


def copy_template(case_dir: Path) -> None:
    if case_dir.exists():
        shutil.rmtree(case_dir)
    shutil.copytree(BASE_CASE, case_dir)
    clean_case_dir(case_dir)


def local_generate(case_dir: Path, env_overrides: dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(env_overrides)
    env["NASA_HUMP_CASE_DIR"] = str(case_dir.relative_to(ROOT))
    run(["python3", "scripts/generate_nasa_hump_blockmesh.py"], env=env)
    run(["python3", "scripts/configure_nasa_hump_case.py"], env=env)
    run(["python3", "scripts/write_nasa_hump_inlet_profile.py"], env=env)


def container_case_path(case_dir: Path) -> str:
    return f"/home/openfoam/{case_dir.relative_to(ROOT)}"


def docker_exec(script: str) -> None:
    run(["docker", "exec", CONTAINER, "/bin/bash", "-lc", script])


def copy_to_container(case_dir: Path) -> None:
    remote_case = container_case_path(case_dir)
    remote_parent = str(Path(remote_case).parent)
    docker_exec(f"rm -rf '{remote_case}' && mkdir -p '{remote_parent}'")
    run(["docker", "cp", str(case_dir), f"{CONTAINER}:{remote_parent}"])


def run_case_in_container(case_dir: Path) -> None:
    remote_case = container_case_path(case_dir)
    docker_exec(
        "set -euo pipefail; "
        f"blockMesh -case '{remote_case}' > '{remote_case}/log.blockMesh'; "
        f"checkMesh -case '{remote_case}' > '{remote_case}/log.checkMesh'; "
        f"postProcess -case '{remote_case}' -func writeCellCentres -time 0 > '{remote_case}/log.writeCellCentres'; "
        f"simpleFoam -case '{remote_case}' > '{remote_case}/log.run'; "
        f"simpleFoam -case '{remote_case}' -postProcess -latestTime -func wallShearStress > '{remote_case}/log.wallShearStress'; "
        f"postProcess -case '{remote_case}' -latestTime -func 'grad(U)' > '{remote_case}/log.gradU'; "
        f"postProcess -case '{remote_case}' -latestTime -dict system/bottomValues > '{remote_case}/log.bottomValues'"
    )


def copy_from_container(case_dir: Path) -> None:
    remote_case = container_case_path(case_dir)
    run(["docker", "cp", f"{CONTAINER}:{remote_case}/.", str(case_dir)])
    (case_dir / "foam.foam").touch()


def evaluate_case(case_dir: Path, tag: str) -> dict[str, object]:
    pred_csv = OUT_ROOT / f"{tag}_predictions.csv"
    summary_json = OUT_ROOT / f"{tag}_score.json"
    result = run(
        [
            "python3",
            "scripts/evaluate_nasa_hump_case.py",
            str(case_dir),
            "--prediction-csv",
            str(pred_csv),
            "--summary-json",
            str(summary_json),
        ]
    )
    return json.loads(result.stdout)


def record_notes(rows: list[dict[str, object]]) -> None:
    lines = [
        "# MAE Experiment Notes",
        "",
        "This file records the post-second-pass NASA hump MAE sweep run against the local benchmark metric.",
        "",
        "| Tag | Key changes | End time | Runtime (min) | MAE | Notes |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['tag']} | {row['changes']} | {row['end_time']} | {row['runtime_minutes']:.2f} | {row['score']:.10f} | {row['note']} |"
        )
    NOTES_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SWEEP_ROOT.mkdir(parents=True, exist_ok=True)

    baseline = json.loads((OUT_ROOT / "reconstructed_nasa_score_second_pass.json").read_text())

    experiments = [
        {
            "tag": "exp_uniform_sst_500",
            "changes": "Current best second-pass baseline rerun deeper with uniform inlet and SST to 500 iterations",
            "note": "Direct convergence-extension test on the strongest known configuration.",
            "env": {
                "NASA_HUMP_INLET_MODE": "uniform",
                "NASA_HUMP_END_TIME": "500",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "stable",
            },
        },
        {
            "tag": "exp_tbl_sst_220",
            "changes": "Analytic turbulent-boundary-layer inlet for U/k/omega; SST; stable transport; base pass-two mesh/top wall",
            "note": "Primary inflow-fidelity test.",
            "env": {
                "NASA_HUMP_INLET_MODE": "tbl",
                "NASA_HUMP_INLET_DELTA": "0.028",
                "NASA_HUMP_END_TIME": "220",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "stable",
            },
        },
        {
            "tag": "exp_tbl_sst_sharp_220",
            "changes": "Same analytic inlet; SST; sharper k and omega convection",
            "note": "Tests whether reduced transport diffusion helps the separated shear layer.",
            "env": {
                "NASA_HUMP_INLET_MODE": "tbl",
                "NASA_HUMP_INLET_DELTA": "0.028",
                "NASA_HUMP_END_TIME": "220",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "sharper",
            },
        },
        {
            "tag": "exp_tbl_sst_sharp_meshtop_220",
            "changes": "Same as sharper SST case plus targeted mesh refinement and a stronger blockage contour",
            "note": "Combined fidelity test for mesh-targeting and upper-wall blockage.",
            "env": {
                "NASA_HUMP_INLET_MODE": "tbl",
                "NASA_HUMP_INLET_DELTA": "0.028",
                "NASA_HUMP_END_TIME": "220",
                "NASA_HUMP_MODEL": "kOmegaSST",
                "NASA_HUMP_SCHEME_MODE": "sharper",
                "NASA_HUMP_Y_CELLS": "260",
                "NASA_HUMP_X_CELLS": "340,400,280",
                "NASA_HUMP_Y_GRADING": "22",
                "NASA_HUMP_TOP_CONTOUR_START": "-0.45",
                "NASA_HUMP_TOP_CONTOUR_END": "0.78",
                "NASA_HUMP_TOP_CONTOUR_DIP": "0.028",
            },
        },
        {
            "tag": "exp_tbl_komega_sharp_meshtop_180",
            "changes": "Analytic inlet; sharper convection; refined mesh and stronger blockage contour; standard kOmega model",
            "note": "Short closure screen against SST on the refined geometry.",
            "env": {
                "NASA_HUMP_INLET_MODE": "tbl",
                "NASA_HUMP_INLET_DELTA": "0.028",
                "NASA_HUMP_END_TIME": "180",
                "NASA_HUMP_MODEL": "kOmega",
                "NASA_HUMP_SCHEME_MODE": "sharper",
                "NASA_HUMP_Y_CELLS": "260",
                "NASA_HUMP_X_CELLS": "340,400,280",
                "NASA_HUMP_Y_GRADING": "22",
                "NASA_HUMP_TOP_CONTOUR_START": "-0.45",
                "NASA_HUMP_TOP_CONTOUR_END": "0.78",
                "NASA_HUMP_TOP_CONTOUR_DIP": "0.028",
            },
        },
    ]

    only_tags_env = os.environ.get("NASA_HUMP_ONLY_TAGS", "").strip()
    if only_tags_env:
        allowed = {item.strip() for item in only_tags_env.split(",") if item.strip()}
        experiments = [experiment for experiment in experiments if experiment["tag"] in allowed]

    rows: list[dict[str, object]] = [
        {
            "tag": "baseline_second_pass",
            "changes": "Existing best second-pass reference",
            "note": "Reference row carried forward from the current repo state.",
            "end_time": int(float(baseline["time_directory"])),
            "runtime_minutes": 0.0,
            "score": float(baseline["score"]),
            "case_dir": "data/NASA_2DWMH",
        }
    ]

    best_score = float(baseline["score"])
    best_case_dir = BASE_CASE
    best_tag = "baseline_second_pass"

    best_env: dict[str, str] | None = None

    for experiment in experiments:
        case_dir = SWEEP_ROOT / experiment["tag"]
        copy_template(case_dir)
        local_generate(case_dir, experiment["env"])

        start = time.time()
        copy_to_container(case_dir)
        run_case_in_container(case_dir)
        copy_from_container(case_dir)
        runtime_minutes = (time.time() - start) / 60.0

        result = evaluate_case(case_dir, experiment["tag"])
        score = float(result["score"])
        row = {
            "tag": experiment["tag"],
            "changes": experiment["changes"],
            "note": experiment["note"],
            "end_time": int(float(result["time_directory"])),
            "runtime_minutes": runtime_minutes,
            "score": score,
            "case_dir": str(case_dir.relative_to(ROOT)),
        }
        rows.append(row)

        if score < best_score:
            best_score = score
            best_case_dir = case_dir
            best_tag = experiment["tag"]
            best_env = dict(experiment["env"])

    if best_env is not None and int(best_env.get("NASA_HUMP_END_TIME", "0")) < 420:
        final_tag = f"{best_tag}_final420"
        final_case_dir = SWEEP_ROOT / final_tag
        final_env = dict(best_env)
        final_env["NASA_HUMP_END_TIME"] = "420"

        copy_template(final_case_dir)
        local_generate(final_case_dir, final_env)

        start = time.time()
        copy_to_container(final_case_dir)
        run_case_in_container(final_case_dir)
        copy_from_container(final_case_dir)
        runtime_minutes = (time.time() - start) / 60.0

        result = evaluate_case(final_case_dir, final_tag)
        score = float(result["score"])
        row = {
            "tag": final_tag,
            "changes": f"Best shortlist configuration rerun to 420 iterations ({best_tag})",
            "note": "Final deeper-convergence follow-up for the strongest shortlisted configuration.",
            "end_time": int(float(result["time_directory"])),
            "runtime_minutes": runtime_minutes,
            "score": score,
            "case_dir": str(final_case_dir.relative_to(ROOT)),
        }
        rows.append(row)

        if score < best_score:
            best_score = score
            best_case_dir = final_case_dir
            best_tag = final_tag

    headers = ["tag", "case_dir", "changes", "end_time", "runtime_minutes", "score", "note"]
    with SUMMARY_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "baseline_score": float(baseline["score"]),
        "best_tag": best_tag,
        "best_score": best_score,
        "score_improvement_vs_baseline": float(baseline["score"]) - best_score,
        "rows": rows,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2))
    record_notes(rows)

    if best_case_dir != BASE_CASE:
        clean_case_dir(BASE_CASE)
        shutil.copytree(best_case_dir, BASE_CASE, dirs_exist_ok=True)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
