"""Plotting example for syelink.

This script demonstrates how to create visualizations of:
1. Validation data with gaze offsets
2. Calibration RAW coordinates

Usage:
    python plot_example.py <path_to_json_file>
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

from syelink import SessionData
from syelink.plotting import plot_calibration_raw, plot_validation


def main() -> None:
    """Run the plotting example."""
    # Get JSON file path from command-line argument
    if len(sys.argv) < 2:
        print("Usage: python plot_example.py <path_to_json_file>")
        print("\nExample:")
        print("  python plot_example.py data/both_eyes/both_eyes.json")
        sys.exit(1)

    json_file = Path(sys.argv[1])
    if not json_file.exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)

    if json_file.suffix != ".json":
        print(f"Error: Expected .json file, got: {json_file.suffix}")
        sys.exit(1)

    data_dir = json_file.parent

    # Load session data
    print("Loading session data...")
    session = SessionData.load_json(str(json_file))

    print(f"Found {len(session.calibrations)} calibrations")
    print(f"Found {len(session.validations)} validations")

    # Plot a validation
    validation_index = 5
    print(f"\nPlotting validation #{validation_index}...")
    plot_validation(
        session,
        validation_index=validation_index,
        save_path=data_dir / "validation_example.png",
    )
    print(f"Saved to: {data_dir / 'validation_example.png'}")

    # Plot a calibration
    calibration_index = 1
    print(f"\nPlotting calibration #{calibration_index}...")
    plot_calibration_raw(
        session,
        cal_index=calibration_index,
        save_path=data_dir / "calibration_example.png",
    )
    print(f"Saved to: {data_dir / 'calibration_example.png'}")

    # Show plots interactively
    plt.show()


if __name__ == "__main__":
    main()
