"""Basic usage example for syelink.

This script demonstrates how to:
1. Parse an ASC file into structured data
2. Save the parsed data as JSON
3. Load the JSON back into Python objects
4. Access calibration and validation data
"""

from pathlib import Path

from syelink import SessionData, parse_asc_file

# Path to example data
DATA_DIR = Path(__file__).parent / "data" / "631both"
ASC_FILE = DATA_DIR / "631both.asc"
JSON_FILE = DATA_DIR / "631both.json"


def main() -> None:
    """Run the example."""
    # Option 1: Parse from ASC file
    print("=" * 60)
    print("Parsing ASC file...")
    print("=" * 60)

    session = parse_asc_file(ASC_FILE)

    print(f"Display: {session.display_coords.width}x{session.display_coords.height}")
    print(f"Calibrations: {len(session.calibrations)}")
    print(f"Validations: {len(session.validations)}")

    # Save to JSON
    output_json = DATA_DIR / "parsed_output.json"
    session.save_json(str(output_json))
    print(f"\nSaved to: {output_json}")

    # Save metadata
    metadata_file = DATA_DIR / "metadata.txt"
    session.save_metadata(metadata_file)
    print(f"Saved metadata to: {metadata_file}")

    # Save recordings to text file
    print("Saving recordings to text file...")
    rec_file = session.save_recordings_text(DATA_DIR)
    print(f"  - {rec_file.name}")

    # Save calibrations to text file
    print("Saving calibrations to text file...")
    cal_file = session.save_calibrations_text(DATA_DIR)
    print(f"  - {cal_file.name}")

    # Save validations to text file
    print("Saving validations to text file...")
    val_file = session.save_validations_text(DATA_DIR)
    print(f"  - {val_file.name}")

    # Option 2: Load from existing JSON
    print("\n" + "=" * 60)
    print("Loading from JSON...")
    print("=" * 60)

    # Use the file we just created if the original doesn't exist
    json_file_to_load = JSON_FILE if JSON_FILE.exists() else output_json
    session = SessionData.load_json(str(json_file_to_load))

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
