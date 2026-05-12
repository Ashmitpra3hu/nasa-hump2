# GPU PyFR PASS 2 Reproducibility

## 1. Connect to Gilbreth

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
ssh gilbreth
```

## 2. Go to the PASS workspace

```bash
cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
```

PASS 2 intentionally reuses the PASS 1 scratch workspace and Python environment so the delta stays focused on the hump-case robustness fixes.

## 3. Environment setup

If the PyFR environment does not already exist or needs refreshing:

```bash
bash scripts/setup_gilbreth_pyfr_env.sh
```

## 4. Mesh check

Run the local mesh audit helper on Gilbreth before submission:

```bash
python3 scripts/pyfr/check_pyfr_hump_mesh.py --variant minimal
```

## 5. Minimal no-sampler hump submission

```bash
bash scripts/submit_pyfr_pass2_minimal_gilbreth.sh
```

## 6. Optional sampler ladder

Only attempt these after the minimal no-sampler run completes and writes solution output:

```bash
bash scripts/submit_pyfr_pass2_minimal_gilbreth.sh field_only
bash scripts/submit_pyfr_pass2_minimal_gilbreth.sh sparse_wall
bash scripts/submit_pyfr_pass2_minimal_gilbreth.sh full_wall
```

## 7. Track Slurm jobs

```bash
squeue -u prabhu56
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,MaxRSS
```

## 8. Fetch lightweight results back locally

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
bash scripts/fetch_gpu_pyfr_pass2_results.sh
```

## 9. Local postprocessing

```bash
python3 scripts/postprocess_gpu_pyfr_pass2.py
```

## 10. Build the PASS 2 PDF

```bash
bash scripts/build_report.sh
```
