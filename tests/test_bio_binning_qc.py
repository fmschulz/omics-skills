from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "bio-binning-qc"
FIXTURES = SKILL_ROOT / "fixtures"
SCRIPT = SKILL_ROOT / "scripts" / "build_bin_qc_tables.py"


class BioBinningQCTests(unittest.TestCase):
    def command(
        self, out_dir: Path, gunc: Path | None = None, routing: Path | None = None
    ) -> list[str]:
        return [
            "uv",
            "run",
            "--no-project",
            "python",
            str(SCRIPT),
            "--routing",
            str(routing or FIXTURES / "domain_routing.tsv"),
            "--checkm2",
            str(FIXTURES / "checkm2.tsv"),
            "--gunc",
            str(gunc or FIXTURES / "gunc.tsv"),
            "--eukcc",
            str(FIXTURES / "eukcc.tsv"),
            "--gtdbtk",
            str(FIXTURES / "gtdbtk.tsv"),
            "--out-dir",
            str(out_dir),
        ]

    def test_routed_fixture_writes_promised_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            result = subprocess.run(self.command(out_dir), cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (out_dir / "bin_metrics.tsv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["qc_tool"], "checkm2")
            self.assertEqual(rows[0]["gunc_pass"], "True")
            self.assertEqual(rows[0]["gunc_css"], "0.0")
            self.assertEqual(rows[1]["qc_tool"], "eukcc")
            self.assertEqual(rows[1]["bin_id"], "bin_euk")
            self.assertEqual(rows[1]["taxonomy"], "1-131567-2759-4751")
            self.assertEqual(rows[2]["domain_route"], "prokaryotic_virus")

    def test_gunc_rejects_eukaryotic_bin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gunc = Path(tmp) / "gunc.tsv"
            gunc.write_text(
                "genome\tclade_separation_score\tpass.GUNC\nbin_euk\t0.1\tTrue\n",
                encoding="utf-8",
            )
            result = subprocess.run(self.command(Path(tmp) / "out", gunc), cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-prokaryotic route", result.stderr)

    def run_percontig(
        self, tmp: str, contig_rows: list[tuple[str, str, str, str]]
    ) -> list[dict[str, str]]:
        """Run the join on a per-contig routing table.

        Columns are (query_id, contig_id, route, review_flag).
        """
        routing = Path(tmp) / "routing.tsv"
        header = "sample_id\tquery_id\tcontig_id\troute\treview_flag\n"
        lines = [
            f"S1\t{query}\t{contig}\t{route}\t{flag}\n"
            for query, contig, route, flag in contig_rows
        ]
        routing.write_text(header + "".join(lines), encoding="utf-8")
        out_dir = Path(tmp) / "out"
        command = self.command(out_dir, routing=routing)
        # Only the routed bins below need tool tables, so drop the fixture inputs
        # for the others.
        command = [
            arg
            for arg in command
            if arg not in {"--gunc", "--eukcc", "--checkm2", "--gtdbtk"}
        ]
        command = [arg for arg in command if not str(arg).startswith(str(FIXTURES))]
        result = subprocess.run(
            command, cwd=REPO_ROOT, text=True, capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with (out_dir / "bin_metrics.tsv").open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_percontig_routing_with_agreeing_contigs_gives_one_row_per_bin(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rows = self.run_percontig(
                tmp,
                [
                    ("bin_viral", "c1", "prokaryotic_virus", "false"),
                    ("bin_viral", "c2", "prokaryotic_virus", "false"),
                ],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["bin_id"], "bin_viral")
            self.assertEqual(rows[0]["domain_route"], "prokaryotic_virus")
            self.assertEqual(rows[0]["review_flag"], "false")

    def test_percontig_routing_with_mixed_contigs_goes_to_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rows = self.run_percontig(
                tmp,
                [
                    ("bin_mixed", "c1", "prokaryotic_virus", "false"),
                    ("bin_mixed", "c2", "giant_virus", "false"),
                ],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["domain_route"], "manual_review")
            self.assertEqual(rows[0]["review_flag"], "true")

    def test_the_same_bin_name_under_two_samples_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            routing = Path(tmp) / "routing.tsv"
            routing.write_text(
                "sample_id\tquery_id\tcontig_id\troute\treview_flag\n"
                "S1\tbin.1\tc1\tprokaryotic_virus\tfalse\n"
                "S2\tbin.1\tc2\tprokaryotic_virus\tfalse\n",
                encoding="utf-8",
            )
            out_dir = Path(tmp) / "out"
            command = [
                "uv", "run", "--no-project", "python", str(SCRIPT),
                "--routing", str(routing), "--out-dir", str(out_dir),
            ]  # fmt: skip
            result = subprocess.run(
                command, cwd=REPO_ROOT, text=True, capture_output=True, check=False
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate identifier bin.1", result.stderr)


if __name__ == "__main__":
    unittest.main()
