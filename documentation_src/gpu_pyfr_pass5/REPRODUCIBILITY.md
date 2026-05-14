# GPU PyFR PASS 5 Reproducibility

## 1. Sync the repository to Gilbreth
```bash
cd /Users/ashmitprabhu/github/nasa-hump2
bash scripts/sync_gpu_pyfr_pass1_to_gilbreth.sh
```

## 2. Connect to Gilbreth
```bash
ssh gilbreth
cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
```

## 3. Submit the diagnostic run
```bash
bash scripts/submit_pyfr_pass5_diagnostic_gilbreth.sh
```

## 4. Inspect queue/job status
```bash
squeue -u "$USER"
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,ExitCode
```

## 5. Submit the promoted run after the diagnostic run is finite
```bash
bash scripts/submit_pyfr_pass5_promoted_gilbreth.sh
```

## 6. Fetch PASS 5 results back locally
```bash
cd /Users/ashmitprabhu/github/nasa-hump2
bash scripts/fetch_gpu_pyfr_pass5_results.sh
```

## 7. Audit VTU fields and extract wall pressure
```bash
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/inspect_pyfr_vtu_fields.py \
  runs/gpu_pyfr_pass4/long/pass4_long_latest.vtu \
  documentation_src/gpu_pyfr_pass5/data/pyfr_vtu_field_audit.json

'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/extract_pyfr_wall_pressure_pass5.py \
  runs/gpu_pyfr_pass5/diagnostic/pass5_diagnostic_latest.vtu \
  data/experimental/NASA_hump/noflow_cp.csv \
  documentation_src/gpu_pyfr_pass5/data/pyfr_wall_cp.csv \
  documentation_src/gpu_pyfr_pass5/data/cp_comparison.csv
```

If a promoted run exists, use its VTU path instead of the diagnostic VTU.

## 8. Build figures and summaries
```bash
MPLCONFIGDIR=docs/.mplconfig python3 scripts/postprocess_gpu_pyfr_pass5.py
```

## 9. Render ParaView figures
```bash
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass5_paraview.py mesh
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass5_paraview.py velocity
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass5_paraview.py pressure
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass5_paraview.py streamlines
```

## 10. Build the PDF
```bash
bash scripts/build_report.sh
```
