#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Extract a manifest from Snakemake JSONL job evidence and final-output paths."""

import argparse
import json
from pathlib import Path

import yaml

from command_redaction import redact_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', type=Path, required=True, help='JSONL records with rule, status, tool, version, command, inputs, outputs')
    parser.add_argument('--outputs-manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--pipeline-name', required=True)
    parser.add_argument('--pipeline-version', required=True)
    parser.add_argument('--commit-sha', required=True)
    parser.add_argument('--engine-version', required=True)
    parser.add_argument('--launch-command', required=True)
    args = parser.parse_args()
    jobs = [json.loads(line) for line in args.jobs.read_text(encoding='utf-8').splitlines() if line.strip()]
    required = {'rule', 'status', 'tool', 'version', 'command', 'inputs', 'outputs'}
    if not jobs or any(set(job) != required for job in jobs):
        parser.error(f'every job must have exactly: {", ".join(sorted(required))}')
    outputs = [line.strip() for line in args.outputs_manifest.read_text().splitlines() if line.strip()]
    if not outputs:
        parser.error('outputs manifest is empty')
    steps = [
        {
            "step_id": f"smk-job-{index}",
            "name": job["rule"],
            "status": job["status"],
            "tool": job["tool"],
            "tool_version": job["version"],
            "command": redact_command(job["command"]),
            "inputs": job["inputs"],
            "outputs": job["outputs"],
        }
        for index, job in enumerate(jobs, 1)
    ]
    manifest = {
        "run_id": args.run_id,
        "workflow_summary": f"Evidence-derived Snakemake run for {args.pipeline_name}.",
        "workflow": {
            "engine": "snakemake",
            "engine_version": args.engine_version,
            "pipeline": {
                "name": args.pipeline_name,
                "version": args.pipeline_version,
                "commit_sha": args.commit_sha,
                "launch_command": redact_command(args.launch_command),
            },
        },
        "steps": steps,
        "outputs": outputs,
        "evidence": [str(args.jobs), str(args.outputs_manifest)],
    }
    args.out.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
