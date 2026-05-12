# GPU PyFR PASS 3 Reproducibility

## 1. Connect to Gilbreth

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
ssh gilbreth
```

## 2. Go to the scratch repo

```bash
cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
```

## 3. Refresh the PyFR environment if needed

```bash
bash scripts/setup_gilbreth_pyfr_env.sh
```

## 4. Submit the PASS 3 minimal hump run

```bash
bash scripts/submit_pyfr_pass3_minimal_gilbreth.sh
```

Optional overrides:

```bash
PYFR_PARTITION=a100-40gb PYFR_MEM=16G PYFR_WALLTIME=00:05:00 \
  bash scripts/submit_pyfr_pass3_minimal_gilbreth.sh
```

## 5. Track the job

```bash
squeue -u prabhu56
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,ExitCode
```

## 6. Fetch the completed results locally

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
bash scripts/fetch_gpu_pyfr_pass3_results.sh
```

## 7. Generate PASS 3 figures and summary tables

```bash
MPLCONFIGDIR=docs/.mplconfig python3 scripts/postprocess_gpu_pyfr_pass3.py
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass3_paraview.py velocity
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass3_paraview.py pressure
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass3_paraview.py mesh
```

## 8. Build the PDF

```bash
bash scripts/build_report.sh
```
