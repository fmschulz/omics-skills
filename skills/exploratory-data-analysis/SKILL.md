---
name: exploratory-data-analysis
description: Inspect a scientific data file and report its structure and quality. Use when triaging an unknown table, array, sequence or image file.
---

# Exploratory Data Analysis

## Overview

Inspect scientific files before downstream analysis. The bundled script recognizes more than 100 simple and compound suffixes and writes a bounded Markdown report. It performs content-level analysis only for the common formats listed below; other recognized formats receive file metadata and a reference-catalog entry.

The six reference files contain 239 format entries. Some entries describe the same suffix in different domain contexts, so this is not a count of unique formats or implemented parsers.

**Bundled content parsers:**
- NumPy arrays (`.npy`, `.npz`), CSV/TSV samples, JSON, and HDF5
- FASTA and FASTQ, including common gzip-compressed suffixes
- TIFF/OME-TIFF, PNG, and JPEG raster images
- Reference-only metadata for every other recognized suffix
- Representative streaming analyzers for PDB/SDF/SMILES, MGF/mzML/mzXML, and mzTab families; proprietary binary formats remain reference-only unless their project environment supplies a reader.

## Quick Reference

| Task | Action |
|------|--------|
| Unknown file | Detect extension and load the matching reference file before analyzing content. |
| Tabular data | Summarize dimensions, types, missingness, ranges, outliers, duplicates, and candidate keys. |
| Sequence data | Count records, length distribution, GC content, quality scores when available, and format issues. |
| Imaging or arrays | Report shape, channels/axes, dtype, value range, metadata, and scale/calibration when present. |
| Final report | Write a concise Markdown EDA report with findings, caveats, and next analysis options. |

## Supported File Categories

The reference catalog is organized into six categories. These entries guide custom analysis; they do not imply that `eda_analyzer.py` parses every listed format.

### 1. Chemistry and Molecular Formats (43 reference entries)
Structure files, computational chemistry outputs, molecular dynamics trajectories, and chemical databases.

**File types include:** `.pdb`, `.cif`, `.mol`, `.mol2`, `.sdf`, `.xyz`, `.smi`, `.gro`, `.log`, `.fchk`, `.cube`, `.dcd`, `.xtc`, `.trr`, `.prmtop`, `.psf`, and more.

**Reference file:** `references/chemistry_molecular_formats.md`

### 2. Bioinformatics and Genomics Formats (44 reference entries)
Sequence data, alignments, annotations, variants, and expression data.

**File types include:** `.fasta`, `.fastq`, `.sam`, `.bam`, `.vcf`, `.bed`, `.gff`, `.gtf`, `.bigwig`, `.h5ad`, `.loom`, `.counts`, `.mtx`, and more.

**Reference file:** `references/bioinformatics_genomics_formats.md`

### 3. Microscopy and Imaging Formats (41 reference entries)
Microscopy images, medical imaging, whole slide imaging, and electron microscopy.

**File types include:** `.tif`, `.nd2`, `.lif`, `.czi`, `.ims`, `.dcm`, `.nii`, `.mrc`, `.dm3`, `.vsi`, `.svs`, `.ome.tiff`, and more.

**Reference file:** `references/microscopy_imaging_formats.md`

### 4. Spectroscopy and Analytical Chemistry Formats (43 reference entries)
NMR, mass spectrometry, IR/Raman, UV-Vis, X-ray, chromatography, and other analytical techniques.

**File types include:** `.fid`, `.mzML`, `.mzXML`, `.raw`, `.mgf`, `.spc`, `.jdx`, `.xy`, `.cif` (crystallography), `.wdf`, and more.

**Reference file:** `references/spectroscopy_analytical_formats.md`

### 5. Proteomics and Metabolomics Formats (36 reference entries)
Mass spec proteomics, metabolomics, lipidomics, and multi-omics data.

**File types include:** `.mzML`, `.pepXML`, `.protXML`, `.mzid`, `.mzTab`, `.sky`, `.mgf`, `.msp`, `.h5ad`, and more.

**Reference file:** `references/proteomics_metabolomics_formats.md`

### 6. General Scientific Data Formats (32 reference entries)
Arrays, tables, hierarchical data, compressed archives, and common scientific formats.

**File types include:** `.npy`, `.npz`, `.csv`, `.xlsx`, `.json`, `.hdf5`, `.zarr`, `.parquet`, `.mat`, `.fits`, `.nc`, `.xml`, and more.

**Reference file:** `references/general_scientific_formats.md`

## Instructions

### Step 1: File Type Detection

When a user provides a file path, first identify the file type:

1. Extract the file extension
2. Look up the extension in the appropriate reference file
3. Identify the file category and format description
4. Load format-specific information

**Example:**
```
User: "Analyze data.fastq"
→ Extension: .fastq
→ Category: bioinformatics_genomics
→ Format: FASTQ Format (sequence data with quality scores)
→ Reference: references/bioinformatics_genomics_formats.md
```

### Step 2: Load Format-Specific Information

Based on the file type, read the corresponding reference file to understand:
- **Typical Data:** What kind of data this format contains
- **Use Cases:** Common applications for this format
- **Python Libraries:** How to read the file in Python
- **EDA Approach:** What analyses are appropriate for this data type

Search the reference file for the specific extension (e.g., search for "### .fastq" in `bioinformatics_genomics_formats.md`).

### Step 3: Perform Data Analysis

Use the bundled script for its supported parsers, or implement a domain-specific analysis after reading the relevant reference entry.

**Option A: Run the analyzer from the checkout**
```bash
uv run skills/exploratory-data-analysis/scripts/eda_analyzer.py <filepath> [output.md]
```

**Option B: Run the installed analyzer**
```bash
uv run ~/.agents/skills/exploratory-data-analysis/scripts/eda_analyzer.py <filepath> [output.md]
```

