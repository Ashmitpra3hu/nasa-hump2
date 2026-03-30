# NASA Hump Reconstruction

This repository now includes a locally reconstructed NASA wall-mounted hump baseline case built under strict no-cheating constraints.

## Main Documentation

- LaTeX report source: `documentation/main.tex`
- Bibliography: `documentation/references.bib`
- Audit trail: `RECONSTRUCTION_AUDIT.md`
- No-cheat plan: `NO_CHEAT_PLAN.md`
- Repo-pattern summary: `CASE_PATTERN_SUMMARY.md`

## Reconstructed Case

- OpenFOAM case: `data/NASA_2DWMH`
- ParaView marker: `data/NASA_2DWMH/foam.foam`
- Figures: `docs/figures`
- Machine-readable outputs: `docs/data`

## Workflow

Run everything from the repository root:

```bash
bash scripts/build_nasa_hump_case.sh
bash scripts/run_nasa_hump_case.sh
bash scripts/postprocess_nasa_hump_case.sh
bash scripts/make_figures.sh
bash scripts/build_report.sh
python3 scripts/evaluate_reconstructed_nasa_case.py
```

## Current Reconstructed NASA Score

The locally reconstructed NASA case was evaluated against the benchmark NASA points and produced:

- `NASA_2DWMH`: `0.2338504550`

The prediction CSV and score summary are stored in:

- `docs/data/reconstructed_nasa_predictions.csv`
- `docs/data/reconstructed_nasa_score.json`
