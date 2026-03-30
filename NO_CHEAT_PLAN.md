# No-Cheat Reconstruction Plan

## 1. Allowed Sources

- The single allowed reference page: `https://tmbwg.github.io/turbmodels/nasahump_val.html`
- The current working tree in this repository after deletion of the original NASA hump case
- OpenFOAM and its built-in tools, executed through Docker
- New scripts, meshes, dictionaries, plots, figures, and documentation created during this task

## 2. Forbidden Sources

- Any website, paper, repo, forum, issue, PR, gist, PDF, or online resource other than the single allowed page
- Any Git history, reflog, stash, old commit, branch, tag, hidden backup, editor history, trash, local snapshot, or cached copy
- Any attempt to recover the deleted NASA hump case from version control or the filesystem
- Any NASA hump files copied from another source

## 3. How I Will Avoid Accidental Use of Deleted or Historical Content

- I will not run `git log`, `git show`, `git diff`, `git checkout`, `git restore`, `git reflog`, or similar history-retrieval commands.
- I will only inspect files that currently exist in the working tree.
- I will build a new case in a fresh directory rather than trying to recreate the deleted layout from hidden state.
- I will keep all online access restricted to the single allowed validation page.
- I will record commands in the final audit so the reconstruction path stays reviewable.

## 4. How I Will Document Assumptions

- Every geometry, boundary-condition, mesh, solver, turbulence-model, and sampling assumption will be written into the case notes, report, and final audit.
- If the allowed page does not fully specify a detail, I will choose the most defensible interpretation based on that page plus surviving repository conventions, then label it explicitly as an assumption.
- If a result reflects a practical compromise for Docker/OpenFOAM compatibility, that will be documented separately from physical assumptions.

## 5. Step-by-Step Reconstruction Plan

1. Read the allowed NASA hump validation page and extract only the information needed for a baseline no-flow-control case, preferably without plenum.
2. Inspect surviving repository cases to infer directory layout, naming, metadata files, run scripts, and post-processing conventions.
3. Write `CASE_PATTERN_SUMMARY.md` to capture the repository style that the new case should follow.
4. Create a fresh NASA hump case directory, helper scripts, and documentation files without referencing deleted or historical content.
5. Reconstruct the hump geometry from the allowed page and defensible in-repo conventions, then generate an OpenFOAM mesh from original inputs created in this task.
6. Define initial fields, transport properties, turbulence settings, solver controls, and sampling dictionaries for at least one credible baseline RANS case.
7. Run the case only through Dockerized OpenFOAM, fix setup issues, and keep the workflow reproducible through shell scripts.
8. Post-process the run into sampled data, residual data, plots, and ParaView-friendly outputs including a `.foam` file.
9. Build a polished LaTeX report covering methodology, assumptions, workflow, settings, results, limitations, and compliance.
10. Write `RECONSTRUCTION_AUDIT.md` listing files changed, commands used, assumptions made, outputs produced, and explicit proof that no forbidden source was used.
