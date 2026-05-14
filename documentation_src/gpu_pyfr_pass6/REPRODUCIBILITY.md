# GPU PyFR PASS 6 Reproducibility

## 1. Connect to Gilbreth
```bash
ssh gilbreth
cd /scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git
```

## 2. Submit the stability sweep
```bash
bash scripts/submit_pyfr_pass6_stability_sweep_gilbreth.sh
```

## 3. Inspect sweep jobs
```bash
squeue -u "$USER"
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,ExitCode
```

## 4. Fetch PASS 6 sweep results locally
```bash
cd /Users/ashmitprabhu/github/nasa-hump2
scp -r \
  'gilbreth:/scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git/runs/gpu_pyfr_pass6/stability/pass6_*' \
  runs/gpu_pyfr_pass6/stability/
```

## 5. Audit finite fields locally
```bash
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/inspect_pyfr_vtu_fields.py \
  runs/gpu_pyfr_pass6/stability/pass6_hump_ns_char_dt5e5/pass6_hump_ns_char_dt5e5_latest.vtu \
  documentation_src/gpu_pyfr_pass6/data/stability_audits/pass6_hump_ns_char_dt5e5.json

'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/extract_pyfr_wall_pressure_pass5.py \
  runs/gpu_pyfr_pass6/stability/pass6_hump_ns_char_dt5e5/pass6_hump_ns_char_dt5e5_latest.vtu \
  data/experimental/NASA_hump/noflow_cp.csv \
  documentation_src/gpu_pyfr_pass6/data/cp_cases/pass6_hump_ns_char_dt5e5_wall.csv \
  documentation_src/gpu_pyfr_pass6/data/cp_cases/pass6_hump_ns_char_dt5e5_cp.csv

'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' \
  scripts/map_pyfr_to_benchmark_pass6.py \
  --vtu runs/gpu_pyfr_pass6/stability/pass6_hump_ns_char_dt5e5/pass6_hump_ns_char_dt5e5_latest.vtu \
  --field-audit documentation_src/gpu_pyfr_pass6/data/stability_audits/pass6_hump_ns_char_dt5e5.json \
  --prediction-csv documentation_src/gpu_pyfr_pass6/data/benchmark_cases/pass6_hump_ns_char_dt5e5_predictions.csv \
  --sample-csv documentation_src/gpu_pyfr_pass6/data/benchmark_cases/pass6_hump_ns_char_dt5e5_samples.csv \
  --summary-json documentation_src/gpu_pyfr_pass6/data/benchmark_cases/pass6_hump_ns_char_dt5e5_metrics.json
```

## 6. Score the benchmark predictions with the repo Python
```bash
python3 - <<'PY'
import json, numpy as np
from pathlib import Path
from closure_challenge.eval import evaluate_individual_case
metrics = Path('documentation_src/gpu_pyfr_pass6/data/benchmark_cases/pass6_hump_ns_char_dt5e5_metrics.json')
pred = np.loadtxt('documentation_src/gpu_pyfr_pass6/data/benchmark_cases/pass6_hump_ns_char_dt5e5_predictions.csv', delimiter=',')
data = json.loads(metrics.read_text())
data['score'] = float(evaluate_individual_case('NASA_2DWMH', pred))
data['score_available'] = True
metrics.write_text(json.dumps(data, indent=2))
PY
```

## 7. Build the PASS 6 summary package
```bash
MPLCONFIGDIR=docs/.mplconfig python3 scripts/postprocess_gpu_pyfr_pass6_stability.py
```

## 8. Render PASS 6 ParaView figures
```bash
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass6_paraview.py mesh
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass6_paraview.py velocity
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass6_paraview.py pressure
'/Users/ashmitprabhu/Desktop/ParaView-6.1.0-RC1.app/Contents/bin/pvpython' scripts/render_gpu_pyfr_pass6_paraview.py streamlines
```

## 9. Build the report
```bash
bash scripts/build_report.sh
```
