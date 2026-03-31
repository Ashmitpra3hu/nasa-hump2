# Second-Pass Changelog

This changelog records files created or modified during the second pass. Tags are:

- `first-pass diagnosis`
- `accuracy improvement`
- `graph reimplementation`
- `ParaView output`
- `evaluation`
- `report/documentation`
- `workflow/reproducibility`
- `compliance/audit`

## Diagnosis / Compliance Files

- `documentation/FIRST_PASS_DIAGNOSIS.md`
  - tags: `first-pass diagnosis`, `report/documentation`, `compliance/audit`
- `documentation/SECOND_PASS_PLAN.md`
  - tags: `report/documentation`, `workflow/reproducibility`, `compliance/audit`
- `documentation/SECOND_PASS_WEBPAGE_SCAN.md`
  - tags: `report/documentation`, `compliance/audit`
- `documentation/SECOND_PASS_REPO_NOTES.md`
  - tags: `report/documentation`, `workflow/reproducibility`
- `documentation/NO_INTERPOLATION_DECLARATION.md`
  - tags: `compliance/audit`, `report/documentation`

## Case / Workflow Refinements

- `scripts/generate_nasa_hump_blockmesh.py`
  - tags: `accuracy improvement`, `workflow/reproducibility`
- `data/NASA_2DWMH/system/blockMeshDict`
  - tags: `accuracy improvement`
- `data/NASA_2DWMH/caseDef`
  - tags: `accuracy improvement`, `report/documentation`
- `data/NASA_2DWMH/system/controlDict`
  - tags: `accuracy improvement`
- `scripts/build_nasa_hump_case.sh`
  - tags: `workflow/reproducibility`
- `scripts/run_nasa_hump_case.sh`
  - tags: `workflow/reproducibility`
- `scripts/postprocess_nasa_hump_case.sh`
  - tags: `workflow/reproducibility`, `graph reimplementation`

## Second-Pass Data / Graph / Evaluation Scripts

- `scripts/make_nasa_hump_second_pass_figures.py`
  - tags: `graph reimplementation`, `report/documentation`
- `scripts/evaluate_nasa_hump_second_pass.py`
  - tags: `evaluation`, `workflow/reproducibility`
- `scripts/make_figures.sh`
  - tags: `graph reimplementation`, `workflow/reproducibility`
- `scripts/build_report.sh`
  - tags: `report/documentation`, `workflow/reproducibility`

## New Second-Pass Report Package

- `documentation/SECOND_PASS_CHANGELOG.md`
  - tags: `report/documentation`, `compliance/audit`
- `documentation/nasa_hump_second_pass_report.tex`
  - tags: `report/documentation`

## Generated Outputs To Be Refreshed By The Second-Pass Run

- `documentation/data_second_pass/*`
  - tags: `graph reimplementation`, `evaluation`, `report/documentation`
- `documentation/figures_second_pass/*`
  - tags: `graph reimplementation`, `ParaView output`, `report/documentation`
- `documentation/build/nasa_hump_second_pass_report.pdf`
  - tags: `report/documentation`
