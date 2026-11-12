import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "notebooks"
SCRIPT = SKILL / "scripts" / "convert_notebook.py"


def test_marimo_to_jupyter_and_jupyter_to_marimo(tmp_path):
    ipynb = tmp_path / "from_marimo.ipynb"
    result = subprocess.run(["uv", "run", "--script", str(SCRIPT), str(SKILL / "fixtures" / "simple_marimo.py"), "--to", "jupyter", "--out", str(ipynb)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(ipynb.read_text())["cells"]

    marimo = tmp_path / "from_jupyter.py"
    result = subprocess.run(["uv", "run", "--script", str(SCRIPT), str(SKILL / "fixtures" / "simple_jupyter.ipynb"), "--to", "marimo", "--out", str(marimo)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "marimo.App" in marimo.read_text()


def test_template_has_bounded_dependencies_and_kernel_placeholder():
    pixi = (SKILL / "templates" / "pixi.toml").read_text()
    assert '= "*"' not in pixi
    template = (SKILL / "templates" / "jupyter_kiss_template.py").read_text()
    assert "name: <PIXI_PROJECT_KERNEL>" in template
    assert "name: python" not in template


SKILL_TEXT = (SKILL / "SKILL.md").read_text()


def header_dependencies(path):
    """Return the dependency strings of a PEP 723 header."""
    header = path.read_text().split("# dependencies = [", 1)[1]
    block = header.split("]", 1)[0]
    return re.findall(r"\"([^\"]+)\"", block)


def test_script_and_template_headers_declare_lower_bounds_only():
    paths = [
        *sorted((SKILL / "scripts").glob("*.py")),
        SKILL / "templates" / "marimo_notebook_template.py",
    ]
    for path in paths:
        dependencies = header_dependencies(path)
        assert dependencies, path
        for dependency in dependencies:
            assert ">=" in dependency, f"{path.name}: {dependency} has no lower bound"
            assert not re.search(r"==|<|~=|\*", dependency), (
                f"{path.name}: {dependency}"
            )
    pixi = (SKILL / "templates" / "pixi.toml").read_text()
    assert not re.search(r'= "[^"]*(==|<|~=|\*)', pixi)


def test_cell_limit_is_50_lines_in_every_document():
    structure = (SKILL / "references" / "notebook_structure.md").read_text()
    assert "25 lines" not in structure
    assert "50 lines" in structure
    assert "bounded" not in SKILL_TEXT
    assert "lower bound" in SKILL_TEXT


def test_skill_names_reference_and_template_files_as_markdown_links():
    spans = re.findall(r"`([^`\n]+)`", SKILL_TEXT)
    unlinked = [
        span
        for span in spans
        if span.endswith(".md") or span.startswith(("references/", "templates/"))
    ]
    assert unlinked == []


def test_step_9_documents_the_flags_of_convert_notebook():
    assert "--to marimo --out" in SKILL_TEXT
    assert "--to jupyter --out" in SKILL_TEXT
    assert "uvx marimo convert" not in SKILL_TEXT


def test_jupyter_fixture_has_unique_cell_ids():
    notebook = json.loads((SKILL / "fixtures" / "simple_jupyter.ipynb").read_text())
    assert (notebook["nbformat"], notebook["nbformat_minor"]) == (4, 5)
    ids = [cell.get("id") for cell in notebook["cells"]]
    assert all(ids)
    assert len(set(ids)) == len(ids)
