# GPU PyFR PASS 1 Reproducibility

This directory holds the LaTeX source and supporting notes for the first GPU PyFR NASA hump attempt on Purdue Gilbreth.

## Local-to-Gilbreth Workflow

1. From the local repo:

   ```bash
   cd /Users/ashmitprabhu/github/nasa-hump2
   ssh gilbreth
   ```

2. On Gilbreth, prepare the user environment:

   ```bash
   cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
   bash scripts/setup_gilbreth_pyfr_env.sh
   ```

3. Submit the smoke job:

   ```bash
   bash scripts/submit_pyfr_smoke_gilbreth.sh
   ```

4. If the smoke job succeeds, submit the medium NASA hump run:

   ```bash
   bash scripts/submit_pyfr_medium_gilbreth.sh
   ```

5. If the medium run is stable enough, submit the promoted run:

   ```bash
   bash scripts/submit_pyfr_promoted_gilbreth.sh
   ```

6. Track jobs on Gilbreth:

   ```bash
   squeue -u prabhu56
   sacct -j <jobid> --format=JobID,JobName,State,Elapsed,MaxRSS
   ```

7. Back on the local machine, fetch lightweight results and postprocess:

   ```bash
   bash scripts/fetch_gpu_pyfr_pass1_results.sh
   python3 scripts/postprocess_gpu_pyfr_pass1.py
   bash scripts/build_report.sh
   ```

## Notes

- The workflow is intentionally split between remote execution and local postprocessing because the NASA comparison plots and PDF report are maintained in the repo’s existing local documentation pipeline.
- Heavy PyFR solution files and transient scratch data are kept on Gilbreth scratch; lightweight CSV summaries, logs, and figures are the main repo-facing artifacts.
