# Third-Pass Experiment Notes

This file records the third-pass NASA hump MAE sweep run against the local benchmark metric after the second-pass baseline had reached `0.2038187409`.

| Tag | Key changes | End time | Runtime (min) | MAE | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| `baseline_second_pass` | Existing best second-pass reference carried forward from the `300`-iteration field | 300 | 0.00 | 0.2038187409 | Starting point for pass three |
| `exp_tbl_sst_220` | Analytic turbulent-boundary-layer inlet for `U`, `k`, and `omega`; SST; stable transport | 200 | 8.34 | 0.2082901628 | Worse than baseline |
| `exp_tbl_sst_sharp_220` | Same analytic inlet; SST; sharper `k` and `omega` convection | 200 | 7.39 | 0.2085083473 | Worse than baseline |
| `exp_tbl_sst_sharp_meshtop_220` | Same analytic inlet; sharper transport; refined mesh; stronger blockage contour | 200 | 21.61 | 0.2216862912 | Clearly worse than baseline |
| `exp_tbl_komega_sharp_meshtop_180` | Same refined geometry path but with `kOmega` instead of SST | 150 | 8.01 | 0.2501395026 | Worst screened option |
| `exp_uniform_sst_500` | Kept the winning second-pass geometry, BCs, and SST model, but extended solve depth to `500` iterations | 500 | 20.72 | 0.1801372055 | Best third-pass result |

## Main Third-Pass Finding

The attempted inflow-profile, stronger-blockage, refined-mesh, and `kOmega` variants all degraded the local MAE relative to the existing second-pass baseline. The only third-pass change that honestly reduced the benchmark error was deeper convergence of the already-best SST baseline from `300` to `500` iterations.

## Why That Matters

- It shows that the second-pass case was still under-converged in benchmark space even though its residuals were already trending down.
- It reduces the temptation to overfit the setup with uncertain inlet or ceiling assumptions when the simpler explanation is still numerical convergence.
- It gives a physically conservative third-pass result because the governing geometry and baseline RANS model were left unchanged.
