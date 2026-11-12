import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "beautiful-data-viz"
APP = SKILL / "examples" / "dash_app.py"


def test_runnable_app_starts_and_meets_callback_latency_budget():
    result = subprocess.run(["uv", "run", "--script", str(APP), "--smoke", "--latency-budget-ms", "300"], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["http_status"] == 200
    assert payload["callback_p95_ms"] <= payload["latency_budget_ms"]


def test_skill_links_dash_reference_and_reference_links_runnable_example():
    text = (SKILL / "SKILL.md").read_text()
    assert "[references/dash.md](references/dash.md)" in text
    dash = (SKILL / "references" / "dash.md").read_text()
    assert "[../examples/dash_app.py](../examples/dash_app.py)" in dash
    assert "examples/dash_app.py --smoke" in dash


TEMPLATE_PACKAGES = ("dash", "plotly")


def reference_template_source() -> str:
    """Return the template code block of references/dash.md."""
    text = (SKILL / "references" / "dash.md").read_text()
    return (
        text.split("## Figure template", 1)[1]
        .split("```python", 1)[1]
        .split("```", 1)[0]
    )


def test_example_registers_the_template_of_the_reference_without_y_gridlines():
    code = f"""
import importlib.util, json
import plotly.io as pio
{reference_template_source()}
reference = pio.templates["dash_ui"].layout.to_plotly_json()
spec = importlib.util.spec_from_file_location("dash_app", {str(APP)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
example = module.TEMPLATE.layout.to_plotly_json()
print(json.dumps({{
    "reference": reference,
    "example": example,
    "default": pio.templates.default,
}}))
"""
    command = ["uv", "run", "--no-project"]
    for package in TEMPLATE_PACKAGES:
        command += ["--with", package]
    result = subprocess.run(
        [*command, "python", "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.splitlines()[-1])
    assert payload["example"] == payload["reference"]
    assert payload["reference"]["yaxis"]["showgrid"] is False
