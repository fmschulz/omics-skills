#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Combine sacct metrics and output checks into a versioned run-evidence record."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
JOB_SCHEMA = ROOT / "schemas" / "slurm-job.schema.json"
EVIDENCE_SCHEMA = ROOT / "schemas" / "run-evidence.schema.json"
SACCT_FIELDS = (
    "JobIDRaw",
    "State",
    "ExitCode",
    "ElapsedRaw",
    "MaxRSS",
    "AllocCPUS",
    "ReqMem",
    "NodeList",
)
MEMORY_UNITS = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def memory_bytes(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMGT])?", value, re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported MaxRSS value: {value}")
    number, unit = match.groups()
    return round(float(number) * MEMORY_UNITS.get((unit or "").upper(), 1))


def read_sacct(path: Path, job_id: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        if tuple(reader.fieldnames or ()) != SACCT_FIELDS:
            raise ValueError(f"sacct columns must be exactly: {', '.join(SACCT_FIELDS)}")
        rows = [
            row
            for row in reader
            if row["JobIDRaw"] == job_id or row["JobIDRaw"].startswith(f"{job_id}.")
        ]
    allocations = [row for row in rows if row["JobIDRaw"] == job_id]
    if len(allocations) != 1:
        raise ValueError(
            f"expected exactly one allocation row for job {job_id}, found {len(allocations)}"
        )
    return allocations[0], rows


def fetch_sacct(path: Path, job_id: str, cluster: str) -> None:
    """Always qualify by cluster. Job IDs collide between clusters, and an
    unqualified `sacct -j` can return another cluster's accounting for the
    same numeric ID."""
    result = subprocess.run(
        [
            "sacct",
            "-M",
            cluster,
            "-j",
            job_id,
            "--format=" + ",".join(SACCT_FIELDS),
            "--parsable2",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"sacct failed with exit {result.returncode}: {result.stderr.strip()}")
    path.write_text(result.stdout, encoding="utf-8")


def validate_json(document: dict[str, object], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError(
            "; ".join(
                f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
                for error in errors
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--sacct-file", type=Path)
    parser.add_argument("--fetch-sacct", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if bool(args.sacct_file) == args.fetch_sacct:
            raise ValueError("choose exactly one of --sacct-file or --fetch-sacct")
        job = json.loads(args.manifest.read_text(encoding="utf-8"))
        validate_json(job, JOB_SCHEMA)
        sacct_path = args.sacct_file
        if args.fetch_sacct:
            sacct_path = args.output.with_suffix(".sacct.psv")
            sacct_path.parent.mkdir(parents=True, exist_ok=True)
            fetch_sacct(sacct_path, args.job_id, job["scheduler"]["cluster"])
        row, sacct_rows = read_sacct(sacct_path, args.job_id)
        workdir = Path(job["workdir"])
        outputs = []
        failure_modes = []
        for expected in job["expected_outputs"]:
            path = workdir / expected["path"]
            size = path.stat().st_size if path.is_file() else 0
            passed = size >= expected["min_bytes"]
            outputs.append(
                {
                    "path": expected["path"],
                    "size_bytes": size,
                    "sha256": sha256(path) if passed else None,
                    "passed": passed,
                }
            )
            if not passed:
                failure_modes.append(f"missing_or_undersized_output:{expected['path']}")
        state = row["State"].split("+", 1)[0]
        if state != "COMPLETED":
            failure_modes.append(f"scheduler_state:{state}")
        if row["ExitCode"] != "0:0":
            failure_modes.append(f"exit_code:{row['ExitCode']}")
        peak_values = [memory_bytes(item["MaxRSS"]) for item in sacct_rows]
        peak_rss = max((value for value in peak_values if value is not None), default=None)
        if peak_rss is None:
            failure_modes.append("missing_peak_rss")
        evidence = {
            "schema_version": "1.1",
            "validation_id": job["validation_id"],
            "driver": job["driver"],
            "truth_set_id": job["truth_set_id"],
            "job_id": args.job_id,
            "scheduler": {
                "cluster": job["scheduler"]["cluster"],
                "state": state,
                "exit_code": row["ExitCode"],
                "elapsed_seconds": int(row["ElapsedRaw"]),
                "peak_rss_bytes": peak_rss,
                "allocated_cpus": int(row["AllocCPUS"]),
                "requested_memory": row["ReqMem"],
                "nodes": row["NodeList"],
            },
            "outputs": outputs,
            "scientific_metrics": {},
            "failure_modes": failure_modes,
        }
        validate_json(evidence, EVIDENCE_SCHEMA)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(evidence, handle, indent=2)
            handle.write("\n")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
