import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills" / "notebooks" / "scripts" / "execute_notebook.py"

UV_RUN_BASE = ["uv", "run", "--no-project"]
# The script's own uv environment has no kernel, so the tests add ipykernel.
UV_RUN = [
    *UV_RUN_BASE,
    *("--with", "nbclient>=0.10,<1"),
    *("--with", "nbformat>=5.10,<6"),
    *("--with", "ipykernel"),
    *("python", str(SCRIPT)),
]
TEMPLATE_PACKAGES = [
    arg
    for package in ("numpy", "pandas", "matplotlib", "duckdb", "ipython", "cycler")
    for arg in ("--with", package)
]


def write_notebook(path: Path, kernelspec: dict | None) -> None:
    metadata = {"kernelspec": kernelspec} if kernelspec else {}
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-1",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["print(2 + 2)"],
            }
        ],
        "metadata": metadata,
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook), encoding="utf-8")


def run_script(notebook: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*UV_RUN, str(notebook), "--out", str(out), *extra],
        text=True,
        capture_output=True,
        check=False,
        cwd=notebook.parent,
    )


def test_without_kernel_flag_a_notebook_without_kernelspec_runs_on_python3(tmp_path):
    notebook = tmp_path / "plain.ipynb"
    out = tmp_path / "plain.executed.ipynb"
    write_notebook(notebook, None)

    result = run_script(notebook, out)

    assert result.returncode == 0, result.stdout + result.stderr
    executed = json.loads(out.read_text(encoding="utf-8"))
    assert executed["cells"][0]["outputs"][0]["text"] == ["4\n"]


def load_script_module():
    """Import the script with stand-ins for nbformat and nbclient."""
    spec = importlib.util.spec_from_file_location("execute_notebook", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    stubs = {"nbformat": mock.MagicMock(), "nbclient": mock.MagicMock()}
    with mock.patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


def test_kernel_name_comes_from_the_flag_then_the_notebook_then_python3():
    resolve = load_script_module().resolve_kernel_name
    assert resolve("project-env", None) == "project-env"
    assert resolve("project-env", "flag-env") == "flag-env"
    assert resolve(None, None) == "python3"
    assert resolve(None, "flag-env") == "flag-env"


def test_without_kernel_flag_the_notebook_kernelspec_name_is_used(tmp_path):
    notebook = tmp_path / "named.ipynb"
    out = tmp_path / "named.executed.ipynb"
    write_notebook(notebook, {"name": "no-such-kernel", "display_name": "Missing"})

    result = run_script(notebook, out)

    assert result.returncode != 0
    assert "no-such-kernel" in result.stdout + result.stderr
    assert not out.exists()


def test_kernel_flag_replaces_the_placeholder_in_the_executed_kernelspec(tmp_path):
    notebook = tmp_path / "placeholder.ipynb"
    out = tmp_path / "placeholder.executed.ipynb"
    write_notebook(notebook, {"name": "<PIXI_PROJECT_KERNEL>", "display_name": "x"})

    result = run_script(notebook, out, "--kernel", "python3")

    assert result.returncode == 0, result.stdout + result.stderr
    executed = json.loads(out.read_text(encoding="utf-8"))
    assert executed["metadata"]["kernelspec"]["name"] == "python3"
    assert "<PIXI_PROJECT_KERNEL>" not in out.read_text(encoding="utf-8")


def test_jupyter_template_runs_top_to_bottom_in_a_fresh_project(tmp_path):
    template = ROOT / "skills" / "notebooks" / "templates" / "jupyter_kiss_template.py"
    project = tmp_path / "project"
    project.mkdir()
    # A fresh project has a pixi.toml, which marks the project root.
    (project / "pixi.toml").write_text(
        (template.parent / "pixi.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )

    result = subprocess.run(
        [
            *UV_RUN_BASE,
            *TEMPLATE_PACKAGES,
            "python",
            str(template),
        ],
        text=True,
        capture_output=True,
        check=False,
        cwd=project,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "data" / "analytics.duckdb").exists()
