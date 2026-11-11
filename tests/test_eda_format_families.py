import importlib.util
import json
import struct
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "exploratory-data-analysis"
SCRIPT = SKILL / "scripts" / "eda_analyzer.py"

spec = importlib.util.spec_from_file_location("eda_v15", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_representative_chemistry_spectrometry_and_proteomics_fixtures():
    fixture = SKILL / "fixtures"
    pdb = module.analyze_file(fixture / "structure.pdb")["data_analysis"]
    mgf = module.analyze_file(fixture / "spectra.mgf")["data_analysis"]
    mztab = module.analyze_file(fixture / "results.mztab")["data_analysis"]
    assert pdb["atom_records"] == 2 and pdb["heteroatom_records"] == 1
    assert mgf == {"analysis_scope": "streaming_full_file", "spectra": 1, "peak_rows": 2}
    assert mztab["protein_rows"] == 1 and mztab["psm_rows"] == 1


def test_large_format_paths_are_streaming_or_memory_mapped():
    source = SCRIPT.read_text()
    assert "np.load(filepath, mmap_mode='r')" in source
    assert "'analysis_scope': 'streaming_full_file'" in source
    assert "sequences = list(SeqIO.parse" not in source


def analyze_text_file(path):
    return module.analyze_file(path)["data_analysis"]


def run_cli_report(path: Path) -> str:
    """Run the script in its own uv environment (numpy, Pillow, Biopython)."""
    report = path.parent / "report.md"
    result = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(path), str(report)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return report.read_text(encoding="utf-8")


def report_statistics(report: str) -> dict:
    assert "**Analysis error:**" not in report, report
    _, block = report.split("### Summary Statistics")
    return json.loads(block.split("```json")[1].split("```")[0])


def write_blank_png(path: Path, width: int, height: int) -> None:
    """Write an all-zero 1-bit PNG; it stays small however many pixels it has."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return (
            struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))
        )

    row = bytes(1 + (width + 7) // 8)
    compressor = zlib.compressobj(level=1)
    pixels = (
        b"".join(compressor.compress(row) for _ in range(height)) + compressor.flush()
    )
    header = struct.pack(">IIBBBBB", width, height, 1, 0, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", pixels)
        + chunk(b"IEND", b"")
    )


def write_npy(path: Path, descr: str, shape: tuple, payload: bytes = b"") -> None:
    header = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': {shape}, }}"
    padding = -(10 + len(header) + 1) % 64
    header = (header + " " * padding + "\n").encode("latin1")
    path.write_bytes(
        b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header + payload
    )


MZML = """<mzML xmlns="http://psi.hupo.org/ms/mzml"><run><spectrumList count="2">
<spectrum index="0"><scanList count="1"><scan/></scanList></spectrum>
<spectrum index="1"><scanList count="1"><scan/></scanList></spectrum>
</spectrumList></run></mzML>"""

MZXML = """<mzXML xmlns="http://sashimi.sourceforge.net/schema_revision/mzXML_3.2">
<msRun scanCount="2"><scan num="1"/><scan num="2"/></msRun></mzXML>"""


def test_mzml_counts_spectra_once_and_mzxml_counts_scans(tmp_path):
    mzml = tmp_path / "run.mzML"
    mzml.write_text(MZML, encoding="utf-8")
    mzxml = tmp_path / "run.mzXML"
    mzxml.write_text(MZXML, encoding="utf-8")

    assert analyze_text_file(mzml)["spectra"] == 2
    assert analyze_text_file(mzxml)["spectra"] == 2


def test_fastq_with_a_zero_length_read_keeps_its_statistics(tmp_path):
    fastq = tmp_path / "reads.fastq"
    fastq.write_text("@r1\nACGT\n+\nIIII\n@r2\n\n+\n\n", encoding="utf-8")

    stats = report_statistics(run_cli_report(fastq))

    assert stats["read_count_sampled"] == 2
    assert stats["min_length"] == 0
    assert stats["max_length"] == 4
    assert stats["mean_quality"] == 40


def test_empty_npy_array_keeps_shape_and_dtype(tmp_path):
    npy = tmp_path / "empty.npy"
    write_npy(npy, "<f8", (0,))

    stats = report_statistics(run_cli_report(npy))

    assert stats["shape"] == [0]
    assert stats["dtype"] == "float64"
    assert stats["statistics"]["mean"] is None


def test_npy_statistics_are_unchanged_for_a_non_empty_array(tmp_path):
    npy = tmp_path / "two.npy"
    write_npy(npy, "<f8", (2,), struct.pack("<2d", 1.0, 3.0))

    stats = report_statistics(run_cli_report(npy))["statistics"]

    assert stats == {"min": 1.0, "max": 3.0, "mean": 2.0, "std": 1.0}


def first_heading(category: str, extension: str) -> str:
    reference = module.load_reference_info(category, extension)
    assert reference is not None, f"no reference entry for .{extension}"
    return reference["raw_section"].splitlines()[0]


def test_reference_lookup_finds_last_entry_before_a_section_heading():
    assert first_heading("chemistry_molecular", "gro").startswith("### .gro ")
    assert first_heading("bioinformatics_genomics", "gvcf").startswith("### .gvcf ")


def test_reference_lookup_reads_every_extension_of_a_heading():
    assert first_heading("bioinformatics_genomics", "gff3").startswith(
        "### .gff / .gff3 "
    )
    assert first_heading("bioinformatics_genomics", "gff").startswith(
        "### .gff / .gff3 "
    )


def test_reference_lookup_matches_the_extension_exactly():
    assert first_heading("spectroscopy_analytical", "d").startswith("### .d - Agilent")
    assert first_heading("bioinformatics_genomics", "bw").startswith(
        "### .bigWig / .bw "
    )
    assert module.load_reference_info("bioinformatics_genomics", "bi") is None


def test_reference_lookup_maps_mzid_to_its_mzidentml_entry():
    assert first_heading("proteomics_metabolomics", "mzid").startswith(
        "### .mzIdentML "
    )


def test_reference_section_stops_at_the_next_heading():
    section = module.load_reference_info("bioinformatics_genomics", "gvcf")[
        "raw_section"
    ]
    assert "### .counts" not in section
    assert "## RNA-Seq" not in section


def test_report_has_no_empty_recommendation_list(tmp_path):
    report = tmp_path / "report.md"
    analysis = module.analyze_file(SKILL / "fixtures" / "structure.pdb")
    text = module.generate_markdown_report(analysis, report)
    assert "consider the following analyses" not in text

    csv = tmp_path / "table.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    text = module.generate_markdown_report(module.analyze_file(csv))
    assert "consider the following analyses" in text
    assert "- Outlier detection" in text


def test_large_image_reports_header_and_skips_statistics(tmp_path):
    png = tmp_path / "large.png"
    write_blank_png(png, 12_000, 12_000)  # 144 million pixels, above the statistics cap

    stats = report_statistics(run_cli_report(png))

    assert stats["size"] == [12_000, 12_000]
    assert stats["mode"] == "1"
    assert stats["format"] == "PNG"
    assert "144,000,000 pixels" in stats["statistics_skipped"]
    assert "value_range" not in stats


def test_image_above_pillow_limit_reports_why_statistics_were_skipped(tmp_path):
    png = tmp_path / "huge.png"
    write_blank_png(
        png, 14_000, 14_000
    )  # 196 million pixels, refused by Pillow's guard

    stats = report_statistics(run_cli_report(png))

    assert "196000000 pixels" in stats["statistics_skipped"]


def test_small_image_keeps_pixel_statistics(tmp_path):
    png = tmp_path / "small.png"
    write_blank_png(png, 8, 8)

    stats = report_statistics(run_cli_report(png))

    assert stats["size"] == [8, 8]
    assert stats["value_range"] == [0, 0]
    assert "statistics_skipped" not in stats
