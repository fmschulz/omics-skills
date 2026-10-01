#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Validate structure inputs and optionally execute Boltz, Foldseek, and TM-Vec."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


def validate_boltz(path: Path) -> None:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("Boltz YAML must be an object with version: 1")
    sequences = payload.get("sequences")
    if not isinstance(sequences, list) or not sequences:
        raise ValueError("Boltz YAML requires a non-empty sequences list")
    entity_types = {"protein", "dna", "rna", "ligand"}
    for index, item in enumerate(sequences):
        if not isinstance(item, dict) or len(item) != 1:
            raise ValueError(f"Boltz sequence {index} must contain one entity-type mapping")
        entity_type, entity = next(iter(item.items()))
        if entity_type not in entity_types or not isinstance(entity, dict) or not entity.get("id"):
            raise ValueError(f"Boltz sequence {index} has an invalid entity type or missing id")
        required = "sequence" if entity_type != "ligand" else None
        if required and not entity.get(required):
            raise ValueError(f"Boltz {entity_type} sequence {index} is missing {required}")
        if entity_type == "ligand" and bool(entity.get("smiles")) == bool(entity.get("ccd")):
            raise ValueError("each Boltz ligand requires exactly one of smiles or ccd")


def existing(path: Path | None, label: str) -> Path | None:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {resolved}")
    return resolved


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    out_dir = args.out_dir.expanduser().resolve()
    commands: list[dict[str, object]] = []
    boltz_yaml = existing(args.boltz_yaml, "Boltz YAML")
    if boltz_yaml:
        validate_boltz(boltz_yaml)
        if args.use_msa_server and not args.approve_public_msa_upload:
            raise ValueError(
                "--use-msa-server requires --approve-public-msa-upload because sequences leave the system"
            )
        command = ["boltz", "predict", str(boltz_yaml), "--out_dir", str(out_dir / "boltz")]
        if args.use_msa_server:
            command.append("--use_msa_server")
        commands.append({"name": "boltz", "command": command, "expected": str(out_dir / "boltz")})

    foldseek_query = existing(args.foldseek_query, "Foldseek query")
    if foldseek_query:
        database = args.foldseek_padded_db if args.gpu else args.foldseek_db
        if database is None:
            required = "--foldseek-padded-db" if args.gpu else "--foldseek-db"
            raise ValueError(f"Foldseek query requires {required}")
        database = database.expanduser().resolve()
        if not database.with_suffix(database.suffix + ".dbtype").exists() and not database.exists():
            raise ValueError(f"Foldseek database prefix is missing: {database}")
        result = out_dir / "foldseek_hits.tsv"
        command = [
            "foldseek",
            "easy-search",
            str(foldseek_query),
            str(database),
            str(result),
            str(out_dir / "foldseek_tmp"),
        ]
        if args.gpu:
            command.extend(["--gpu", "1"])
        commands.append({"name": "foldseek", "command": command, "expected": str(result)})

    tmvec_query = existing(args.tmvec_query, "TM-Vec query")
    if tmvec_query:
        tmvec_db = existing(args.tmvec_db, "TM-Vec database")
        if tmvec_db is None:
            raise ValueError("TM-Vec query requires --tmvec-db")
        # The pinned fork's `search --output` is a folder; it writes results.tsv in it.
        tmvec_dir = out_dir / "tmvec"
        commands.append(
            {
                "name": "tmvec",
                "command": [
                    "tmvec",
                    "search",
                    "--input-fasta",
                    str(tmvec_query),
                    "--database",
                    str(tmvec_db),
                    "--output",
                    str(tmvec_dir),
                ],
                "expected": str(tmvec_dir / "results.tsv"),
            }
        )
    if not commands:
        raise ValueError("select at least one Boltz, Foldseek, or TM-Vec input")
    return {"out_dir": str(out_dir), "commands": commands}


def execute(plan: dict[str, object]) -> None:
    out_dir = Path(str(plan["out_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    for step in plan["commands"]:
        assert isinstance(step, dict)
        subprocess.run(step["command"], check=True)
        expected = Path(str(step["expected"]))
        if not expected.exists():
            raise ValueError(f"{step['name']} completed without expected output: {expected}")
        if expected.is_file() and expected.stat().st_size == 0:
            raise ValueError(f"{step['name']} produced an empty output: {expected}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boltz-yaml", type=Path)
    parser.add_argument("--use-msa-server", action="store_true")
    parser.add_argument("--approve-public-msa-upload", action="store_true")
    parser.add_argument("--foldseek-query", type=Path)
    parser.add_argument("--foldseek-db", type=Path)
    parser.add_argument("--foldseek-padded-db", type=Path)
    parser.add_argument("--tmvec-query", type=Path)
    parser.add_argument("--tmvec-db", type=Path)
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--plan-out", type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = build_plan(args)
        if args.plan_out:
            if args.plan_out.exists():
                raise ValueError(f"refusing to overwrite plan: {args.plan_out}")
            args.plan_out.parent.mkdir(parents=True, exist_ok=True)
            args.plan_out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        if args.execute:
            execute(plan)
    except (OSError, subprocess.CalledProcessError, ValueError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
