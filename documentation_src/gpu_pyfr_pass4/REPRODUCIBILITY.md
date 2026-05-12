# GPU PyFR PASS 4 Reproducibility

## 1. Connect to Gilbreth

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
ssh gilbreth
```

## 2. Go to the scratch repo

```bash
cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
```

## 3. Refresh the environment if needed

```bash
bash scripts/setup_gilbreth_pyfr_env.sh
```

## 4. Submit the longer PASS 4 run

```bash
bash scripts/submit_pyfr_pass4_long_gilbreth.sh
```

Optional conservative overrides:

```bash
PYFR_PARTITION=a100-40gb PYFR_MEM=16G PYFR_WALLTIME=00:10:00 \
  bash scripts/submit_pyfr_pass4_long_gilbreth.sh
```

## 5. Track the Slurm job

```bash
squeue -u prabhu56
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,ExitCode
```

## 6. Fetch results locally

```bash
cd /Users/ashmitprabhu/github/nasa-hump2
bash scripts/fetch_gpu_pyfr_pass4_results.sh
```

## 7. Postprocess and extract Cp externally

```bash
MPLCONFIGDIR=docs/.mplconfig python3 scripts/postprocess_gpu_pyfr_pass4.py
```

## 8. Render ParaView figures from the VTU

```bash
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass4_paraview.py mesh
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass4_paraview.py velocity
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass4_paraview.py pressure
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/render_gpu_pyfr_pass4_paraview.py streamlines
```

## 9. Build the report

```bash
bash scripts/build_report.sh
```