PEP 723 metadata in the script creates an isolated environment with the libraries used by its content parsers.

**Option C: Custom analysis in the conversation**
Based on the format information from the reference file, perform appropriate analysis:

For tabular data (CSV, TSV, Excel):
- Load with pandas
- Check dimensions, data types
- Analyze missing values
- Calculate summary statistics
- Identify outliers
- Check for duplicates

For sequence data (FASTA, FASTQ):
- Count sequences
- Analyze length distributions
- Calculate GC content
- Assess quality scores (FASTQ)

For images (TIFF, ND2, CZI):
- Check dimensions (X, Y, Z, C, T)
- Analyze bit depth and value range
- Extract metadata (channels, timestamps, spatial calibration)
- Calculate intensity statistics

For arrays (NPY, HDF5):
- Check shape and dimensions
- Analyze data type
- Calculate statistical summaries
- Check for missing/invalid values

### Step 4: Generate the Report

The bundled script reports file metadata, the matching reference entry, sampled or full content statistics, parser errors, and format-level follow-up options. Label every sample explicitly. For a custom analysis, use the following sections:

#### Required Sections:
1. **Title and Metadata**
   - Filename and timestamp
   - File size and location

2. **Basic Information**
   - File properties
   - Format identification

3. **File Type Details**
   - Format description from reference
   - Typical data content
   - Common use cases
   - Python libraries for reading

4. **Data Analysis**
   - Structure and dimensions
   - Statistical summaries
   - Quality assessment
   - Data characteristics

5. **Key Findings**
   - Notable patterns
   - Potential issues
   - Quality metrics

6. **Recommendations**
   - Preprocessing steps
   - Appropriate analyses
   - Tools and methods
   - Visualization approaches (any figures follow `/beautiful-data-viz`: greyscale first, color only to encode information)

#### Template Location
Use `assets/report_template.md` as a guide for report structure.

### Step 5: Save Report

Save the markdown report with a descriptive filename:
- Pattern: `{original_filename}_eda_report.md`
- Example: `experiment_data.fastq` → `experiment_data_eda_report.md`

For multiple related files, write one report per file, then add a short comparison summary covering shared structure, mismatches, and how the files relate before recommending an integration path.

## Detailed Format References

Reference files are large (10,000+ words each); do not load one whole. Search for the section heading matching the extension (e.g., grep `"### .pdb"` in `references/chemistry_molecular_formats.md`) and extract just that entry. Each entry gives the format description, typical data, use cases, Python libraries with code examples, and the recommended EDA approach. When analyzing several files of the same type, reuse the extracted entry instead of re-reading the reference.

## Input Requirements

- One or more local scientific data files.
- Permission to read the files and enough disk/RAM for the requested inspection.
- Domain context when available, such as assay type, organism, instrument, or expected sample count.
- Optional output path for the Markdown report.

## Output

- Markdown EDA report next to the input file or at the requested output path.
- Basic file metadata: path, size, modified time, detected format, and relevant parser.
- Data structure summary, quality observations, likely issues, and downstream recommendations.
- Any generated figures (styled per `/beautiful-data-viz`), tables, or temporary summaries needed to support the report.

## Quality Gates

- [ ] File type detection and selected reference file are stated.
- [ ] The report distinguishes observed facts from downstream recommendations.
- [ ] Missing values, malformed records, parser failures, or unreadable sections are reported explicitly.
- [ ] Large-file sampling is labeled as sampling and does not imply full-file statistics.
- [ ] Suggested downstream analyses match the detected format and available metadata.
- [ ] NumPy `.npy` inspection uses memory mapping, FASTA uses full-file streaming, FASTQ is an explicitly bounded streaming sample, and each implemented format family has a fixture.

## Examples

### Example 1: Analyzing a FASTQ file

```python
# User provides: "Analyze reads.fastq"

# 1. Detect file type
extension = '.fastq'
category = 'bioinformatics_genomics'

# 2. Read reference info
# Search references/bioinformatics_genomics_formats.md for "### .fastq"

# 3. Perform analysis: stream records instead of loading the file into memory
from Bio import SeqIO
lengths = []
for record in SeqIO.parse('reads.fastq', 'fastq'):
    lengths.append(len(record))
    # also accumulate GC counts and per-read mean quality here

# 4. Generate report
# Include: format description, analysis results, QC recommendations

# 5. Save as: reads_eda_report.md
```

## Troubleshooting

### Missing Libraries

Custom analysis of formats outside the bundled parsers may require specialized libraries:

**Problem:** Import error when trying to read a file

**Solution:** Add the parser to the project environment with `uv`, or run a one-off command with `uv run --with`.
```bash
uv run --with biopython python analysis.py
```

Common requirements by category:
- **Bioinformatics:** `biopython`, `pysam`, `pyBigWig`
- **Chemistry:** `rdkit`, `mdanalysis`, `cclib`
- **Microscopy:** `tifffile`, `nd2reader`, `aicsimageio`, `pydicom`
- **Spectroscopy:** `nmrglue`, `pymzml`, `pyteomics`
- **General:** `pandas`, `numpy`, `h5py`, `scipy`

### Unknown File Types

If a file extension is not in the references:

1. Ask the user about the file format
2. Check if it's a vendor-specific variant
3. Attempt generic analysis based on file structure (text vs binary)
4. Provide general recommendations

### Large Files

For very large files:

1. Use sampling strategies (first N records)
2. Use memory-mapped access (for HDF5, NPY)
3. Process in chunks (for CSV, FASTQ)
4. Provide estimates based on samples

On a shared HPC login node, inspect only small samples. Submit full-file inspection as a batch job (`sbatch`) with explicit CPU, memory, and thread limits.
