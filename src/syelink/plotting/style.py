"""Plot styling configuration for syelink visualizations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationPlotStyle:
    """Style configuration for validation plots.

    All colors can be any matplotlib-compatible color string
    (hex, named colors, RGB tuples, etc.)

    Example:
        >>> style = ValidationPlotStyle(
        ...     color_left="red",
        ...     color_right="blue",
        ...     marker_size=300,
        ... )
        >>> plot_validation(session, style=style)

    """

    # Eye colors
    color_left: str = "#00FFFF"  # Cyan
    color_right: str = "#4169E1"  # Royal blue

    # Target and screen colors
    color_target: str = "#000000"  # Black
    color_screen: str = "#888888"  # Gray

    # Marker settings
    marker: str = "+"
    marker_size: float = 200
    marker_linewidth: float = 2

    # Line settings (connecting target to gaze)
    line_style: str = "--"
    line_width: float = 1.5
    line_alpha: float = 0.8

    # Label settings
    label_fontsize: float = 11
    label_fontweight: str = "bold"
    show_labels: bool = True

    # Figure settings
    figsize: tuple[float, float] = (12, 10)
    dpi: int = 150
    title_fontsize: float = 14

    # Legend settings
    show_legend: bool = True
    legend_loc: str = "upper right"
    legend_fontsize: float = 10


@dataclass
class CalibrationPlotStyle:
    """Style configuration for calibration plots.

    Example:
        >>> style = CalibrationPlotStyle(
        ...     color_left="green",
        ...     color_right="purple",
        ... )
        >>> plot_calibration_raw(session, style=style)

    """

    # Eye colors
    color_left: str = "cyan"
    color_right: str = "magenta"

    # Marker settings
    marker: str = "+"
    marker_size: float = 300
    marker_linewidth: float = 2

    # Grid settings
    show_grid: bool = True
    grid_alpha: float = 0.3

    # Figure settings
    figsize: tuple[float, float] = (16, 7)
    dpi: int = 150
    title_fontsize: float = 14
    label_fontsize: float = 12


# Default styles
DEFAULT_VALIDATION_STYLE = ValidationPlotStyle()
DEFAULT_CALIBRATION_STYLE = CalibrationPlotStyle()
