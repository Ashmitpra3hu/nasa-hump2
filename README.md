# NASA Hump Reconstruction

The primary document for this repository is the PDF report:

- `documentation/pass_one.pdf`
- `documentation/pass_two.pdf`

This repository includes a locally reconstructed NASA wall-mounted hump baseline case built under strict no-cheating constraints.

## Main Documentation

- First-pass PDF: `documentation/pass_one.pdf`
- Second-pass PDF: `documentation/pass_two.pdf`
- LaTeX report sources: `documentation_src/`
- Bibliography: `documentation_src/references.bib`
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
python3 scripts/evaluate_nasa_hump_second_pass.py
```

## Current Reconstructed NASA Score

The locally reconstructed NASA case was evaluated against the benchmark NASA points and produced:

- `NASA_2DWMH`: `0.2338504550`

The prediction CSV and score summary are stored in:

- `docs/data/reconstructed_nasa_predictions.csv`
- `docs/data/reconstructed_nasa_score.json`
- `documentation_src/data_second_pass/reconstructed_nasa_predictions_second_pass.csv`
- `documentation_src/data_second_pass/reconstructed_nasa_score_second_pass.json`
