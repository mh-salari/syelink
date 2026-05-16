"""Plot calibration points (P-CR in HREF angular space) for both eyes.

Shows the polynomial input — the P-CR feature in HREF coordinates — at each cal target.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from syelink.plotting.style import DEFAULT_CALIBRATION_STYLE

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.figure import Figure

    from syelink.models import SessionData
    from syelink.plotting.style import CalibrationPlotStyle


def plot_calibration_raw(
    session: SessionData,
    cal_index: int = 0,
    save_path: str | Path | None = None,
    style: CalibrationPlotStyle | None = None,
) -> Figure:
    """Plot RAW calibration points for both eyes on single plot.

    Args:
        session: SessionData object containing calibration data
        cal_index: Which calibration to plot (0-based index)
        save_path: Optional path to save the figure
        style: Optional CalibrationPlotStyle for customizing colors, markers, etc.

    Returns:
        matplotlib Figure object

    Example:
        >>> from syelink.plotting import plot_calibration_raw, CalibrationPlotStyle
        >>> style = CalibrationPlotStyle(color_left="green", color_right="orange")
        >>> fig = plot_calibration_raw(session, style=style)

    """
    if style is None:
        style = DEFAULT_CALIBRATION_STYLE

    cal = session.calibrations[cal_index]

    fig, axes = plt.subplots(1, 2, figsize=style.figsize)

    colors = {"left": style.color_left, "right": style.color_right}

    for ax, eye in zip(axes, ["left", "right"], strict=False):
        eye_data = cal.left_eye if eye == "left" else cal.right_eye
        if not eye_data:
            ax.text(
                0.5,
                0.5,
                f"No {eye.upper()} eye data",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(f"{eye.upper()} Eye")
            continue

        points = eye_data.points
        result = eye_data.result

        # Get calibration points (exclude origin point 10)
        cal_points = [p for p in points if p.point_number != 10]

        xs = [p.pcr_href_x for p in cal_points]
        ys = [p.pcr_href_y for p in cal_points]

        ax.scatter(
            xs,
            ys,
            c=colors[eye],
            marker=style.marker,
            s=style.marker_size,
            linewidths=style.marker_linewidth,
        )

        ax.set_xlabel("P-CR X (HREF angular units)", fontsize=style.label_fontsize)
        ax.set_ylabel("P-CR Y (HREF angular units)", fontsize=style.label_fontsize)
        if style.show_grid:
            ax.grid(True, alpha=style.grid_alpha)
        ax.set_aspect("equal")
        ax.invert_yaxis()
        ax.set_title(f"{eye.upper()} Eye - {result}", fontsize=style.label_fontsize, fontweight="bold")

    fig.suptitle(
        f"Calibration #{cal_index + 1} — P-CR in HREF (polynomial input)\n"
        f"Timestamp: {cal.timestamp} ms, Type: {cal.calibration_type}, Mode: {cal.tracking_mode}",
        fontsize=style.title_fontsize,
        fontweight="bold",
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=style.dpi, bbox_inches="tight")

    return fig
