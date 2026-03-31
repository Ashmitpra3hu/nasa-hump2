# MAE Experiment Notes

This file records the post-second-pass NASA hump MAE sweep run against the local benchmark metric.

| Tag | Key changes | End time | Runtime (min) | MAE | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| baseline_second_pass | Existing best second-pass reference | 300 | 0.00 | 0.2038187409 | Reference row carried forward from the current repo state. |
| exp_uniform_sst_500 | Current best second-pass baseline rerun deeper with uniform inlet and SST to 500 iterations | 500 | 20.72 | 0.1801372055 | Direct convergence-extension test on the strongest known configuration. |
