"""Command-line interface for syelink.

Provides commands for parsing ASC files and creating visualizations.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from syelink.extract import parse_asc_file
from syelink.models import SessionData
from syelink.plotting import plot_calibration_raw, plot_validation


def cmd_parse(args: argparse.Namespace) -> int:
    """Parse an ASC file and save as JSON."""
    asc_path = Path(args.asc_file)
    if not asc_path.exists():
        print(f"Error: File not found: {asc_path}", file=sys.stderr)
        return 1

    print(f"Parsing {asc_path}...")

    session = parse_asc_file(asc_path)

    # Determine output path
    output_path = Path(args.output) if args.output else asc_path.with_suffix(".json")

    session.save_json(str(output_path))

    print(f"Saved to {output_path}")
    print(f"  - {len(session.calibrations)} calibrations")
    print(f"  - {len(session.validations)} validations")
    if session.display_coords:
        print(f"  - Display: {session.display_coords.width}x{session.display_coords.height}")

    return 0


def cmd_plot_validation(args: argparse.Namespace) -> int:
    """Plot validation data from JSON file."""
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return 1

    session = SessionData.load_json(str(json_path))

    if args.index >= len(session.validations):
        print(
            f"Error: Validation index {args.index} out of range (0-{len(session.validations) - 1})",
            file=sys.stderr,
        )
        return 1

    # Determine output path
    save_path = Path(args.output) if args.output else json_path.parent / f"validation_{args.index}.png"

    plot_validation(
        session,
        validation_index=args.index,
        save_path=save_path,
        target_image_path=args.target_image,
    )

    print(f"Saved plot to {save_path}")

    if args.show:
        plt.show()

    return 0


def cmd_plot_calibration(args: argparse.Namespace) -> int:
    """Plot calibration data from JSON file."""
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return 1

    session = SessionData.load_json(str(json_path))

    if args.index >= len(session.calibrations):
        print(
            f"Error: Calibration index {args.index} out of range (0-{len(session.calibrations) - 1})",
            file=sys.stderr,
        )
        return 1

    # Determine output path
    save_path = Path(args.output) if args.output else json_path.parent / f"calibration_{args.index}.png"

    plot_calibration_raw(
        session,
        cal_index=args.index,
        save_path=save_path,
    )

    print(f"Saved plot to {save_path}")

    if args.show:
        plt.show()

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show information about a JSON session file."""
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return 1

    session = SessionData.load_json(str(json_path))

    print(f"Session: {json_path.name}")
    print("=" * 60)

    if session.display_coords:
        dc = session.display_coords
        print(f"Display: {dc.width}x{dc.height} pixels")
        print()

    print(f"Calibrations: {len(session.calibrations)}")
    for i, cal in enumerate(session.calibrations):
        left_result = cal.left_eye.result if cal.left_eye else "N/A"
        right_result = cal.right_eye.result if cal.right_eye else "N/A"
        print(f"  [{i}] {cal.calibration_type} @ {cal.timestamp}ms - L:{left_result} R:{right_result}")

    print()
    print(f"Validations: {len(session.validations)}")
    for i, val in enumerate(session.validations):
        left_err = f"{val.summary_left.error_avg_deg:.2f}°" if val.summary_left else "N/A"
        right_err = f"{val.summary_right.error_avg_deg:.2f}°" if val.summary_right else "N/A"
        print(f"  [{i}] {val.validation_type} @ {val.timestamp}ms - L:{left_err} R:{right_err}")

    return 0


def cmd_export_text(args: argparse.Namespace) -> int:
    """Export ASC file data to text files."""
    asc_path = Path(args.asc_file)
    if not asc_path.exists():
        print(f"Error: File not found: {asc_path}", file=sys.stderr)
        return 1

    print(f"Parsing {asc_path}...")
    session = parse_asc_file(asc_path)

    # Determine output directory
    output_dir = Path(args.output) if args.output else asc_path.parent

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}", file=sys.stderr)
        return 1

    print("Exporting to text files...")

    # Use ASC filename (without extension) as prefix for output files
    filename_prefix = asc_path.stem

    # Save recordings
    rec_file = session.save_recordings_text(output_dir, filename_prefix)
    print(f"  ✓ {rec_file.name}")

    # Save calibrations
    cal_file = session.save_calibrations_text(output_dir, filename_prefix)
    print(f"  ✓ {cal_file.name}")

    # Save validations
    val_file = session.save_validations_text(output_dir, filename_prefix)
    print(f"  ✓ {val_file.name}")

    # Save metadata
    metadata_file = output_dir / f"{filename_prefix}_metadata.txt"
    session.save_metadata(metadata_file)
    print(f"  ✓ {metadata_file.name}")

    print(f"\nAll files saved to: {output_dir}")

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="syelink",
        description="Parse and visualize EyeLink eye tracker data",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse ASC file to JSON")
    parse_parser.add_argument("asc_file", help="Path to the ASC file")
    parse_parser.add_argument("-o", "--output", help="Output JSON file path")
    parse_parser.set_defaults(func=cmd_parse)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show session information")
    info_parser.add_argument("json_file", help="Path to the JSON session file")
    info_parser.set_defaults(func=cmd_info)

    # Export text command
    export_parser = subparsers.add_parser("export-text", help="Export ASC file to text files")
    export_parser.add_argument("asc_file", help="Path to the ASC file")
    export_parser.add_argument("-o", "--output", help="Output directory (default: same as ASC file)")
    export_parser.set_defaults(func=cmd_export_text)

    # Plot validation command
    plot_val_parser = subparsers.add_parser("plot-validation", help="Plot validation data")
    plot_val_parser.add_argument("json_file", help="Path to the JSON session file")
    plot_val_parser.add_argument("-i", "--index", type=int, default=0, help="Validation index (default: 0)")
    plot_val_parser.add_argument("-o", "--output", help="Output image path")
    plot_val_parser.add_argument("--target-image", help="Path to custom target image")
    plot_val_parser.add_argument("--show", action="store_true", help="Show plot interactively")
    plot_val_parser.set_defaults(func=cmd_plot_validation)

    # Plot calibration command
    plot_cal_parser = subparsers.add_parser("plot-calibration", help="Plot calibration data")
    plot_cal_parser.add_argument("json_file", help="Path to the JSON session file")
    plot_cal_parser.add_argument("-i", "--index", type=int, default=0, help="Calibration index (default: 0)")
    plot_cal_parser.add_argument("-o", "--output", help="Output image path")
    plot_cal_parser.add_argument("--show", action="store_true", help="Show plot interactively")
    plot_cal_parser.set_defaults(func=cmd_plot_calibration)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
