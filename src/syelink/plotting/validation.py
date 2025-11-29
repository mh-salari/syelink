"""Create validation plots showing target positions and gaze offsets.

Shows left and right eye data with error vectors and offset labels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from adjustText import adjust_text
from matplotlib import patches
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image

from syelink.plotting.style import DEFAULT_VALIDATION_STYLE

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.figure import Figure

    from syelink.models import SessionData
    from syelink.plotting.style import ValidationPlotStyle


def plot_validation(
    session: SessionData,
    validation_index: int = 0,
    save_path: str | Path | None = None,
    target_scale: float = 0.015,
    target_image_path: str | Path | None = None,
    style: ValidationPlotStyle | None = None,
    show_connectors: bool = False,
) -> Figure:
    """Plot a single validation showing left and right eye data.

    Args:
        session: SessionData object containing validation data
        validation_index: Index of validation to plot (0-based)
        save_path: Optional path to save the plot
        target_scale: Scaling factor for target image size (default: 0.015)
        target_image_path: Optional path to custom target image
        style: Optional ValidationPlotStyle for customizing colors, markers, etc.
        show_connectors: Whether to draw connector lines from original label positions
            to adjusted label positions (default: False)

    Returns:
        matplotlib Figure object

    Example:
        >>> from syelink.plotting import plot_validation, ValidationPlotStyle
        >>> style = ValidationPlotStyle(color_left="red", color_right="green")
        >>> fig = plot_validation(session, style=style, show_connectors=True)

    """
    if style is None:
        style = DEFAULT_VALIDATION_STYLE

    # Get display coordinates
    if not session.display_coords:
        msg = "Session data missing display_coords"
        raise ValueError(msg)

    dc = session.display_coords
    screen_w = dc.width
    screen_h = dc.height

    # Get validation data
    validation = session.validations[validation_index]

    if not validation.targets:
        msg = f"Validation {validation_index} has no target data"
        raise ValueError(msg)

    # Get targets
    targets = validation.targets.targets
    target_x = [t[0] for t in targets]
    target_y = [t[1] for t in targets]

    # Get validation points
    points = validation.points

    # Separate left and right eye data
    left_data = [p for p in points if p.eye == "LEFT"]
    right_data = [p for p in points if p.eye == "RIGHT"]

    # Get summary statistics
    summary_left = validation.summary_left
    summary_right = validation.summary_right

    # Create figure
    fig, ax = plt.subplots(figsize=style.figsize)

    # Calculate axis limits with padding
    all_gaze_x = [p.gaze_x for p in points]
    all_gaze_y = [p.gaze_y for p in points]
    padding = 20
    xlim = [min(0, *all_gaze_x) - padding, max(screen_w, *all_gaze_x) + padding]
    ylim = [min(0, *all_gaze_y) - padding, max(screen_h, *all_gaze_y) + padding]

    # Draw screen boundary
    screen_rect = patches.Rectangle(
        (0, 0),
        screen_w,
        screen_h,
        linewidth=2,
        edgecolor=style.color_screen,
        facecolor="none",
    )
    ax.add_patch(screen_rect)

    # Load and display target image if provided, otherwise use simple markers
    if target_image_path:
        target_img = Image.open(target_image_path)
        zoom = target_scale * (xlim[1] - xlim[0]) / target_img.width
        for tx, ty in zip(target_x, target_y, strict=False):
            imagebox = OffsetImage(target_img, zoom=zoom)
            ab = AnnotationBbox(imagebox, (tx, ty), frameon=False, pad=0)
            ax.add_artist(ab)
    else:
        # Fallback: plot target markers as simple crosses
        ax.scatter(
            target_x,
            target_y,
            c=style.color_target,
            marker="x",
            s=style.marker_size,
            linewidths=style.marker_linewidth,
            zorder=1,
        )

    # Collect text labels for adjustment
    texts = []

    # Plot left eye data
    for p in left_data:
        target = targets[p.point_number]
        tx, ty = target[0], target[1]
        gx, gy = p.gaze_x, p.gaze_y

        # Draw line from target to gaze point
        ax.plot(
            [tx, gx],
            [ty, gy],
            color=style.color_left,
            linewidth=style.line_width,
            linestyle=style.line_style,
            alpha=style.line_alpha,
            zorder=2,
        )

        # Draw gaze point marker
        ax.scatter(
            gx,
            gy,
            c=style.color_left,
            marker=style.marker,
            s=style.marker_size,
            linewidths=style.marker_linewidth,
            zorder=3,
        )

        # Add label
        if style.show_labels:
            label = f"{p.offset_deg:.2f}"
            # Place label at gaze point (let adjustText handle overlap)
            text = ax.text(
                gx,
                gy,
                label,
                fontsize=style.label_fontsize,
                fontweight=style.label_fontweight,
                color=style.color_left,
                zorder=4,
            )
            texts.append(text)

    # Plot right eye data
    for p in right_data:
        target = targets[p.point_number]
        tx, ty = target[0], target[1]
        gx, gy = p.gaze_x, p.gaze_y

        # Draw line from target to gaze point
        ax.plot(
            [tx, gx],
            [ty, gy],
            color=style.color_right,
            linewidth=style.line_width,
            linestyle=style.line_style,
            alpha=style.line_alpha,
            zorder=2,
        )

        # Draw gaze point marker
        ax.scatter(
            gx,
            gy,
            c=style.color_right,
            marker=style.marker,
            s=style.marker_size,
            linewidths=style.marker_linewidth,
            zorder=3,
        )

        # Add label
        if style.show_labels:
            label = f"{p.offset_deg:.2f}"
            # Place label at gaze point (let adjustText handle overlap)
            text = ax.text(
                gx,
                gy,
                label,
                fontsize=style.label_fontsize,
                fontweight=style.label_fontweight,
                color=style.color_right,
                zorder=4,
            )
            texts.append(text)

    # Store original text positions before adjustment
    original_positions = [(t.get_position(), t) for t in texts]

    # Adjust text labels to avoid overlaps
    if texts:
        # Prepare target positions for adjustText points argument
        target_points = [(float(tx), float(ty)) for tx, ty in zip(target_x, target_y, strict=False)]
        adjust_text(
            texts,
            points=target_points,
            expand=(1.1, 1.1),
            force_points=(1.5, 1.5),
            force_text=(0.7, 0.7),
            ax=ax,
        )

        # Draw connector lines only if requested
        if show_connectors:
            for orig_pos, text in original_positions:
                new_pos = text.get_position()
                # Only draw line if text was actually moved
                if abs(orig_pos[0] - new_pos[0]) > 1 or abs(orig_pos[1] - new_pos[1]) > 1:
                    ax.plot(
                        [orig_pos[0], new_pos[0]],
                        [orig_pos[1], new_pos[1]],
                        color="gray",
                        lw=0.5,
                        alpha=0.5,
                        zorder=3,
                    )

    # Set axis properties
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.invert_yaxis()  # Invert y-axis to match screen coordinates
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X (pixels)", fontsize=12)
    ax.set_ylabel("Y (pixels)", fontsize=12)

    # Create title with summary statistics
    title_parts = [f"Validation #{validation_index + 1}"]
    if summary_left:
        title_parts.append(f"Left eye: {summary_left.error_avg_deg:.2f}° avg, {summary_left.error_max_deg:.2f}° max")
    if summary_right:
        title_parts.append(
            f"Right eye: {summary_right.error_avg_deg:.2f}° avg, {summary_right.error_max_deg:.2f}° max"
        )

    ax.set_title("\n".join(title_parts), fontsize=style.title_fontsize, fontweight="bold", pad=20)

    # Add legend
    if style.show_legend:
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker=style.marker,
                color=style.color_left,
                markerfacecolor=style.color_left,
                markeredgecolor=style.color_left,
                markersize=12,
                markeredgewidth=2,
                label="Left eye",
                linestyle=style.line_style,
                linewidth=style.line_width,
            ),
            Line2D(
                [0],
                [0],
                marker=style.marker,
                color=style.color_right,
                markerfacecolor=style.color_right,
                markeredgecolor=style.color_right,
                markersize=12,
                markeredgewidth=2,
                label="Right eye",
                linestyle=style.line_style,
                linewidth=style.line_width,
            ),
            Line2D(
                [0],
                [0],
                marker=style.marker,
                color=style.color_target,
                markerfacecolor=style.color_target,
                markeredgecolor=style.color_target,
                markersize=10,
                label="Target",
                linestyle="",
            ),
        ]
        ax.legend(handles=legend_elements, loc=style.legend_loc, fontsize=style.legend_fontsize, framealpha=0.9)

    plt.tight_layout()

    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=style.dpi, bbox_inches="tight", facecolor="white")

    return fig
