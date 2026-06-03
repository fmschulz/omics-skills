"""Beautiful plotting defaults for matplotlib / seaborn.

Goal:
- Publication-quality plots with readable labels, minimal whitespace, and sensible defaults.
- Works in Jupyter notebooks.
- Matplotlib-first; uses seaborn if available for easier theming.

References:
- Seaborn aesthetics + palettes: https://seaborn.pydata.org/
- LearnUI palette guidance: https://www.learnui.design/tools/data-color-picker.html
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


@dataclass(frozen=True)
class VizConfig:
    medium: str = "notebook"      # notebook | paper | slides
    background: str = "light"     # light | dark
    font_scale: float = 1.0
    dpi: int = 150


TUFTE_COLORS = {
    "light_bg": "#ffffff",
    "dark_bg": "#151515",
    "light_text": "#111111",
    "dark_text": "#dddddd",
    "light_secondary": "#666666",
    "dark_secondary": "#999999",
    "light_axis": "#cccccc",
    "dark_axis": "#444444",
    "series_default": "#666666",
    "series_default_dark": "#999999",
    "highlight": "#e41a1c",
    "highlight_dark": "#fc8d62",
    "min": "#e15759",
    "max": "#4e79a7",
}


def _maybe_set_retina() -> None:
    """Make notebook output crisper if running inside IPython."""
    try:
        from IPython import get_ipython  # type: ignore
        ip = get_ipython()
        if ip is not None:
            ip.run_line_magic("config", "InlineBackend.figure_format = 'retina'")
    except Exception:
        pass


def set_beautiful_style(*, medium: str = "notebook", background: str = "light", font_scale: float = 1.0, dpi: int = 150) -> VizConfig:
    """Set global plotting defaults.

    Parameters
    ----------
    medium:
        notebook | paper | slides
    background:
        light | dark
    font_scale:
        Additional scale factor applied to font sizes.
    dpi:
        Figure DPI for notebook rendering.
    """
    _maybe_set_retina()

    # Base size ladder (points)
    base = {
        "paper":   {"title": 11, "label": 9,  "tick": 8,  "legend": 8},
        "notebook":{"title": 13, "label": 11, "tick": 10, "legend": 10},
        "slides":  {"title": 18, "label": 14, "tick": 12, "legend": 12},
    }.get(medium, {"title": 13, "label": 11, "tick": 10, "legend": 10})

    title = base["title"] * font_scale
    label = base["label"] * font_scale
    tick = base["tick"] * font_scale
    legend = base["legend"] * font_scale

    is_dark = background.lower() == "dark"

    # Tufte-inspired neutral ink colors (avoid pure black/white).
    fg = TUFTE_COLORS["dark_text"] if is_dark else TUFTE_COLORS["light_text"]
    grid = TUFTE_COLORS["dark_axis"] if is_dark else TUFTE_COLORS["light_axis"]
    face = TUFTE_COLORS["dark_bg"] if is_dark else TUFTE_COLORS["light_bg"]
    secondary = TUFTE_COLORS["dark_secondary"] if is_dark else TUFTE_COLORS["light_secondary"]

    rc = {
        # Figure / save
        "figure.dpi": dpi,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "figure.facecolor": face,
        "axes.facecolor": face,

        # Typography
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"],
        "text.color": fg,
        "axes.labelcolor": secondary,
        "axes.titlecolor": fg,
        "axes.titlesize": title,
        "axes.labelsize": label,
        "xtick.color": fg,
        "ytick.color": fg,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,

        # Lines / markers
        "lines.linewidth": 1.5,
        "lines.markersize": 3,

        # Axes / spines
        "axes.edgecolor": grid,
        "axes.linewidth": 0.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": grid,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.12,

        # Ticks
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 4,
        "ytick.major.size": 4,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,

        # Legend
        "legend.frameon": False,
        "legend.fontsize": legend,
        "legend.title_fontsize": legend,
    }

    mpl.rcParams.update(rc)

    # If seaborn is available, use it for coherent themes/palettes.
    try:
        import seaborn as sns  # type: ignore
        sns.set_theme(style="white", context=medium)
        sns.set_context(medium, font_scale=font_scale)
        sns.set_palette("colorblind")
        mpl.rcParams.update(rc)
    except Exception:
        pass

    return VizConfig(medium=medium, background=background, font_scale=font_scale, dpi=dpi)


def despine(ax: Axes) -> Axes:
    """Remove top/right spines and soften left/bottom."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.8)
    ax.spines["bottom"].set_alpha(0.8)
    return ax


