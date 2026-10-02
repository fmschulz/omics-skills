# Environments: pinning and capturing software

Pinning and capturing exact software environments so a rerun uses the identical stack (Sandve 2013, Rule 3; Wilson 2017, "make dependencies explicit"). Read this when setting up or recording a project's software environment.

**House rule:** bioinformatics tool stacks use **pixi** (conda-forge + bioconda); Python-only deps use **uv**; never use the system Python or run `conda`/`pip` against a base environment.

## Contents

- pixi for bioinformatics tool stacks
- uv for Python dependencies
- Sharing with conda-based collaborators (pixi export)
- Containers (Docker / Apptainer / Singularity)
- Recording exact versions into results

## pixi for bioinformatics tool stacks

Pixi resolves a conda environment from a `pixi.toml` manifest and writes a `pixi.lock` with exact, cross-platform pinned versions. Commit both. Channels for bioinformatics are `conda-forge` and `bioconda` (order matters: `conda-forge` first).

```bash
pixi init metagenome_mags_project          # create pixi.toml
pixi add bwa samtools fastp seqkit         # newest releases; pixi.lock records them
pixi install                               # resolve + write pixi.lock
pixi run bwa mem ...                        # run a tool from the env
pixi shell                                  # drop into the env
```

- A minimal pinned manifest with channels and a lock-capture comment: `examples/environment.pixi.toml`.
- `pixi.lock` is the reproducibility artifact — it pins exact builds. Always commit it.
- Recreate the exact env elsewhere: `pixi install` against the committed `pixi.lock`.

## uv for Python dependencies

For the project's own Python code and its libraries (pysam, Biopython, pandas), use uv — not system Python, not conda pip.

```bash
uv init                                     # create pyproject.toml
uv add pysam biopython pandas               # add deps, writes uv.lock
uv run python src/parse_checkm.py ...       # run in the locked env
uv sync                                      # recreate env from uv.lock
```

Commit `pyproject.toml` and `uv.lock`. Keep the heavy bioinformatics binaries (aligners, samtools) in pixi and the Python analysis libraries in uv; they coexist cleanly.

## Sharing with conda-based collaborators (pixi export)

Keep pixi as the source of truth; do not maintain a separate conda environment. When a collaborator needs a conda file, export it from the workspace.

```bash
pixi workspace export conda-environment environment.yml   # conda environment.yaml from pixi.toml
pixi workspace export conda-explicit-spec conda-spec/     # fully pinned explicit spec from pixi.lock
```

Regenerate exported files after every change to `pixi.toml` or `pixi.lock`, and never edit them by hand. To reproduce an older conda-based project, import its file into pixi instead of running conda: `pixi init --import environment.yml`.

## Containers (Docker / Apptainer / Singularity)

For long-lived, shared, or published analyses, capture the whole environment as an image built `FROM` a locked env so the exact tool that produced a result is preserved (Sandve 2013).

```dockerfile
# Dockerfile — build the analysis env from the committed pixi lock
FROM ghcr.io/prefix-dev/pixi:latest
WORKDIR /project
COPY pixi.toml pixi.lock ./
RUN pixi install --locked        # exact versions from pixi.lock
COPY . .
ENTRYPOINT ["pixi", "run"]
```

```bash
docker build -t mags-pipeline:1.0 .
docker run --rm -v "$PWD:/project" mags-pipeline:1.0 ./results/2026-03-30_qc_trim_assemble_bin/runall

# HPC without Docker: build/run with Apptainer (formerly Singularity)
apptainer build mags-pipeline_1.0.sif docker://mags-pipeline:1.0
apptainer exec --bind "$PWD" mags-pipeline_1.0.sif ./runall
```

Tag the image version to match the Git release that produced the figures.

## Recording exact versions into results

Pinning is not enough — write the actual versions used into each experiment's provenance file at run time, and into `tasks/METHODS.md`. The driver script does this as its first action (see `examples/runall.sh`):

```bash
{
  echo "# provenance  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host: $(uname -a)"
  echo "git: $(git rev-parse HEAD 2>/dev/null || echo 'not a repo')"
  echo "seed: ${SEED}"
  for tool in fastqc fastp metaspades.py bwa minimap2 samtools metabat2; do
    command -v "$tool" >/dev/null 2>&1 && printf '%s: ' "$tool" && "$tool" --version 2>&1 | head -n1
  done
} > provenance.txt
```

This makes the result self-describing: a reviewer opening the experiment dir sees the exact tool versions, the Git commit, and the random seed that produced it.
