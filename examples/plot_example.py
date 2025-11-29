"""Plotting example for syelink.

This script demonstrates how to create visualizations of:
1. Validation data with gaze offsets
2. Calibration RAW coordinates
"""

from pathlib import Path

import matplotlib.pyplot as plt

from syelink import SessionData
from syelink.plotting import plot_calibration_raw, plot_validation

# Path to example data
DATA_DIR = Path(__file__).parent / "data" / "631both"
JSON_FILE = DATA_DIR / "parsed_output.json"


def main() -> None:
    """Run the plotting example."""
    # Load session data
    print("Loading session data...")
    session = SessionData.load_json(str(JSON_FILE))

    print(f"Found {len(session.calibrations)} calibrations")
    print(f"Found {len(session.validations)} validations")

    # Plot a validation
    print("\nPlotting validation #5...")
    plot_validation(
        session,
        validation_index=5,
        save_path=DATA_DIR / "validation_example.png",
    )
    print(f"Saved to: {DATA_DIR / 'validation_example.png'}")

    # Plot a calibration
    print("\nPlotting calibration #6...")
    plot_calibration_raw(
        session,
        cal_index=6,
        save_path=DATA_DIR / "calibration_example.png",
    )
    print(f"Saved to: {DATA_DIR / 'calibration_example.png'}")

    # Show plots interactively
    plt.show()


if __name__ == "__main__":
    main()
