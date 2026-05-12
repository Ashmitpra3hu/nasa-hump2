# GPU PyFR PASS 3 Notes

PASS 3 was created because PASS 2 had already removed the sampler-first design problem, but the first legal Slurm submissions were still pointed at GPU partitions the `rmaulik` association could not use. The decisive PASS 3 fixes were:

1. submit only to `a100-40gb`, which the account is actually allocated,
2. shorten the hump run to a five-minute no-sampler backfill target,
3. remove the wall-force helper from the minimal case so the first milestone is just solution writing,
4. fetch and postprocess the raw VTU externally instead of depending on PyFR samplers.

The successful PASS 3 GPU job was Slurm job `10702409` on host `gilbreth-n017.rcac.purdue.edu`.
