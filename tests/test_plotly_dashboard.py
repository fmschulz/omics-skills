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
