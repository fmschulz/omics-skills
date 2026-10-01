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
    def command(self, out_dir: Path, gunc: Path | None = None) -> list[str]:
        return [
            "uv", "run", "--no-project", "python", str(SCRIPT),
            "--routing", str(FIXTURES / "domain_routing.tsv"),
            "--checkm2", str(FIXTURES / "checkm2.tsv"),
            "--gunc", str(gunc or FIXTURES / "gunc.tsv"),
            "--eukcc", str(FIXTURES / "eukcc.tsv"),
            "--gtdbtk", str(FIXTURES / "gtdbtk.tsv"),
            "--out-dir", str(out_dir),
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


if __name__ == "__main__":
    unittest.main()
