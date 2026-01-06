"""Data structure definitions for EyeLink calibration and validation data.

These structures define what fields will be extracted from the raw ASC text.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from typing import Any


@dataclass
class DisplayCoords:
    """Display/screen coordinates from the EyeLink ASC file.

    Parsed from: MSG <timestamp> DISPLAY_COORDS <left> <top> <right> <bottom>
    Example: MSG 228029 DISPLAY_COORDS 0 0 1279 1023

    The values are 0-indexed, so width = right - left + 1, height = bottom - top + 1.
    """

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        """Screen width in pixels."""
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        """Screen height in pixels."""
        return self.bottom - self.top + 1

    @property
    def center_x(self) -> float:
        """Screen center X coordinate."""
        return (self.left + self.right) / 2

    @property
    def center_y(self) -> float:
        """Screen center Y coordinate."""
        return (self.top + self.bottom) / 2

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisplayCoords:
        """Create DisplayCoords from a dictionary."""
        return cls(
            left=data["left"],
            top=data["top"],
            right=data["right"],
            bottom=data["bottom"],
        )


# CALIBRATION DATA STRUCTURE
@dataclass
class CalibrationPoint:
    """Single calibration point with RAW and HREF coordinates.

    RAW coordinates: Pupil/camera coordinates from the eye tracker sensor (small values, ~-60 to 0 range).
    HREF coordinates: Head-Referenced Eye Angle in angular units (~260+ units per visual degree).
                      Range approximately -2600 to +2600 for X, -2000 to +2000 for Y.

    Format in ASC file: MSG <timestamp> !CAL <raw_x>, <raw_y>  <href_x>, <href_y>
    Example: MSG 270129 !CAL -55.7, -114.5  -2521, 2003
    """

    point_number: int  # 1-9 for calibration points, 10 is origin (0,0)
    raw_x: float  # RAW camera x coordinate (small values, ~-60 to 0 range)
    raw_y: float  # RAW camera y coordinate (small values, ~-150 to -90 range)
    href_x: float  # HREF head-referenced x (angular, ~260 units/deg, ~-2600 to +2600)
    href_y: float  # HREF head-referenced y (angular, ~260 units/deg, ~-2000 to +2000)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationPoint:
        """Create CalibrationPoint from a dictionary."""
        return cls(**data)


@dataclass
class PolynomialCoefficients:
    """5th-order polynomial coefficients for coordinate mapping.

    Formula from EyeLink ASC file: X=a+bx+cy+dxx+eyy, Y=f+gx+hy+ixx+jyy
    (Note: "goaly" in the raw file is a typo for "hy")

    The input x,y must be PRENORMALIZED RAW coordinates:
        x = raw_x - prenorm_x
        y = raw_y - prenorm_y

    Output is in HREF (head-referenced angular) coordinates.
    """

    const: float  # a or f - constant term
    x: float  # b or g - linear x coefficient
    y: float  # c or h - linear y coefficient
    xx: float  # d or i - quadratic x² coefficient
    yy: float  # e or j - quadratic y² coefficient

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolynomialCoefficients:
        """Create PolynomialCoefficients from a dictionary."""
        return cls(**data)

    def apply(self, raw_x: float, raw_y: float) -> float:
        """Apply coefficients to prenormalized RAW coordinates to get HREF coordinate.

        Formula: val = const + x*rx + y*ry + xx*rx*rx + yy*ry*ry
        """
        return self.const + self.x * raw_x + self.y * raw_y + self.xx * raw_x * raw_x + self.yy * raw_y * raw_y


@dataclass
class CalibrationGains:
    """Calibration gain values for each axis.

    These represent the sensitivity/gain of the eye tracker in different
    screen regions. Large values (>1000) often indicate calibration issues.

    cx, lx, rx: center, left, right x gains
    cy, ty, by: center, top, bottom y gains
    """

    cx: float  # Center x gain
    lx: float  # Left x gain
    rx: float  # Right x gain
    cy: float  # Center y gain
    ty: float  # Top y gain
    by: float  # Bottom y gain

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationGains:
        """Create CalibrationGains from a dictionary."""
        return cls(**data)


@dataclass
class CornerCorrection:
    """Corner correction coefficients for the 4 screen quadrants.

    The polynomial mapping (HREF -> screen coords) has residual errors at the
    screen corners. These coefficients provide a secondary correction:

        final_x = poly_x + corner_x[quadrant] * poly_x * poly_y
        final_y = poly_y + corner_y[quadrant] * poly_x * poly_y

    Where poly_x, poly_y are the polynomial outputs before corner correction.

    Quadrant indices (based on polynomial output signs):
        0 = top-left     (screen_x < 0, screen_y < 0)
        1 = top-right    (screen_x > 0, screen_y < 0)
        2 = bottom-left  (screen_x < 0, screen_y > 0)
        3 = bottom-right (screen_x > 0, screen_y > 0)

    Note: screen_y < 0 = top of screen in EyeLink's internal coordinate system.
    """

    # 4 pairs of (x, y) coefficients, one per quadrant
    q0_x: float  # Top-left x coefficient
    q0_y: float  # Top-left y coefficient
    q1_x: float  # Top-right x coefficient
    q1_y: float  # Top-right y coefficient
    q2_x: float  # Bottom-left x coefficient
    q2_y: float  # Bottom-left y coefficient
    q3_x: float  # Bottom-right x coefficient
    q3_y: float  # Bottom-right y coefficient

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CornerCorrection:
        """Create CornerCorrection from a dictionary."""
        return cls(**data)

    @staticmethod
    def get_quadrant(screen_x: float, screen_y: float) -> int:
        """Determine which quadrant a point is in based on polynomial output."""
        if screen_x < 0:
            return 0 if screen_y < 0 else 2
        return 1 if screen_y < 0 else 3

    def apply(self, poly_x: float, poly_y: float) -> tuple[float, float]:
        """Apply corner correction to polynomial output.

        Args:
            poly_x: X coordinate from polynomial (before correction)
            poly_y: Y coordinate from polynomial (before correction)

        Returns:
            (corrected_x, corrected_y) after applying corner correction

        """
        quadrant = self.get_quadrant(poly_x, poly_y)
        product = poly_x * poly_y

        coeffs = [
            (self.q0_x, self.q0_y),
            (self.q1_x, self.q1_y),
            (self.q2_x, self.q2_y),
            (self.q3_x, self.q3_y),
        ]
        cx, cy = coeffs[quadrant]

        corrected_x = poly_x + cx * product
        corrected_y = poly_y + cy * product

        return corrected_x, corrected_y


@dataclass
class EyeCalibration:
    """Calibration data for a single eye (LEFT or RIGHT).

    The calibration process maps RAW camera coordinates to HREF angular coordinates.
    The polynomial coefficients (polynomial_x, polynomial_y) with prenormalization
    offsets (prenorm_x, prenorm_y) define this mapping.

    Usage:
        1. Normalize: x = raw_x - prenorm_x, y = raw_y - prenorm_y
        2. Apply polynomial_x to get href_x (angular units)
        3. Apply polynomial_y to get href_y (angular units)
    """

    eye: Literal["LEFT", "RIGHT"]
    result: Literal["GOOD", "POOR", "FAILED", "FAIR"]
    points: list[CalibrationPoint]  # 9 calibration points + 1 origin point (total 10)
    polynomial_x: PolynomialCoefficients | None = None  # X-axis polynomial (a,b,c,d,e)
    polynomial_y: PolynomialCoefficients | None = None  # Y-axis polynomial (f,g,h,i,j)
    gains: CalibrationGains | None = None
    corner_correction: CornerCorrection | None = None  # Secondary corner correction
    prenorm_x: float = 0.0  # Subtract from raw_x before polynomial
    prenorm_y: float = 0.0  # Subtract from raw_y before polynomial

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EyeCalibration:
        """Create EyeCalibration from a dictionary."""
        points = [CalibrationPoint.from_dict(p) for p in data["points"]]
        poly_x = PolynomialCoefficients.from_dict(data["polynomial_x"]) if data.get("polynomial_x") else None
        poly_y = PolynomialCoefficients.from_dict(data["polynomial_y"]) if data.get("polynomial_y") else None
        gains = CalibrationGains.from_dict(data["gains"]) if data.get("gains") else None
        corner_corr = CornerCorrection.from_dict(data["corner_correction"]) if data.get("corner_correction") else None

        return cls(
            eye=data["eye"],
            result=data["result"],
            points=points,
            polynomial_x=poly_x,
            polynomial_y=poly_y,
            gains=gains,
            corner_correction=corner_corr,
            prenorm_x=data.get("prenorm_x", 0.0),
            prenorm_y=data.get("prenorm_y", 0.0),
        )

    def raw_to_href(
        self,
        raw_x: float,
        raw_y: float,
        apply_corner_correction: bool = True,
    ) -> tuple[float, float]:
        """Convert RAW camera coordinates to HREF coordinates using this calibration.

        The full pipeline:
            1. Prenormalize: x = raw_x - prenorm_x, y = raw_y - prenorm_y
            2. Apply polynomial: href_x, href_y = polynomial(x, y)
            3. Apply corner correction (if available and enabled):
               final = poly + corner_coeff[quadrant] * poly_x * poly_y

        Args:
            raw_x: RAW camera x coordinate
            raw_y: RAW camera y coordinate
            apply_corner_correction: Whether to apply corner correction (default True)

        Returns:
            (href_x, href_y) in head-referenced angular coordinates

        """
        if not self.polynomial_x or not self.polynomial_y:
            msg = "Calibration coefficients missing"
            raise ValueError(msg)

        # Step 1: Apply prenormalization
        x_norm = raw_x - self.prenorm_x
        y_norm = raw_y - self.prenorm_y

        # Step 2: Apply polynomial
        href_x = self.polynomial_x.apply(x_norm, y_norm)
        href_y = self.polynomial_y.apply(x_norm, y_norm)

        # Step 3: Apply corner correction if available
        if apply_corner_correction and self.corner_correction:
            href_x, href_y = self.corner_correction.apply(href_x, href_y)

        return href_x, href_y


# CALIBRATION/VALIDATION TARGETS
@dataclass
class CalibrationTargets:
    """Calibration/validation target positions.

    Stores the actual screen positions where calibration or validation targets were displayed.
    For validations, parsed from the "at X,Y" part of VALIDATE messages.
    For calibrations, can be extracted from validation data of the same session.

    Calibration types:
    - H3: horizontal 3-point calibration
    - HV3: 3-point calibration
    - HV5: 5-point calibration
    - HV9: 9-point grid calibration (most common)
    - HV13: 13-point calibration
    """

    calibration_type: str  # H3, HV3, HV5, HV9, HV13
    targets: list[tuple[float, float]]  # [(x1,y1), (x2,y2), ...] in pixels

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationTargets:
        """Create CalibrationTargets from a dictionary."""
        return cls(
            calibration_type=data["calibration_type"],
            targets=[tuple(t) for t in data["targets"]],
        )


@dataclass
class CalibrationData:
    """Complete calibration segment data."""

    timestamp: int  # Milliseconds
    calibration_type: str  # e.g., "HV9"
    tracking_mode: str  # e.g., "P-CR"
    targets: CalibrationTargets | None = None  # Target positions
    left_eye: EyeCalibration | None = None
    right_eye: EyeCalibration | None = None
    content: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationData:
        """Create CalibrationData from a dictionary."""
        left = EyeCalibration.from_dict(data["left_eye"]) if data.get("left_eye") else None
        right = EyeCalibration.from_dict(data["right_eye"]) if data.get("right_eye") else None
        targets = CalibrationTargets.from_dict(data["targets"]) if data.get("targets") else None

        return cls(
            timestamp=data["timestamp"],
            calibration_type=data["calibration_type"],
            tracking_mode=data["tracking_mode"],
            targets=targets,
            left_eye=left,
            right_eye=right,
            content=data.get("content"),
        )


# VALIDATION DATA STRUCTURE
@dataclass
class ValidationSummary:
    """Validation summary metrics for one eye."""

    eye: Literal["LEFT", "RIGHT"]
    result: Literal["GOOD", "POOR", "FAILED", "FAIR"]
    error_avg_deg: float  # Average error in degrees
    error_max_deg: float  # Maximum error in degrees
    offset_deg: float  # Offset in degrees
    offset_pix_x: float  # Offset in pixels (x)
    offset_pix_y: float  # Offset in pixels (y)
    ppd: float | None = None  # Pixels per degree (calculated)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationSummary:
        """Create ValidationSummary from a dictionary."""
        return cls(**data)


@dataclass
class ValidationPoint:
    """Validation offset data for a single point and eye.

    Does NOT store target positions (those are in CalibrationTargets).
    Stores only the offset/error data and calculated gaze position.

    The gaze position is where the participant actually looked:
    gaze_x = target_x + offset_pix_x
    gaze_y = target_y + offset_pix_y
    """

    point_number: int  # 0-8 (validation uses 0-based indexing)
    eye: Literal["LEFT", "RIGHT"]
    offset_deg: float  # Offset error in degrees
    offset_pix_x: float  # Offset error in pixels (x)
    offset_pix_y: float  # Offset error in pixels (y)
    gaze_x: float  # Actual gaze x = target_x + offset_pix_x
    gaze_y: float  # Actual gaze y = target_y + offset_pix_y

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationPoint:
        """Create ValidationPoint from a dictionary."""
        return cls(**data)


@dataclass
class ValidationData:
    """Complete validation segment data."""

    timestamp: int  # Milliseconds
    validation_type: str  # e.g., "HV9"
    tracking_mode: str  # e.g., "LR" (left-right binocular)
    targets: CalibrationTargets | None = None  # Target positions
    summary_left: ValidationSummary | None = None
    summary_right: ValidationSummary | None = None
    points: list[ValidationPoint] = field(default_factory=list)  # 18 points (9 points x 2 eyes)
    content: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationData:
        """Create ValidationData from a dictionary."""
        sum_left = ValidationSummary.from_dict(data["summary_left"]) if data.get("summary_left") else None
        sum_right = ValidationSummary.from_dict(data["summary_right"]) if data.get("summary_right") else None
        points = [ValidationPoint.from_dict(p) for p in data.get("points", [])]
        targets = CalibrationTargets.from_dict(data["targets"]) if data.get("targets") else None

        return cls(
            timestamp=data["timestamp"],
            validation_type=data["validation_type"],
            tracking_mode=data["tracking_mode"],
            targets=targets,
            summary_left=sum_left,
            summary_right=sum_right,
            points=points,
            content=data.get("content"),
        )


@dataclass
class RecordingData:
    """Recording segment metadata."""

    start_time: int
    end_time: int | None
    content: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordingData:
        """Create RecordingData from a dictionary."""
        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            content=data.get("content"),
        )


# GAZE SAMPLE AND RAW PUPIL/CR DATA


@dataclass
class RawPupilData:
    """Raw pupil and corneal reflection data from eye tracker camera.

    This data is only available when raw recording is enabled (record_raw_data=True in pyelink).
    Data is recorded as MSG lines with format:
    MSG <msg_ts> L <sample_ts> <px> <py> <pa> <width> <height> <crx> <cry> <crarea> <cr2x> <cr2y> <crarea2> R ...

    Values of -32768.0 or 4294934528.0 indicate missing/invalid data.
    """

    pupil_x: float | None  # Raw pupil X coordinate in camera sensor units
    pupil_y: float | None  # Raw pupil Y coordinate in camera sensor units
    pupil_area: float | None  # Pupil area
    pupil_width: float | None  # Pupil width in pixels
    pupil_height: float | None  # Pupil height in pixels
    cr_x: float | None  # Corneal reflection X coordinate
    cr_y: float | None  # Corneal reflection Y coordinate
    cr_area: float | None  # Corneal reflection area
    cr2_x: float | None = None  # Secondary CR X
    cr2_y: float | None = None  # Secondary CR Y
    cr2_area: float | None = None  # Secondary CR area

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RawPupilData:
        """Create RawPupilData from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GazeSample:
    """Single gaze sample with optional raw pupil/CR data.

    Gaze data is always present (from sample lines in ASC file).
    Raw pupil/CR data is only present in RECORD mode when raw recording was enabled.
    """

    timestamp: int  # Sample timestamp in milliseconds
    segment: int  # Segment number (1-based)
    mode: Literal["RECORD", "CALIBRATE", "VALIDATE", "OFFLINE"]  # Recording mode
    tracking_mode: str  # e.g., "CR", "P-CR", "LR"
    sample_rate: int  # Sampling rate in Hz (e.g., 1000)
    eyes_tracked: str  # "L", "R", or "LR"

    # Gaze data (always present)
    left_gaze_x: float | None
    left_gaze_y: float | None
    left_pupil: float | None
    right_gaze_x: float | None
    right_gaze_y: float | None
    right_pupil: float | None
    status: str  # Status flags (e.g., "...C.", ".C..R")

    # Raw pupil/CR data (only in RECORD mode with raw recording)
    left_raw: RawPupilData | None = None
    right_raw: RawPupilData | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GazeSample:
        """Create GazeSample from a dictionary."""
        # Handle nested RawPupilData
        left_raw = None
        right_raw = None
        if "left_raw" in data and data["left_raw"] is not None:
            left_raw = RawPupilData.from_dict(data["left_raw"])
        if "right_raw" in data and data["right_raw"] is not None:
            right_raw = RawPupilData.from_dict(data["right_raw"])

        return cls(
            timestamp=data["timestamp"],
            segment=data["segment"],
            mode=data["mode"],
            tracking_mode=data["tracking_mode"],
            sample_rate=data["sample_rate"],
            eyes_tracked=data["eyes_tracked"],
            left_gaze_x=data.get("left_gaze_x"),
            left_gaze_y=data.get("left_gaze_y"),
            left_pupil=data.get("left_pupil"),
            right_gaze_x=data.get("right_gaze_x"),
            right_gaze_y=data.get("right_gaze_y"),
            right_pupil=data.get("right_pupil"),
            status=data["status"],
            left_raw=left_raw,
            right_raw=right_raw,
        )


