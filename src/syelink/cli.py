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


def load_session_data(file_path: Path) -> SessionData:
    """Load session data from either ASC or JSON file.

    Args:
        file_path: Path to ASC or JSON file

    Returns:
        SessionData object

    Raises:
        ValueError: If file format is not supported

    """
    suffix = file_path.suffix.lower()

    if suffix == ".asc":
        return parse_asc_file(file_path)
    if suffix == ".json":
        return SessionData.load_json(str(file_path))
    msg = f"Unsupported file format: {file_path.name}\nExpected ASC or JSON file, got {suffix or 'no extension'}."
    raise ValueError(msg)


def cmd_convert(args: argparse.Namespace) -> int:
    """Convert ASC file to JSON and/or text files."""
    asc_path = Path(args.asc_file)
    if not asc_path.exists():
        print(f"Error: File not found: {asc_path}", file=sys.stderr)
        return 1

    export_json = args.json
    export_text = args.text
    export_samples = args.samples
    if not export_json and not export_text and not export_samples:
        export_json = True
        export_text = True
        export_samples = True

    print(f"Parsing {asc_path}...")

    try:
        session = parse_asc_file(asc_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_dir = Path(args.output) if args.output else asc_path.parent
    filename_prefix = asc_path.stem

    if export_json:
        json_path = output_dir / f"{filename_prefix}.json"
        session.save_json(str(json_path))
        print(f"  ✓ {json_path.name}")

    if export_text:
        if not output_dir.exists():
            print(f"Error: Output directory not found: {output_dir}", file=sys.stderr)
            return 1

        rec_file = session.save_recordings_text(output_dir, filename_prefix)
        print(f"  ✓ {rec_file.name}")

        cal_file = session.save_calibrations_text(output_dir, filename_prefix)
        print(f"  ✓ {cal_file.name}")

        val_file = session.save_validations_text(output_dir, filename_prefix)
        print(f"  ✓ {val_file.name}")

        metadata_file = output_dir / f"{filename_prefix}_metadata.txt"
        session.save_metadata(metadata_file)
        print(f"  ✓ {metadata_file.name}")

    if export_samples and session.gaze_samples:
        csv_path = output_dir / f"{filename_prefix}_samples.csv"
        session.save_samples_csv(str(csv_path))
        samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
        print(f"  ✓ {csv_path.name} ({len(session.gaze_samples):,} samples, {samples_with_raw:,} with raw data)")

    print("\nSession summary:")
    print(f"  - {len(session.calibrations)} calibrations")
    print(f"  - {len(session.validations)} validations")
    if session.gaze_samples:
        samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
        print(f"  - {len(session.gaze_samples):,} gaze samples ({samples_with_raw:,} with raw pupil/CR data)")
    if session.display_coords:
        print(f"  - Display: {session.display_coords.width}x{session.display_coords.height}")
    print(f"\nAll files saved to: {output_dir}")

    return 0


def cmd_plot_validation(args: argparse.Namespace) -> int:
    """Plot validation data from ASC or JSON file."""
    file_path = Path(args.data_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        session = load_session_data(file_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    num_validations = len(session.validations)
    if num_validations == 0:
        print("Error: No validations found in the file", file=sys.stderr)
        return 1

    if args.index >= num_validations:
        print(
            f"Error: Validation index {args.index} out of range (0-{num_validations - 1})",
            file=sys.stderr,
        )
        return 1

    print(f"Found {num_validations} validation(s) in {file_path.name}")
    if num_validations > 1:
        print(f"Plotting validation #{args.index} (use -i to select different validation)")

    # Determine output path with consistent naming
    if args.output:
        save_path = Path(args.output)
    else:
        filename_prefix = file_path.stem
        save_path = file_path.parent / f"{filename_prefix}_validation_{args.index}.png"

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
    """Plot calibration data from ASC or JSON file."""
    file_path = Path(args.data_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        session = load_session_data(file_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    num_calibrations = len(session.calibrations)
    if num_calibrations == 0:
        print("Error: No calibrations found in the file", file=sys.stderr)
        return 1

    if args.index >= num_calibrations:
        print(
            f"Error: Calibration index {args.index} out of range (0-{num_calibrations - 1})",
            file=sys.stderr,
        )
        return 1

    print(f"Found {num_calibrations} calibration(s) in {file_path.name}")
    if num_calibrations > 1:
        print(f"Plotting calibration #{args.index} (use -i to select different calibration)")

    # Determine output path with consistent naming
    if args.output:
        save_path = Path(args.output)
    else:
        filename_prefix = file_path.stem
        save_path = file_path.parent / f"{filename_prefix}_calibration_{args.index}.png"

    plot_calibration_raw(
        session,
        cal_index=args.index,
        save_path=save_path,
    )

    print(f"Saved plot to {save_path}")

    if args.show:
        plt.show()

    return 0


def cmd_export_samples(args: argparse.Namespace) -> int:
    """Export gaze samples to CSV file."""
    file_path = Path(args.data_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        session = load_session_data(file_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not session.gaze_samples:
        print("Error: No gaze samples found in the file", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        csv_path = Path(args.output)
    else:
        filename_prefix = file_path.stem
        csv_path = file_path.parent / f"{filename_prefix}_samples.csv"

    print(f"Exporting {len(session.gaze_samples):,} gaze samples to CSV...")

    try:
        session.save_samples_csv(str(csv_path))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Show statistics
    samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
    print(f"  ✓ Total samples: {len(session.gaze_samples):,}")
    print(
        f"  ✓ Samples with raw pupil/CR data: {samples_with_raw:,} ({samples_with_raw / len(session.gaze_samples) * 100:.1f}%)"
    )

    # Show file size
    size_mb = csv_path.stat().st_size / (1024 * 1024)
    print(f"  ✓ File size: {size_mb:.2f} MB")
    print(f"\nSaved to: {csv_path}")

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show information about an ASC or JSON session file."""
    file_path = Path(args.data_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        session = load_session_data(file_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Session: {file_path.name}")
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

    print()
    print(f"Gaze samples: {len(session.gaze_samples):,}")
    if session.gaze_samples:
        samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
        print(
            f"  - With raw pupil/CR data: {samples_with_raw:,} ({samples_with_raw / len(session.gaze_samples) * 100:.1f}%)"
        )

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="syelink",
        description="Parse and visualize EyeLink eye tracker data",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert ASC file to JSON, text files, and/or CSV samples")
    convert_parser.add_argument("asc_file", help="Path to the ASC file")
    convert_parser.add_argument("-o", "--output", help="Output directory (default: same as ASC file)")
    convert_parser.add_argument("--json", action="store_true", help="Export JSON file only")
    convert_parser.add_argument("--text", action="store_true", help="Export text files only")
    convert_parser.add_argument("--samples", action="store_true", help="Export gaze samples CSV only")
    convert_parser.set_defaults(func=cmd_convert)

    # Export samples command
    export_parser = subparsers.add_parser("export-samples", help="Export gaze samples to CSV")
    export_parser.add_argument("data_file", help="Path to the ASC or JSON file")
    export_parser.add_argument("-o", "--output", help="Output CSV file path (default: <filename>_samples.csv)")
    export_parser.set_defaults(func=cmd_export_samples)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show session information")
    info_parser.add_argument("data_file", help="Path to the ASC or JSON file")
    info_parser.set_defaults(func=cmd_info)

    # Plot validation command
    plot_val_parser = subparsers.add_parser("plot-validation", help="Plot validation data")
    plot_val_parser.add_argument("data_file", help="Path to the ASC or JSON file")
    plot_val_parser.add_argument("-i", "--index", type=int, default=0, help="Validation index (default: 0)")
    plot_val_parser.add_argument("-o", "--output", help="Output image path")
    plot_val_parser.add_argument("--target-image", help="Path to custom target image")
    plot_val_parser.add_argument("--show", action="store_true", help="Show plot interactively")
    plot_val_parser.set_defaults(func=cmd_plot_validation)

    # Plot calibration command
    plot_cal_parser = subparsers.add_parser("plot-calibration", help="Plot calibration data")
    plot_cal_parser.add_argument("data_file", help="Path to the ASC or JSON file")
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
