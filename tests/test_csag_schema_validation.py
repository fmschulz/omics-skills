from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "csag-extraction" / "scripts" / "validate_paper_extraction.py"


def minimal_extraction() -> dict:
    return {
        "id": "doi:10.1000/fixture",
        "title": "Fixture paper",
        "schema_version": "0.6.0",
        "validator_version": "0.6.0",
        "assertions": [
            {
                "id": "doi:10.1000/fixture/assertion/A0001",
                "assertion_text": "The fixture supports the claim.",
                "claim_role": "result_claim",
                "normalization_status": "raw",
                "contexts": [{"context_type": "other", "description": "fixture"}],
            }
        ],
        "evidence_items": [
            {
                "id": "doi:10.1000/fixture/evidence/E0001",
                "evidence_type": "experimental_result",
                "evidence_text": "The measured value increased.",
            }
        ],
        "evidence_links": [
            {
                "id": "doi:10.1000/fixture/elink/L0001",
                "evidence_item": "doi:10.1000/fixture/evidence/E0001",
                "assertion": "doi:10.1000/fixture/assertion/A0001",
                "polarity": "supports",
            }
        ],
        "extraction_activities": [
            {
                "id": "doi:10.1000/fixture/activity/ACT0001",
                "activity_type": "machine extraction",
                "parameters": [
                    {"key": "doi_status", "value": "resolved"},
                    {"key": "pmid_status", "value": "unresolved"},
                ],
            }
        ],
    }


class CsagSchemaValidationTests(unittest.TestCase):
    def run_validator(self, payload: dict, strict: bool = False, source_markdown: str | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "paper.json"
            report = root / "report.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            command = [
                "uv",
                "run",
                "--script",
                str(SCRIPT),
                str(source),
                "--report-out",
                str(report),
            ]
            if strict:
                command.append("--strict")
            if source_markdown is not None:
                markdown = root / "source.md"
                markdown.write_text(source_markdown, encoding="utf-8")
                command += ["--source-markdown", str(markdown)]
            return subprocess.run(
                command,
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_authoritative_linkml_schema_rejects_unknown_field(self) -> None:
        payload = minimal_extraction()
        payload["made_up_field"] = "not in schema"
        result = self.run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LinkML schema validation failed", result.stdout + result.stderr)

    def test_strict_mode_rejects_missing_text_grounding(self) -> None:
        result = self.run_validator(minimal_extraction(), strict=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing strict text grounding", result.stdout + result.stderr)


    def grounded_extraction(self, source: str, start: int, end: int, exact: str) -> dict:
        payload = minimal_extraction()
        payload["assertions"][0]["text_spans"] = [
            {
                "document_id": payload["id"],
                "section_type": "results",
                "start_char": start,
                "end_char": end,
                "exact_text": exact,
            }
        ]
        return payload

    def test_strict_mode_accepts_a_span_that_matches_the_source(self) -> None:
        """A span whose offsets and quote agree with the source raises no
        grounding complaint. (The shared fixture carries unrelated schema
        errors, so this asserts on the grounding issues specifically.)"""
        source = "# Paper\n\nThe bacterium grew faster at 37 degrees.\n"
        start = source.index("grew faster")
        payload = self.grounded_extraction(source, start, start + len("grew faster"), "grew faster")
        output = self.run_validator(payload, strict=True, source_markdown=source)
        combined = output.stdout + output.stderr
        self.assertNotIn("impossible character offsets", combined)
        self.assertNotIn("exact_text does not match the source slice", combined)
        self.assertNotIn("is past the", combined)

    def test_strict_mode_rejects_impossible_offsets(self) -> None:
        source = "# Paper\n\nThe bacterium grew faster at 37 degrees.\n"
        payload = self.grounded_extraction(source, 999, 2, "anything")
        result = self.run_validator(payload, strict=True, source_markdown=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("impossible character offsets", result.stdout + result.stderr)

    def test_strict_mode_rejects_a_quote_absent_from_the_source(self) -> None:
        source = "# Paper\n\nThe bacterium grew faster at 37 degrees.\n"
        payload = self.grounded_extraction(source, 0, 10, "a sentence the paper never contains")
        result = self.run_validator(payload, strict=True, source_markdown=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact_text does not match the source slice", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