@dataclass
class SessionData:
    """Container for all session data."""

    calibrations: list[CalibrationData] = field(default_factory=list)
    validations: list[ValidationData] = field(default_factory=list)
    recordings: list[RecordingData] = field(default_factory=list)
    gaze_samples: list[GazeSample] = field(default_factory=list)
    display_coords: DisplayCoords | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the session data to a dictionary."""
        data = asdict(self)
        # Remove content from recordings, calibrations, and validations to avoid bloating JSON
        if "recordings" in data:
            for rec in data["recordings"]:
                rec.pop("content", None)
        if "calibrations" in data:
            for cal in data["calibrations"]:
                cal.pop("content", None)
        if "validations" in data:
            for val in data["validations"]:
                val.pop("content", None)
        return data

    def to_json(self, indent: int = 4) -> str:
        """Convert the session data to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self, filepath: str) -> None:
        """Save the session data to a JSON file."""
        with Path(filepath).open("w", encoding="utf-8") as f:
            f.write(self.to_json())

    def save_metadata(self, filepath: str | Path) -> None:
        """Save session metadata to a text file.

        Includes raw messages for calibrations and validations, and start/end for recordings.
        """
        with Path(filepath).open("w", encoding="utf-8") as f:
            # CALIBRATIONS
            f.write("-" * 80 + "\n")
            f.write("CALIBRATIONS\n")
            f.write("-" * 80 + "\n")
            for i, cal in enumerate(self.calibrations):
                f.write(f"[{i + 1}] Calibration @ {cal.timestamp}ms ({cal.calibration_type})\n")
                if cal.content:
                    found_msg = False
                    for line in cal.content.splitlines():
                        if "!CAL CALIBRATION" in line:
                            f.write(f"    {line.strip()}\n")
                            found_msg = True
                    if not found_msg:
                        f.write("    (No result message found)\n")
                # f.write("\n")

            # VALIDATIONS
            f.write("-" * 80 + "\n")
            f.write("VALIDATIONS\n")
            f.write("-" * 80 + "\n")
            for i, val in enumerate(self.validations):
                f.write(f"[{i + 1}] Validation @ {val.timestamp}ms ({val.validation_type})\n")
                if val.content:
                    found_msg = False
                    for line in val.content.splitlines():
                        if "!CAL VALIDATION" in line:
                            f.write(f"    {line.strip()}\n")
                            found_msg = True
                    if not found_msg:
                        f.write("    (No result message found)\n")
                # f.write("\n")

            # RECORDINGS
            f.write("-" * 80 + "\n")
            f.write("RECORDINGS\n")
            f.write("-" * 80 + "\n\n")
            for i, rec in enumerate(self.recordings):
                end = rec.end_time or "N/A"
                duration = (rec.end_time - rec.start_time) if rec.end_time else "N/A"
                f.write(f"[{i + 1}] Recording: {rec.start_time}ms - {end}ms (Duration: {duration}ms)\n")

    def save_recordings_text(self, output_dir: str | Path, filename_prefix: str = "") -> Path:
        """Save all recording blocks to a single text file with headers.

        Args:
            output_dir: Directory to save the text file in.
            filename_prefix: Optional prefix for the filename (e.g., "subject01").
                           If provided, output will be "{prefix}_recordings.txt".
                           If empty, output will be "recordings.txt".

        Returns:
            Path to the saved file.

        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename_prefix:
            filepath = output_dir / f"{filename_prefix}_recordings.txt"
        else:
            filepath = output_dir / "recordings.txt"

        with filepath.open("w", encoding="utf-8") as f:
            for i, rec in enumerate(self.recordings):
                if rec.content:
                    f.write("=" * 80 + "\n")
                    f.write(f"RECORDING #{i + 1} (Start: {rec.start_time}, End: {rec.end_time})\n")
                    f.write("=" * 80 + "\n")
                    f.write(rec.content)
                    f.write("\n\n")
        return filepath

    def save_calibrations_text(self, output_dir: str | Path, filename_prefix: str = "") -> Path:
        """Save all calibration blocks to a single text file with headers.

        Args:
            output_dir: Directory to save the text file in.
            filename_prefix: Optional prefix for the filename (e.g., "subject01").
                           If provided, output will be "{prefix}_calibrations.txt".
                           If empty, output will be "calibrations.txt".

        Returns:
            Path to the saved file.

        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename_prefix:
            filepath = output_dir / f"{filename_prefix}_calibrations.txt"
        else:
            filepath = output_dir / "calibrations.txt"

        with filepath.open("w", encoding="utf-8") as f:
            for i, cal in enumerate(self.calibrations):
                if cal.content:
                    f.write("=" * 80 + "\n")
                    f.write(f"CALIBRATION #{i + 1} (Timestamp: {cal.timestamp}, Type: {cal.calibration_type})\n")
                    f.write("=" * 80 + "\n")
                    f.write(cal.content)
                    f.write("\n\n")
        return filepath

    def save_validations_text(self, output_dir: str | Path, filename_prefix: str = "") -> Path:
        """Save all validation blocks to a single text file with headers.

        Args:
            output_dir: Directory to save the text file in.
            filename_prefix: Optional prefix for the filename (e.g., "subject01").
                           If provided, output will be "{prefix}_validations.txt".
                           If empty, output will be "validations.txt".

        Returns:
            Path to the saved file.

        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename_prefix:
            filepath = output_dir / f"{filename_prefix}_validations.txt"
        else:
            filepath = output_dir / "validations.txt"

        with filepath.open("w", encoding="utf-8") as f:
            for i, val in enumerate(self.validations):
                if val.content:
                    f.write("=" * 80 + "\n")
                    f.write(f"VALIDATION #{i + 1} (Timestamp: {val.timestamp}, Type: {val.validation_type})\n")
                    f.write("=" * 80 + "\n")
                    f.write(val.content)
                    f.write("\n\n")
        return filepath

    def save_samples_csv(self, filepath: str | Path) -> Path:
        """Save gaze samples to CSV file.

        CSV columns:
        - timestamp: Sample timestamp (ms)
        - segment: Segment number (1-based)
        - mode: Recording mode (RECORD/CALIBRATE/VALIDATE/OFFLINE)
        - tracking_mode: Tracking mode (e.g., CR, P-CR)
        - sample_rate: Sampling rate in Hz
        - eyes_tracked: Eyes tracked (L/R/LR)
        - left_gaze_x, left_gaze_y, left_pupil: Left eye gaze data
        - right_gaze_x, right_gaze_y, right_pupil: Right eye gaze data
        - status: Status flags
        - left_raw_*: Left eye raw pupil/CR data (11 columns, empty if not available)
        - right_raw_*: Right eye raw pupil/CR data (11 columns, empty if not available)

        Args:
            filepath: Path to save CSV file

        Returns:
            Path to the saved file

        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Define CSV column headers
        headers = [
            "timestamp",
            "segment",
            "mode",
            "tracking_mode",
            "sample_rate",
            "eyes_tracked",
            "left_gaze_x",
            "left_gaze_y",
            "left_pupil",
            "right_gaze_x",
            "right_gaze_y",
            "right_pupil",
            "status",
            "left_raw_px",
            "left_raw_py",
            "left_raw_pa",
            "left_raw_width",
            "left_raw_height",
            "left_raw_crx",
            "left_raw_cry",
            "left_raw_crarea",
            "left_raw_cr2x",
            "left_raw_cr2y",
            "left_raw_cr2area",
            "right_raw_px",
            "right_raw_py",
            "right_raw_pa",
            "right_raw_width",
            "right_raw_height",
            "right_raw_crx",
            "right_raw_cry",
            "right_raw_crarea",
            "right_raw_cr2x",
            "right_raw_cr2y",
            "right_raw_cr2area",
        ]

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for sample in self.gaze_samples:
                row = {
                    "timestamp": sample.timestamp,
                    "segment": sample.segment,
                    "mode": sample.mode,
                    "tracking_mode": sample.tracking_mode,
                    "sample_rate": sample.sample_rate,
                    "eyes_tracked": sample.eyes_tracked,
                    "left_gaze_x": sample.left_gaze_x if sample.left_gaze_x is not None else "",
                    "left_gaze_y": sample.left_gaze_y if sample.left_gaze_y is not None else "",
                    "left_pupil": sample.left_pupil if sample.left_pupil is not None else "",
                    "right_gaze_x": sample.right_gaze_x if sample.right_gaze_x is not None else "",
                    "right_gaze_y": sample.right_gaze_y if sample.right_gaze_y is not None else "",
                    "right_pupil": sample.right_pupil if sample.right_pupil is not None else "",
                    "status": sample.status,
                }

                # Add left raw data (empty if not available)
                if sample.left_raw:
                    row.update({
                        "left_raw_px": sample.left_raw.pupil_x if sample.left_raw.pupil_x is not None else "",
                        "left_raw_py": sample.left_raw.pupil_y if sample.left_raw.pupil_y is not None else "",
                        "left_raw_pa": sample.left_raw.pupil_area if sample.left_raw.pupil_area is not None else "",
                        "left_raw_width": sample.left_raw.pupil_width
                        if sample.left_raw.pupil_width is not None
                        else "",
                        "left_raw_height": sample.left_raw.pupil_height
                        if sample.left_raw.pupil_height is not None
                        else "",
                        "left_raw_crx": sample.left_raw.cr_x if sample.left_raw.cr_x is not None else "",
                        "left_raw_cry": sample.left_raw.cr_y if sample.left_raw.cr_y is not None else "",
                        "left_raw_crarea": sample.left_raw.cr_area if sample.left_raw.cr_area is not None else "",
                        "left_raw_cr2x": sample.left_raw.cr2_x if sample.left_raw.cr2_x is not None else "",
                        "left_raw_cr2y": sample.left_raw.cr2_y if sample.left_raw.cr2_y is not None else "",
                        "left_raw_cr2area": sample.left_raw.cr2_area if sample.left_raw.cr2_area is not None else "",
                    })
                else:
                    row.update({key: "" for key in headers if key.startswith("left_raw_")})

                # Add right raw data (empty if not available)
                if sample.right_raw:
                    row.update({
                        "right_raw_px": sample.right_raw.pupil_x if sample.right_raw.pupil_x is not None else "",
                        "right_raw_py": sample.right_raw.pupil_y if sample.right_raw.pupil_y is not None else "",
                        "right_raw_pa": sample.right_raw.pupil_area if sample.right_raw.pupil_area is not None else "",
                        "right_raw_width": sample.right_raw.pupil_width
                        if sample.right_raw.pupil_width is not None
                        else "",
                        "right_raw_height": sample.right_raw.pupil_height
                        if sample.right_raw.pupil_height is not None
                        else "",
                        "right_raw_crx": sample.right_raw.cr_x if sample.right_raw.cr_x is not None else "",
                        "right_raw_cry": sample.right_raw.cr_y if sample.right_raw.cr_y is not None else "",
                        "right_raw_crarea": sample.right_raw.cr_area if sample.right_raw.cr_area is not None else "",
                        "right_raw_cr2x": sample.right_raw.cr2_x if sample.right_raw.cr2_x is not None else "",
                        "right_raw_cr2y": sample.right_raw.cr2_y if sample.right_raw.cr2_y is not None else "",
                        "right_raw_cr2area": sample.right_raw.cr2_area
                        if sample.right_raw.cr2_area is not None
                        else "",
                    })
                else:
                    row.update({key: "" for key in headers if key.startswith("right_raw_")})

                writer.writerow(row)

        return filepath

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionData:
        """Create a SessionData object from a dictionary."""
        calibrations = [CalibrationData.from_dict(c) for c in data.get("calibrations", [])]
        validations = [ValidationData.from_dict(v) for v in data.get("validations", [])]
        recordings = [RecordingData.from_dict(r) for r in data.get("recordings", [])]
        display_coords = DisplayCoords.from_dict(data["display_coords"]) if data.get("display_coords") else None
        return cls(
            calibrations=calibrations,
            validations=validations,
            recordings=recordings,
            display_coords=display_coords,
        )

    @classmethod
    def load_json(cls, filepath: str) -> SessionData:
        """Load session data from a JSON file."""
        with Path(filepath).open(encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
