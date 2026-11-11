#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Extract a manifest from a normalized CWL provenance JSON record."""

import argparse
import json
from pathlib import Path

import yaml

from command_redaction import redact_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.provenance.read_text(encoding='utf-8'))
    required = {'run_id', 'engine_version', 'pipeline_name', 'pipeline_version', 'commit_sha', 'launch_command', 'steps', 'outputs'}
    if set(data) != required or not data['steps'] or not data['outputs']:
        parser.error(f'provenance must have exactly {", ".join(sorted(required))} and non-empty steps/outputs')
    step_required = {'name', 'status', 'tool', 'tool_version', 'command', 'inputs', 'outputs'}
    if any(set(step) != step_required for step in data['steps']):
        parser.error('each CWL step lacks complete command/version/input/output evidence')
    steps = [
        {
            "step_id": f"cwl-step-{index}",
            **step,
            "command": redact_command(step["command"]),
        }
        for index, step in enumerate(data["steps"], 1)
    ]
    manifest = {
        "run_id": data["run_id"],
        "workflow_summary": f"Evidence-derived CWL run for {data['pipeline_name']}.",
        "workflow": {
            "engine": "cwl",
            "engine_version": data["engine_version"],
            "pipeline": {
                "name": data["pipeline_name"],
                "version": data["pipeline_version"],
                "commit_sha": data["commit_sha"],
                "launch_command": redact_command(data["launch_command"]),
            },
        },
        "steps": steps,
        "outputs": data["outputs"],
        "evidence": [str(args.provenance)],
    }
    args.out.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