def apply_range_frame(ax: Axes, x_data: Sequence[float], y_data: Sequence[float]) -> Axes:
    """Constrain visible axis lines to the observed data range."""
    despine(ax)
    x_values = list(x_data)
    y_values = list(y_data)
    if x_values:
        ax.spines["bottom"].set_bounds(min(x_values), max(x_values))
    if y_values:
        ax.spines["left"].set_bounds(min(y_values), max(y_values))
    ax.tick_params(direction="in", length=3, width=0.5)
    return ax


def direct_label(
    ax: Axes,
    x_data: Sequence[float],
    y_data: Sequence[float],
    label: str,
    *,
    color: str = TUFTE_COLORS["series_default"],
    offset: tuple[float, float] = (8, 0),
) -> Axes:
    """Label a series at its final point instead of using a legend."""
    x_values = list(x_data)
    y_values = list(y_data)
    if not x_values or not y_values:
        return ax
    ax.annotate(
        label,
        xy=(x_values[-1], y_values[-1]),
        xytext=offset,
        textcoords="offset points",
        color=color,
        fontsize=mpl.rcParams.get("axes.labelsize", 10),
        va="center",
    )
    return ax


def annotate_point(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    *,
    color: str = "#333333",
    offset: tuple[float, float] = (0, 24),
) -> Axes:
    """Annotate one notable point with a restrained leader line."""
    ax.annotate(
        text,
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        color=color,
        fontsize=mpl.rcParams.get("xtick.labelsize", 9),
        fontstyle="italic",
        ha="center",
        arrowprops={"arrowstyle": "-", "color": mpl.rcParams["axes.edgecolor"], "lw": 0.5},
    )
    return ax


def sparkline(
    ax: Axes,
    values: Sequence[float],
    *,
    color: str = TUFTE_COLORS["series_default"],
    mark_min_max: bool = True,
    mark_endpoint: bool = True,
) -> Axes:
    """Draw a compact trend with no axes or grid."""
    data = list(values)
    if not data:
        return ax
    x = list(range(len(data)))
    ax.plot(x, data, color=color, linewidth=1)
    if mark_min_max:
        min_i = min(range(len(data)), key=data.__getitem__)
        max_i = max(range(len(data)), key=data.__getitem__)
        ax.plot(min_i, data[min_i], "o", color=TUFTE_COLORS["min"], markersize=2)
        ax.plot(max_i, data[max_i], "o", color=TUFTE_COLORS["max"], markersize=2)
    if mark_endpoint:
        ax.plot(x[-1], data[-1], "o", color=color, markersize=2)
    ax.set_xlim(0, len(data) - 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def minimize_whitespace(ax: Axes, *, x: float = 0.02, y: float = 0.05) -> Axes:
    """Reduce default margins while keeping slight breathing room."""
    ax.margins(x=x, y=y)
    return ax


def finalize_axes(
    ax: Axes,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    tight: bool = True,
) -> Axes:
    """Apply final presentation tweaks."""
    despine(ax)
    minimize_whitespace(ax)

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    if title:
        ax.set_title(title, loc="left", pad=10, weight="semibold")
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, ha="left", va="bottom")

    # Prefer y-grid only for most charts
    ax.xaxis.grid(False)

    if tight:
        fig = ax.figure
        if isinstance(fig, Figure):
            try:
                fig.tight_layout()
            except Exception:
                pass

    return ax
