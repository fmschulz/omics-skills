import json
import os
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


STYLE = SKILL / "assets" / "beautiful_style.py"

LOAD_STYLE = f"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("beautiful_style", {str(STYLE)!r})
style = importlib.util.module_from_spec(spec)
sys.modules["beautiful_style"] = style
spec.loader.exec_module(style)
"""


def run_python(code: str, *packages: str) -> subprocess.CompletedProcess:
    command = ["uv", "run", "--no-project"]
    for package in packages:
        command += ["--with", package]
    return subprocess.run(
        [*command, "python", "-c", LOAD_STYLE + code],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )


def test_finalize_axes_keeps_constrained_layout_without_a_warning() -> None:
    result = run_python(
        """
import warnings
import matplotlib.pyplot as plt
fig, ax = plt.subplots(constrained_layout=True)
ax.plot([0, 1], [0, 1])
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    style.finalize_axes(ax, title="t", xlabel="x", ylabel="y")
    fig.canvas.draw()
print(json.dumps({
    "warnings": [str(item.message) for item in caught],
    "engine": type(fig.get_layout_engine()).__name__,
}))
""",
        "matplotlib",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["warnings"] == []
    assert outcome["engine"] == "ConstrainedLayoutEngine"


def test_finalize_axes_still_applies_tight_layout_without_a_layout_engine() -> None:
    result = run_python(
        """
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
before = fig.subplotpars.left
ax.set_ylabel("a rather long y axis label\\nover two lines")
style.finalize_axes(ax, title="t")
print(json.dumps(bool(fig.subplotpars.left != before)))
""",
        "matplotlib",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) is True


FONT_SIZES = """
import matplotlib as mpl
sizes = {}
themed = {}
for medium in ("paper", "notebook", "slides"):
    style.set_beautiful_style(medium=medium)
    sizes[medium] = mpl.rcParams["font.size"]
    themed[medium] = mpl.rcParams["axes.axisbelow"]
print(json.dumps({"sizes": sizes, "themed": themed}))
"""


def test_font_size_per_medium_is_the_same_with_and_without_seaborn() -> None:
    plain = run_python(FONT_SIZES, "matplotlib")
    themed = run_python(FONT_SIZES, "matplotlib", "seaborn")
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert themed.returncode == 0, themed.stdout + themed.stderr

    without_seaborn = json.loads(plain.stdout)
    with_seaborn = json.loads(themed.stdout)

    assert with_seaborn["sizes"] == without_seaborn["sizes"]
    sizes = with_seaborn["sizes"]
    assert sizes["paper"] < sizes["notebook"] < sizes["slides"]
    # seaborn's white theme sets axes.axisbelow, so this shows it ran for every medium.
    assert set(with_seaborn["themed"].values()) == {True}
