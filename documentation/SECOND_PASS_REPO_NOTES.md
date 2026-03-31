# Second-Pass Repo Notes

## Local Repository Patterns Re-Checked For Pass 2

This note records what was learned from the surviving local repository materials during the second pass. It supplements `CASE_PATTERN_SUMMARY.md` by focusing specifically on what is reusable for refinement, reporting, evaluation, and graph production.

## Folder Structure Patterns

- Benchmark data live under `data/`.
- A case is typically organized around:
  - `0/`
  - `constant/`
  - `system/`
  - top-level case metadata such as `caseDef` and `fieldDef`
- Runtime outputs are stored beside the case rather than hidden elsewhere:
  - `log.*`
  - `postProcessing/`
  - `VTK/`
  - `.foam`

## Workflow Patterns

- The repo favors short shell scripts with clear sequencing rather than heavy framework tooling.
- The NASA case already follows that style with separate scripts for build, run, post-process, figure generation, and report build.
- Existing evaluation utilities live in `scripts/` and write machine-readable outputs into `docs/data/`.

## Reporting Patterns

- The repository already treats the PDF report as the primary top-level deliverable through `README.pdf`.
- The LaTeX report is self-contained in `documentation/`, with a compiled artifact under `documentation/build/`.
- Figures live under `docs/figures/`, which is therefore the most consistent place to store second-pass images too.

## Sampling And Post-Processing Patterns

- The first-pass NASA case already uses separate small dictionaries in `system/` for residuals and station sampling.
- This matches the broader repository preference for small, readable dictionaries rather than one oversized `controlDict`.
- The evaluation workflow is external to OpenFOAM and uses the final field plus the local benchmark point file under `data/evaluation_points/`.

## Reusable Local Materials For Pass 2

- `CASE_PATTERN_SUMMARY.md` for the reconstructed case layout target.
- `NO_CHEAT_PLAN.md` and `RECONSTRUCTION_AUDIT.md` for compliance style.
- `documentation/main.tex` as the first-pass report baseline.
- `scripts/evaluate_reconstructed_nasa_case.py` as the baseline accuracy workflow.
- `scripts/render_nasa_hump_paraview.py` and `scripts/render_nasa_hump_paraview.sh` as the ParaView workflow baseline.
- `docs/data/reconstructed_nasa_score.json` and `docs/data/summary.json` as first-pass numerical reference points.

## Local PDF / Documentation Note

- The surviving local PDF `submissions/wu/description_document.pdf` is present in the repository.
- It is treated only as a local repository artifact and not as an external online source.
- Because the second pass is centered on the rebuilt NASA case rather than on reverse-engineering another submission, this PDF is used only as evidence that local report-style artifacts exist in the repository, not as a source of copied NASA-case content.

## Pass-2 Reuse Decision

The second pass should preserve the existing repository style:

- case outputs remain under `data/NASA_2DWMH`
- plots and tables remain under `docs/`
- the new refinement report remains under `documentation/`
- accuracy, figure generation, and reproducibility continue to be driven by short scripts in `scripts/`
