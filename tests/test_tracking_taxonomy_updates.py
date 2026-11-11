from __future__ import annotations

import csv
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "tracking-taxonomy-updates"
CONVERTER = SKILL_ROOT / "scripts" / "quickclade_to_routing.py"
FIXTURE = SKILL_ROOT / "fixtures" / "quickclade-machine.tsv"


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

    def test_quickclade_fixture_routes_all_domains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--no-project",
                    "python",
                    str(CONVERTER),
                    str(FIXTURE),
                    "--sample-id",
                    "sample-1",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual([row["downstream_tool"] for row in rows], ["gtdbtk", "eukcc", "gvclass", ""])
            self.assertEqual(rows[-1]["review_flag"], "true")

    def test_eukcc_job_passes_the_bin_suffix(self) -> None:
        """`eukcc folder` reads only files ending in --suffix (default `.fa`)."""
        template = SKILL_ROOT / "templates" / "taxonomy-tool.sbatch"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            eukcc = fake_bin / "eukcc"
            eukcc.write_text(
                '#!/usr/bin/env bash\nprintf "%s\\n" "$@" '
                '> "$TAXONOMY_OUTPUT/args.txt"\n',
                encoding="utf-8",
            )
            eukcc.chmod(0o755)
            (root / "bins").mkdir()
            env = os.environ | {
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "TAXONOMY_TOOL": "eukcc",
                "TAXONOMY_INPUT": str(root / "bins"),
                "TAXONOMY_OUTPUT": str(root / "out"),
                "EUKCC2_DB": str(root / "db"),
                "EUKCC_SUFFIX": ".fna",
            }
            result = subprocess.run(
                ["bash", str(template)],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = (root / "out" / "args.txt").read_text(encoding="utf-8").split()
        self.assertEqual(args[args.index("--suffix") + 1], ".fna")


if __name__ == "__main__":
    unittest.main()
