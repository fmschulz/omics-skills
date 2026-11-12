from __future__ import annotations

import csv
import fcntl
import importlib.util
import math
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "tracking-taxonomy-updates"
CONVERTER = SKILL_ROOT / "scripts" / "quickclade_to_routing.py"
FIXTURE = SKILL_ROOT / "fixtures" / "quickclade-machine.tsv"
"""Real QuickClade output (BBTools 39.85), four contigs with five hits each.

Produced on 2026-11-11 with `docker run --rm -u UID:GID -v "$PWD":/work -w /work
bryce911/bbtools:39.85 quickclade.sh contigs.fa percontig
ref=/bbmap/resources/refseqA48_with_ribo.spectra.gz
out=quickclade_percontig.tsv format=machine usetree threads=4`.
Image digest sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1.
`contigs.fa` holds NCBI phiX174 (NC_001422.1), phage lambda (NC_001416.1), pUC19
(L09137.2) and the human mitochondrion (NC_001807.4). The file is unedited.
"""


def load_converter():
    spec = importlib.util.spec_from_file_location("quickclade_to_routing", CONVERTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TrackingTaxonomyUpdatesTests(unittest.TestCase):
    def test_route_sends_each_domain_to_its_tool(self) -> None:
        route = load_converter().route
        cases = {
            "Bacteriophage": ("prokaryotic_virus", "vcontact3"),
            "Bacterial virus": ("prokaryotic_virus", "vcontact3"),
            "Bacteria": ("prokaryote", "gtdbtk"),
            "Archaea": ("prokaryote", "gtdbtk"),
            "Nucleocytoviricota": ("giant_virus", "gvclass"),
            "Eukaryota": ("eukaryote", "eukcc"),
            "Mixed": ("manual_review", ""),
        }
        for domain, expected in cases.items():
            with self.subTest(domain=domain):
                self.assertEqual(route(domain)[:2], expected)

    def run_converter(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--no-project", "python", str(CONVERTER), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def read_routing(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_real_quickclade_output_routes_each_contig_once(self) -> None:
        """The fixture has five hits per contig; only the best hit is routed."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            result = self.run_converter(
                str(FIXTURE), "--sample-id", "sample-1", "--output", str(output)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = self.read_routing(output)
        self.assertEqual(
            [row["contig_id"] for row in rows],
            ["NC_001422.1", "NC_001416.1", "L09137.2", "NC_001807.4"],
        )
        self.assertEqual(
            [row["quickclade_domain"] for row in rows],
            ["Viruses", "Viruses", "Bacteria", "Eukaryota"],
        )
        self.assertEqual(
            [row["downstream_tool"] for row in rows],
            ["vcontact3", "vcontact3", "gtdbtk", "eukcc"],
        )
        self.assertEqual(
            [row["quickclade_confidence"] for row in rows],
            ["98.9", "98.9", "99.3", "98.9"],
        )
        self.assertEqual({row["low_confidence"] for row in rows}, {"false"})
        self.assertTrue(rows[0]["quickclade_taxonomy"].startswith("sk__Viruses;"))

    def test_min_confidence_flags_rows_for_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            result = self.run_converter(
                str(FIXTURE),
                "--sample-id",
                "sample-1",
                "--min-confidence",
                "99",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = self.read_routing(output)
        self.assertEqual(
            [row["low_confidence"] for row in rows], ["true", "true", "false", "true"]
        )
        flagged = rows[0]
        self.assertEqual(flagged["route"], "manual_review")
        self.assertEqual(flagged["downstream_tool"], "")
        self.assertEqual(flagged["review_flag"], "true")
        self.assertEqual(rows[2]["downstream_tool"], "gtdbtk")

    def test_domain_comes_from_the_lineage(self) -> None:
        domain_of = load_converter().domain_of
        self.assertEqual(domain_of("sk__Archaea;k__Thermoproteati"), "Archaea")
        self.assertEqual(
            domain_of(
                "sk__Viruses;k__Bamfordvirae;p__Nucleocytoviricota;c__Megaviricetes"
            ),
            "Nucleocytoviricota",
        )
        with self.assertRaises(ValueError):
            domain_of("k__Metazoa")

    def test_append_adds_a_second_sample_and_refuses_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            first = ("--output", str(output))
            self.assertEqual(
                self.run_converter(
                    str(FIXTURE), "--sample-id", "S1", *first
                ).returncode,
                0,
            )
            plain = self.run_converter(str(FIXTURE), "--sample-id", "S2", *first)
            self.assertEqual(plain.returncode, 1)
            self.assertIn("refusing to overwrite", plain.stderr)

            appended = self.run_converter(
                str(FIXTURE), "--sample-id", "S2", "--append", *first
            )
            self.assertEqual(appended.returncode, 0, appended.stderr)
            rows = self.read_routing(output)
            self.assertEqual(len(rows), 8)
            self.assertEqual(
                [row["sample_id"] for row in rows], ["S1"] * 4 + ["S2"] * 4
            )
            self.assertEqual(output.read_text(encoding="utf-8").count("sample_id\t"), 1)

            again = self.run_converter(
                str(FIXTURE), "--sample-id", "S2", "--append", *first
            )
            self.assertEqual(again.returncode, 1)
            self.assertIn("NC_001422.1", again.stderr)
            self.assertEqual(len(self.read_routing(output)), 8)

    def test_conversion_waits_for_the_output_lock_and_replaces_atomically(self) -> None:
        converter = load_converter()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            lock_path = output.with_name(output.name + ".lock")
            lock_path.touch()
            finished = threading.Event()

            def convert() -> None:
                with patch.object(
                    converter.os, "replace", wraps=converter.os.replace
                ) as replace:
                    converter.convert(FIXTURE, output, "S1")
                self.assertEqual(replace.call_args.args[1], output)
                finished.set()

            worker = threading.Thread(target=convert)
            with lock_path.open("a+") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                worker.start()
                self.assertFalse(finished.wait(0.5), "converted without the lock")
                self.assertFalse(output.exists())
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            worker.join(timeout=30)
            self.assertTrue(finished.is_set())
            self.assertEqual(
                sorted(path.name for path in Path(tmp).iterdir()),
                ["domain_routing.tsv", "domain_routing.tsv.lock"],
            )

    def test_concurrent_appends_of_one_sample_add_it_once(self) -> None:
        converter = load_converter()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            converter.convert(FIXTURE, output, "S0")
            outcomes: list[str] = []

            def append() -> None:
                try:
                    converter.convert(FIXTURE, output, "S1", append=True)
                    outcomes.append("added")
                except ValueError:
                    outcomes.append("refused")

            workers = [threading.Thread(target=append) for _ in range(6)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=30)
            rows = self.read_routing(output)
        self.assertEqual(sorted(outcomes), ["added"] + ["refused"] * 5)
        self.assertEqual(len(rows), 8)

    def test_append_requires_the_exact_output_header(self) -> None:
        converter = load_converter()
        fields = list(converter.OUTPUT_FIELDS)
        headers = {
            "reordered": [*fields[1:], fields[0]],
            "extra": [*fields, "extra"],
            "short": fields[:-1],
        }
        for name, header in headers.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "domain_routing.tsv"
                original = "\t".join(header) + "\n"
                output.write_text(original, encoding="utf-8")
                result = self.run_converter(
                    str(FIXTURE),
                    "--sample-id",
                    "S1",
                    "--append",
                    "--output",
                    str(output),
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("header", result.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), original)

    def test_min_confidence_must_be_a_finite_percent(self) -> None:
        for value in ("nan", "inf", "-inf", "-1", "100.5"):
            with self.subTest(value), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "domain_routing.tsv"
                result = self.run_converter(
                    str(FIXTURE),
                    "--sample-id",
                    "S1",
                    f"--min-confidence={value}",
                    "--output",
                    str(output),
                )
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("--min-confidence", result.stderr)
                self.assertFalse(output.exists())

    def test_domain_confidence_must_be_a_finite_percent(self) -> None:
        converter = load_converter()
        self.assertEqual(converter.domain_confidence("d:0;k:1"), 0.0)
        self.assertEqual(converter.domain_confidence("d:100"), 100.0)
        for confidence in ("d:nan;k:1", "d:inf", "d:-1", "d:100.5", "d:abc"):
            with self.subTest(confidence), self.assertRaises(ValueError):
                converter.domain_confidence(confidence)
        self.assertTrue(math.isfinite(converter.domain_confidence("d:98.9")))

    def test_non_finite_domain_confidence_in_the_input_fails_the_run(self) -> None:
        header, first, *_ = FIXTURE.read_text(encoding="utf-8").splitlines()
        columns = header.split("\t")
        fields = first.split("\t")
        fields[columns.index("Confidence")] = "d:nan;k:97.9"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "nan.tsv"
            source.write_text(
                "\n".join([header, "\t".join(fields)]) + "\n", encoding="utf-8"
            )
            output = Path(tmp) / "out.tsv"
            result = self.run_converter(
                str(source), "--sample-id", "S1", "--output", str(output)
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("d:", result.stderr)
            self.assertFalse(output.exists())

    def test_whole_file_queries_are_rejected(self) -> None:
        """A run without `percontig` reports Q_Contigs above 1 per query."""
        header, first, *_ = FIXTURE.read_text(encoding="utf-8").splitlines()
        columns = header.split("\t")
        fields = first.split("\t")
        fields[columns.index("Q_Contigs")] = "12"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "perfile.tsv"
            source.write_text(
                "\n".join([header, "\t".join(fields)]) + "\n", encoding="utf-8"
            )
            result = self.run_converter(
                str(source), "--sample-id", "S1", "--output", str(Path(tmp) / "out.tsv")
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("percontig", result.stderr)

    def test_missing_real_column_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "guess.tsv"
            source.write_text(
                "query\tcontig\tdomain\nbin_1\tc1\tBacteria\n", encoding="utf-8"
            )
            result = self.run_converter(
                str(source), "--sample-id", "S1", "--output", str(Path(tmp) / "out.tsv")
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("#QueryName", result.stderr)

    def run_template(self, root: Path, tool: str, **extra: str) -> list[str]:
        """Run the sbatch template with a fake `pixi`; return the pixi arguments.

        No tool is on PATH: a tool called bare would fail with "command not found".
        """
        fake_bin = root / "bin"
        fake_bin.mkdir()
        pixi = fake_bin / "pixi"
        pixi.write_text(
            '#!/usr/bin/env bash\nprintf "%s\\n" "$@" >> "$TAXONOMY_OUTPUT/pixi.txt"\n',
            encoding="utf-8",
        )
        pixi.chmod(0o755)
        (root / "bins").mkdir()
        env = (
            os.environ
            | {
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "TAXONOMY_TOOL": tool,
                "TAXONOMY_INPUT": str(root / "bins"),
                "TAXONOMY_OUTPUT": str(root / "out"),
            }
            | extra
        )
        result = subprocess.run(
            ["bash", str(SKILL_ROOT / "templates" / "taxonomy-tool.sbatch")],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return (root / "out" / "pixi.txt").read_text(encoding="utf-8").split()

    def test_eukcc_job_runs_through_pixi_and_passes_the_bin_suffix(self) -> None:
        """`eukcc folder` reads only files ending in --suffix (default `.fa`)."""
        with tempfile.TemporaryDirectory() as tmp:
            args = self.run_template(
                Path(tmp), "eukcc", EUKCC2_DB=f"{tmp}/db", EUKCC_SUFFIX=".fna"
            )
        self.assertEqual(args[:3], ["run", "--frozen", "eukcc"])
        self.assertEqual(args[args.index("--suffix") + 1], ".fna")

    def test_every_tool_runs_through_pixi(self) -> None:
        extra = {
            "gtdbtk": {"GTDBTK_DATA_PATH": "/db"},
            "vcontact3": {"VCONTACT3_DB": "/db"},
            "gvclass": {},
        }
        for tool, env in extra.items():
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as tmp:
                args = self.run_template(Path(tmp), tool, **env)
                self.assertEqual(args[:2], ["run", "--frozen"])
                self.assertIn(tool, args)

    def test_template_sets_log_paths(self) -> None:
        template = SKILL_ROOT / "templates" / "taxonomy-tool.sbatch"
        directives = [
            line
            for line in template.read_text(encoding="utf-8").splitlines()
            if line.startswith("#SBATCH")
        ]
        self.assertIn("#SBATCH --output=logs/taxonomy-%j.out", directives)
        self.assertIn("#SBATCH --error=logs/taxonomy-%j.err", directives)


if __name__ == "__main__":
    unittest.main()
