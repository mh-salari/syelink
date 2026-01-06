"""syelink - Parse and analyze EyeLink eye tracker data.

This package provides tools for parsing EyeLink ASC files and extracting
calibration, validation, and session data into structured Python objects.

Example usage:
    >>> from syelink import parse_asc_file, SessionData
    >>> session = parse_asc_file("recording.asc")
    >>> print(f"Found {len(session.calibrations)} calibrations")
    >>> session.save_json("output.json")

    >>> # Or load from existing JSON
    >>> session = SessionData.load_json("output.json")

For plotting:
    >>> from syelink.plotting import plot_validation, plot_calibration_raw
    >>> fig = plot_validation(session, validation_index=0)
"""

from syelink.extract import parse_asc_file, parse_gaze_samples
from syelink.models import (
    CalibrationData,
    CalibrationGains,
    CalibrationPoint,
    CalibrationTargets,
    CornerCorrection,
    DisplayCoords,
    EyeCalibration,
    GazeSample,
    PolynomialCoefficients,
    RawPupilData,
    SessionData,
    ValidationData,
    ValidationPoint,
    ValidationSummary,
)

__version__ = "0.1.0"

__all__ = [
    "CalibrationData",
    "CalibrationGains",
    "CalibrationPoint",
    "CalibrationTargets",
    "CornerCorrection",
    "DisplayCoords",
    "EyeCalibration",
    "GazeSample",
    "PolynomialCoefficients",
    "RawPupilData",
    "SessionData",
    "ValidationData",
    "ValidationPoint",
    "ValidationSummary",
    "parse_asc_file",
    "parse_gaze_samples",
]
