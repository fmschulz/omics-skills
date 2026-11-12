import ast
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
    *("--with", "nbclient>=0.10"),
    *("--with", "nbformat>=5.10"),
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


STYLE_MODULE = ROOT / "skills" / "beautiful-data-viz" / "assets" / "beautiful_style.py"
MARIMO_TEMPLATE = (
    ROOT / "skills" / "notebooks" / "templates" / "marimo_notebook_template.py"
)


def make_project(tmp_path: Path, template: Path, *, with_input: bool) -> Path:
    """Copy a template into a fresh project, with the style module beside it.

    A notebook imports ``beautiful_style`` from its own directory, so the project
    carries a copy of the module. The pixi.toml marks the project root.
    """
    project = tmp_path / "project"
    project.mkdir()
    (project / "pixi.toml").write_text(
        (template.parent / "pixi.toml").read_text(encoding="utf-8")
        if (template.parent / "pixi.toml").exists()
        else "[workspace]\n",
        encoding="utf-8",
    )
    (project / STYLE_MODULE.name).write_text(
        STYLE_MODULE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (project / template.name).write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    if with_input:
        raw = project / "data" / "raw"
        raw.mkdir(parents=True)
        (raw / "events.tsv").write_text(
            "kind\tn\nsplice\t3\nskip\t5\n", encoding="utf-8"
        )
    return project


def run_template(
    project: Path, template: Path, *packages: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            *UV_RUN_BASE,
            *[arg for package in packages for arg in ("--with", package)],
            "python",
            str(project / template.name),
        ],
        text=True,
        capture_output=True,
        check=False,
        cwd=project,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )


def test_jupyter_template_runs_top_to_bottom_in_a_fresh_project(tmp_path):
    template = ROOT / "skills" / "notebooks" / "templates" / "jupyter_kiss_template.py"
    project = make_project(tmp_path, template, with_input=True)

    result = run_template(
        project,
        template,
        "numpy",
        "pandas",
        "matplotlib",
        "duckdb",
        "ipython",
        "cycler",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "data" / "analytics.duckdb").exists()
    assert (project / "outputs" / "top_values.png").exists()


def test_jupyter_template_raises_when_the_input_file_is_missing(tmp_path):
    template = ROOT / "skills" / "notebooks" / "templates" / "jupyter_kiss_template.py"
    project = make_project(tmp_path, template, with_input=False)

    result = run_template(
        project,
        template,
        "numpy",
        "pandas",
        "matplotlib",
        "duckdb",
        "ipython",
        "cycler",
    )

    assert result.returncode != 0
    assert "FileNotFoundError" in result.stderr
    assert "events.tsv" in result.stderr


def test_marimo_template_runs_and_follows_the_structure_rule(tmp_path):
    project = make_project(tmp_path, MARIMO_TEMPLATE, with_input=False)

    result = run_template(
        project, MARIMO_TEMPLATE, "marimo", "numpy", "pandas", "matplotlib"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "outputs" / "example_figure.png").exists()


def marimo_cells(template: Path) -> list[ast.FunctionDef]:
    tree = ast.parse(template.read_text(encoding="utf-8"))
    return [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any("cell" in ast.unparse(decorator) for decorator in node.decorator_list)
    ]


def is_markdown_cell(cell: ast.FunctionDef) -> bool:
    return "mo.md(" in ast.unparse(cell)


def test_marimo_template_opens_with_markdown_and_follows_each_figure_with_a_caption():
    cells = marimo_cells(MARIMO_TEMPLATE)
    assert is_markdown_cell(cells[0]), (
        "first cell must be the markdown title and purpose"
    )
    figure_positions = [
        i for i, cell in enumerate(cells) if "savefig(" in ast.unparse(cell)
    ]
    assert figure_positions
    for position in figure_positions:
        assert position + 1 < len(cells), "the figure cell is the last cell"
        assert is_markdown_cell(cells[position + 1]), "a caption cell must follow"
        assert ".set_title(" not in ast.unparse(cells[position]), "no in-plot title"


def test_notebook_templates_import_the_style_module_instead_of_copying_its_values():
    templates = ROOT / "skills" / "notebooks" / "templates"
    for template in (templates / "jupyter_kiss_template.py", MARIMO_TEMPLATE):
        text = template.read_text(encoding="utf-8")
        assert "from beautiful_style import set_beautiful_style" in text, template.name
        assert "rcParams.update" not in text, template.name
        assert "dpi=" not in text, template.name
    plot_style = (
        ROOT / "skills" / "notebooks" / "references" / "plot_style.md"
    ).read_text()
    assert "rcParams.update" not in plot_style
    assert "120" not in plot_style
