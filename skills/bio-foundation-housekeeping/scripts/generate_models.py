#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "linkml==1.11.1",
#   "pydantic==2.13.4",
# ]
# ///
"""Generate and verify Pydantic models from a LinkML schema."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from contextlib import chdir
from pathlib import Path
from types import ModuleType

from linkml.generators.pydanticgen import PydanticGenerator


def generate_source(schema_path: Path) -> str:
    schema_path = schema_path.resolve()
    with chdir(schema_path.parent):
        generator = PydanticGenerator(
            schema_path.name,
            extra_fields="forbid",
            emit_metadata=False,
        )
        source = generator.serialize()
    compile(source, str(schema_path), "exec")
    return source


def load_module(path: Path) -> ModuleType:
    module_name = f"generated_linkml_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generated model: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


def write_or_check(output_path: Path, source: str, check: bool) -> str:
    if output_path.exists():
        if output_path.read_text(encoding="utf-8") != source:
            raise FileExistsError(f"refusing to overwrite changed generated model: {output_path}")
        return "verified" if check else "unchanged"
    if check:
        raise FileNotFoundError(f"generated model is missing: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(source)
        temporary = Path(handle.name)
    temporary.replace(output_path)
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expect-class",
        action="append",
        default=[],
        help="Class that must exist in the generated module; repeat as needed",
    )
    parser.add_argument("--check", action="store_true", help="Verify without writing")
    args = parser.parse_args(argv)

    schema_path = args.schema.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    if not schema_path.is_file():
        parser.error(f"schema does not exist: {schema_path}")

    try:
        source = generate_source(schema_path)
        status = write_or_check(output_path, source, args.check)
        module = load_module(output_path)
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as exc:
        print(str(exc))
        return 2
    except Exception as exc:
        print(f"model generation failed with {type(exc).__name__}")
        return 2

    missing = [name for name in args.expect_class if not hasattr(module, name)]
    if missing:
        print(f"generated model is missing expected classes: {', '.join(missing)}")
        return 2

    print(f"Generated model {status}: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
