# Optional GPU mapping

The driver maps on the CPU with `bwa-mem2` and `minimap2`. Use a GPU mapper only when the hardware is there and the run goes through the scheduler on a GPU node (`hpc-slurm` has the account and queue rules). Check a GPU result against the CPU path on a small subset first, and record the tool, version and GPU device in `tasks/METHODS.md`.

- Short reads: NVIDIA Parabricks `fq2bam` (GPU BWA-MEM with sorting and duplicate marking).
- Long reads: Parabricks `minimap2`, with presets `map-ont`, `map-hifi` and `lr:hq`.
- The CPU and GPU forks `mm2-fast` and `mm2-gb` are built on minimap2 v2.24, which is older than the version in [docs/README.md](../docs/README.md). Use them only when that older base is acceptable.
