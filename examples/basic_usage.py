"""Basic usage example for syelink.

This script demonstrates how to:
1. Parse an ASC file into structured data
2. Save the parsed data as JSON
3. Load the JSON back into Python objects
4. Access calibration and validation data

Usage:
    python basic_usage.py <path_to_asc_file>
"""

import sys
from pathlib import Path

from syelink import SessionData, parse_asc_file


def main() -> None:
    # Get ASC file path from command-line argument
    if len(sys.argv) < 2:
        print("Usage: python basic_usage.py <path_to_asc_file>")
        print("\nExample:")
        print("  python basic_usage.py data/both_eyes/both_eyes.asc")
        sys.exit(1)

    asc_file = Path(sys.argv[1])
    if not asc_file.exists():
        print(f"Error: File not found: {asc_file}")
        sys.exit(1)

    if asc_file.suffix != ".asc":
        print(f"Error: Expected .asc file, got: {asc_file.suffix}")
        sys.exit(1)

    data_dir = asc_file.parent

    # Option 1: Parse from ASC file
    print("=" * 60)
    print("Parsing ASC file...")
    print("=" * 60)

    session = parse_asc_file(asc_file)

    print(f"Display: {session.display_coords.width}x{session.display_coords.height}")
    print(f"Calibrations: {len(session.calibrations)}")
    print(f"Validations: {len(session.validations)}")
    if session.gaze_samples:
        samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
        print(f"Gaze samples: {len(session.gaze_samples):,} ({samples_with_raw:,} with raw pupil/CR data)")

    # Save to JSON
    output_json = data_dir / "parsed_output.json"
    session.save_json(str(output_json))
    print(f"\nSaved to: {output_json}")

    # Save metadata
    metadata_file = data_dir / "metadata.txt"
    session.save_metadata(metadata_file)
    print(f"Saved metadata to: {metadata_file}")

    # Save recordings to text file
    print("Saving recordings to text file...")
    rec_file = session.save_recordings_text(data_dir)
    print(f"  - {rec_file.name}")

    # Save calibrations to text file
    print("Saving calibrations to text file...")
    cal_file = session.save_calibrations_text(data_dir)
    print(f"  - {cal_file.name}")

    # Save validations to text file
    print("Saving validations to text file...")
    val_file = session.save_validations_text(data_dir)
    print(f"  - {val_file.name}")

    # Save gaze samples to CSV
    if session.gaze_samples:
        print("Saving gaze samples to CSV...")
        csv_file = session.save_samples_csv(data_dir / "gaze_samples.csv")
        samples_with_raw = sum(1 for s in session.gaze_samples if s.left_raw or s.right_raw)
        print(f"  - {csv_file.name} ({len(session.gaze_samples):,} samples, {samples_with_raw:,} with raw data)")
    else:
        print("No gaze samples found in this file")

    # Option 2: Load from JSON
    print("\n" + "=" * 60)
    print("Loading from JSON...")
    print("=" * 60)

    # Load the JSON file we just created
    session = SessionData.load_json(str(output_json))

    # Access recording data
    print(f"\nRecordings: {len(session.recordings)}")
    for i, rec in enumerate(session.recordings):
        duration = (rec.end_time - rec.start_time) if rec.end_time else 0
        print(f"  [{i}] Start: {rec.start_time}, End: {rec.end_time}, Duration: {duration}ms")

    # Access calibration data
    print("\nCalibrations:")
    for i, cal in enumerate(session.calibrations):
        left = cal.left_eye
        right = cal.right_eye
        print(f"  [{i}] Type: {cal.calibration_type}, Timestamp: {cal.timestamp}ms")
        if left:
            print(f"       LEFT eye: {left.result}")
        if right:
            print(f"       RIGHT eye: {right.result}")

    # Access validation data
    print("\nValidations:")
    for i, val in enumerate(session.validations):
        print(f"  [{i}] Type: {val.validation_type}, Timestamp: {val.timestamp}ms")
        if val.summary_left:
            print(
                f"       LEFT eye:  avg={val.summary_left.error_avg_deg:.2f}°, max={val.summary_left.error_max_deg:.2f}°"
            )
        if val.summary_right:
            print(
                f"       RIGHT eye: avg={val.summary_right.error_avg_deg:.2f}°, max={val.summary_right.error_max_deg:.2f}°"
            )

    # Access individual calibration points
    print("\n" + "=" * 60)
    print("Calibration point details (first calibration, left eye):")
    print("=" * 60)

    cal = session.calibrations[0]
    if cal.left_eye:
        for point in cal.left_eye.points[:3]:  # First 3 points
            print(
                f"  Point {point.point_number}: RAW=({point.raw_x:.1f}, {point.raw_y:.1f}) -> HREF=({point.href_x:.0f}, {point.href_y:.0f})"
            )


if __name__ == "__main__":
    main()
