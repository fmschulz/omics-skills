#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Extract a minimal run manifest from Nextflow `trace.txt` + `work/` directory.

This script is intentionally conservative:
- It reads task rows from `trace.txt`.
- It maps each `hash` (e.g., `45/ab752a`) to `work/<hash>/`.
- It reads `.command.sh` when present and embeds it into the manifest.
- It does NOT guess tool versions.

Usage (the dependencies come from the inline script header, so use `uv run --script`):
  uv run --script scripts/extract_nextflow_run.py --trace trace.txt --workdir work \
      --out run_manifest.yaml --run-id <id> --pipeline-name rnaseq \
      --tool-versions tool-versions.json --outputs-manifest outputs.txt \
      [--pipeline-version <tag>] [--repo-url <url>] [--commit-sha <sha>] \
      [--engine-version <version>] [--launch-command "nextflow run ..."]

Required: --trace, --workdir, --out, --run-id, --pipeline-name, --tool-versions,
--outputs-manifest. Run with --help for the option list.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import (  # noqa: UP035  # legacy Dict/List annotations remain in this file
    Any,
    Dict,
    List,
    Optional,
)

import yaml

from command_redaction import redact_command


def sniff_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(errors='ignore')[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[',', '\t'])
    except Exception:
        # Nextflow trace is often tab-separated; fall back to tab.
        class Tab(csv.Dialect):
            delimiter = '\t'
            quotechar = '"'
            escapechar = None
            doublequote = True
            skipinitialspace = False
            lineterminator = '\n'
            quoting = csv.QUOTE_MINIMAL
        return Tab()


def read_command(work_task_dir: Path) -> Optional[str]:
    # `.command.run` is a wrapper that can embed the full task environment.
    # Read only the task script and redact common credential patterns.
    path = work_task_dir / '.command.sh'
    if path.exists():
        return redact_command(path.read_text(errors='ignore'))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace', required=True, type=Path, help='Nextflow trace file (e.g., trace.txt)')
    ap.add_argument('--workdir', required=True, type=Path, help='Nextflow work directory (e.g., work/)')
    ap.add_argument('--out', required=True, type=Path, help='Output manifest path (.yaml or .json)')
    ap.add_argument('--run-id', required=True, help='Stable run identifier')
    ap.add_argument('--pipeline-name', required=True, help='Pipeline name')
    ap.add_argument('--pipeline-version', default='', help='Pipeline version (tag) if known')
    ap.add_argument('--repo-url', default='', help='Repo URL if known')
    ap.add_argument('--commit-sha', default='', help='Commit SHA if known')
    ap.add_argument('--engine-version', default='', help='Nextflow version if known')
    ap.add_argument('--launch-command', default='', help='Exact nextflow launch command (quoted)')
    ap.add_argument('--tool-versions', required=True, type=Path, help='JSON mapping task/process names to {tool, version}')
    ap.add_argument('--outputs-manifest', required=True, type=Path, help='One final output path per line')

    args = ap.parse_args()

    dialect = sniff_dialect(args.trace)
    with args.trace.open(newline='', errors='ignore') as f:
        reader = csv.DictReader(f, dialect=dialect)
        rows = list(reader)

    tool_versions = json.loads(args.tool_versions.read_text(encoding='utf-8'))
    final_outputs = [line.strip() for line in args.outputs_manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not final_outputs:
        ap.error('--outputs-manifest has no output paths')

    steps: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        task_hash = (row.get('hash') or '').strip()
        task_name = (row.get('name') or '').strip() or f'task_{i}'
        work_task_dir = args.workdir / task_hash if task_hash else None

        cmd = None
        workdir_str = ''
        if work_task_dir and work_task_dir.exists():
            workdir_str = str(work_task_dir)
            cmd = read_command(work_task_dir)

        process_name = task_name.split(' (', 1)[0]
        tool_record = tool_versions.get(task_name) or tool_versions.get(process_name)
        if not tool_record or not tool_record.get('tool') or not tool_record.get('version'):
            ap.error(f'missing tool/version evidence for task: {task_name}')
        inputs = []
        outputs = []
        if work_task_dir:
            for filename, target in (('.command.in', inputs), ('.command.out', outputs)):
                evidence_path = work_task_dir / filename
                if evidence_path.is_file():
                    target.extend(line.strip() for line in evidence_path.read_text(encoding='utf-8').splitlines() if line.strip())
        if not cmd or not inputs or not outputs:
            ap.error(f'incomplete command/input/output evidence for task: {task_name}')

        steps.append({
            'step_id': f'nf-task-{i}',
            'name': task_name,
            'status': (row.get('status') or '').strip(),
            'exit_code': (row.get('exit') or '').strip(),
            'workdir': workdir_str,
            'tool': tool_record['tool'],
            'tool_version': tool_record['version'],
            'command': cmd,
            'inputs': inputs,
            'outputs': outputs,
            'resources': {
                'duration': row.get('duration'),
                'realtime': row.get('realtime'),
                'cpu_pct': row.get('%cpu'),
                'peak_rss': row.get('peak_rss'),
                'peak_vmem': row.get('peak_vmem'),
            }
        })

    manifest: Dict[str, Any] = {
        "run_id": args.run_id,
        "workflow_summary": f"Evidence-derived Nextflow run for {args.pipeline_name}.",
        "workflow": {
            "engine": "nextflow",
            "engine_version": args.engine_version,
            "pipeline": {
                "name": args.pipeline_name,
                "version": args.pipeline_version,
                "repo_url": args.repo_url,
                "commit_sha": args.commit_sha,
                "launch_command": redact_command(args.launch_command),
            },
            "execution": {
                "workdir": str(args.workdir),
            },
        },
        "steps": steps,
        "outputs": final_outputs,
        "evidence": [
            str(args.trace),
            str(args.workdir),
            str(args.tool_versions),
            str(args.outputs_manifest),
        ],
    }

    if args.out.suffix.lower() in {'.yml', '.yaml'}:
        args.out.write_text(yaml.safe_dump(manifest, sort_keys=False))
    else:
        args.out.write_text(json.dumps(manifest, indent=2))

    print(f"Wrote: {args.out}")


if __name__ == '__main__':
    main()
