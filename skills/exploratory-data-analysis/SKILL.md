---
name: exploratory-data-analysis
description: Inspect a scientific data file and report its structure and quality in a bounded Markdown report. Use when triaging an unknown table, array, sequence, image or mass-spectrometry file.
---

# Exploratory Data Analysis

Inspect a scientific file before downstream analysis. `scripts/eda_analyzer.py` recognizes more than 100 suffixes and writes a bounded Markdown report. It parses content only for the formats below; every other recognized suffix gets file metadata and a reference-catalog entry.

**Parsed by the script:**
- NumPy arrays (`.npy`, `.npz`), CSV/TSV samples, JSON, HDF5
- FASTA and FASTQ, including common gzip-compressed suffixes
- TIFF/OME-TIFF, PNG, JPEG
- Streaming analyzers for PDB/SDF/SMILES, MGF/mzML/mzXML and mzTab families

**Reference-only:** every other recognized suffix, and proprietary binary formats unless the project environment supplies a reader.

## Instructions

1. Run the installed analyzer (PEP 723 metadata creates an isolated environment with the parser libraries):

   ```bash
   uv run ~/.agents/skills/exploratory-data-analysis/scripts/eda_analyzer.py <filepath> [output.md]
   ```

   The default report is `<input stem>_eda_report.md` next to the input file. For several related files, write one report each, then add a short comparison covering shared structure and mismatches before recommending an integration path.
2. For a format the script does not parse, look up the extension in the reference catalog, read only that entry, and run a custom analysis with the libraries it names. Add a missing parser with `uv run --with <package> python analysis.py`.
3. Reference catalogs in `references/` (the script reads them): `chemistry_molecular_formats.md`, `bioinformatics_genomics_formats.md`, `microscopy_imaging_formats.md`, `spectroscopy_analytical_formats.md`, `proteomics_metabolomics_formats.md`, `general_scientific_formats.md`. Each is 2,000 to 2,800 words; never load one whole. Grep the heading (for example `"### .pdb"`) and extract that entry: format description, typical data, use cases, Python libraries, recommended EDA approach. Entries can repeat a suffix in different domain contexts. If an extension is in none, ask the user for the format and check for a vendor variant.
4. Report sections (a template is in `assets/report_template.md`): title and metadata; basic information and format identification; format details from the reference entry; data analysis (structure, dimensions, statistical summaries, quality); key findings; recommendations (preprocessing, analyses, tools, visualization). Figures follow `/beautiful-data-viz`.

## Large files

Sample, and label every sample as a sample. Use memory mapping for HDF5 and NPY, chunks for CSV and FASTQ, and estimates from samples. The script memory-maps `.npy`, streams FASTA in full, and reads FASTQ as an explicitly bounded streaming sample. On a shared login node inspect only small samples; follow `hpc-slurm` for full-file inspection.

## Input Requirements

A local data file, read permission, and enough disk and RAM for the inspection. Domain context (assay, organism, instrument, expected sample count) helps.

## Output

The Markdown report (metadata, detected format and parser, structure summary, quality observations, issues, recommendations), plus any figures that support it.

## Quality Gates

- The report states the detected file type and the reference entry used.
- It separates observed facts from recommendations, and reports missing values, malformed records, parser failures and unreadable sections explicitly.
- Sampled statistics are labeled as sampled.
