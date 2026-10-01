import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "beautiful-data-viz"
EXPORT = SKILL / "scripts" / "export_fixture.py"


def test_fixture_exports_png_svg_and_pdf(tmp_path):
    target = tmp_path / "growth"
    result = subprocess.run(["uv", "run", "--script", str(EXPORT), str(SKILL / "fixtures" / "growth_curve.csv"), "--out", str(target), "--background", "dark"], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    for suffix in ("png", "svg", "pdf"):
        path = target.with_suffix(f".{suffix}")
        assert path.is_file() and path.stat().st_size > 100
    metadata = json.loads(target.with_suffix(".json").read_text())
    assert metadata["annotation_colors"]
    assert set(metadata["annotation_colors"]) == {metadata["text_color"]}


def test_default_series_colors_are_neutral_greys(tmp_path: Path) -> None:
    target = tmp_path / "growth"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--script",
            str(EXPORT),
            str(SKILL / "fixtures" / "growth_curve.csv"),
            "--out",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    colors = json.loads(target.with_suffix(".json").read_text())["line_colors"]
    assert colors
    for color in colors:
        red, green, blue = (color[i : i + 2] for i in (1, 3, 5))
        assert red == green == blue, f"default series color {color} is not grey"
