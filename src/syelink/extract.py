"""Parse EyeLink ASC data into structured Python objects (dataclasses).

Provides functions to extract calibration, validation, and display data from ASC files.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import TYPE_CHECKING

from syelink.models import (
    CalibrationData,
    CalibrationGains,
    CalibrationPoint,
    CalibrationTargets,
    CornerCorrection,
    DisplayCoords,
    EyeCalibration,
    PolynomialCoefficients,
    RecordingData,
    SessionData,
    ValidationData,
    ValidationPoint,
    ValidationSummary,
)
from syelink.parser import find_all_segments

if TYPE_CHECKING:
    from typing import Any


def parse_calibration_points(text: str) -> list[CalibrationPoint]:
    """Parse calibration points from text block."""
    points = []
    # MSG	270129 !CAL -55.7, -114.5  -2521, 2003
    # Pattern: !CAL <raw_x>, <raw_y>  <href_x>, <href_y>
    pattern = r"!CAL\s+([-\d.]+),\s+([-\d.]+)\s+([-\d.]+),\s+([-\d.]+)"

    matches = re.findall(pattern, text)
    for i, match in enumerate(matches):
        points.append(
            CalibrationPoint(
                point_number=i + 1,
                raw_x=float(match[0]),
                raw_y=float(match[1]),
                href_x=float(match[2]),
                href_y=float(match[3]),
            )
        )
    return points


def parse_coefficients(text: str) -> tuple[PolynomialCoefficients | None, PolynomialCoefficients | None]:
    """Parse calibration coefficients for X and Y."""
    # MSG	270129 !CAL Cal coeff:(X=a+bx+cy+dxx+eyy,Y=f+gx+goaly+ixx+jyy)
    #      -0  119.98  3.7625 -0.0051343 -0.47168
    #    116.47  1.1614  152.45 -1.1095 -2.6127

    # Find the line with "Cal coeff" and the following two lines
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "!CAL Cal coeff" in line and i + 2 < len(lines):
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()

            # Extract numbers
            nums1 = [float(x) for x in line1.split()]
            nums2 = [float(x) for x in line2.split()]

            poly_x = None
            poly_y = None

            if len(nums1) >= 5:
                poly_x = PolynomialCoefficients(const=nums1[0], x=nums1[1], y=nums1[2], xx=nums1[3], yy=nums1[4])

            if len(nums2) >= 5:
                poly_y = PolynomialCoefficients(const=nums2[0], x=nums2[1], y=nums2[2], xx=nums2[3], yy=nums2[4])

            return poly_x, poly_y
    return None, None


def parse_gains(text: str) -> CalibrationGains | None:
    """Parse calibration gains."""
    # MSG	270129 !CAL Gains: cx:189.343 lx:204.884 rx:212.186
    # MSG	270129 !CAL Gains: cy:985.598 ty:71.873 by:951.361

    cx_match = re.search(r"Gains:.*cx:([-\d.]+)", text)
    lx_match = re.search(r"Gains:.*lx:([-\d.]+)", text)
    rx_match = re.search(r"Gains:.*rx:([-\d.]+)", text)

    cy_match = re.search(r"Gains:.*cy:([-\d.]+)", text)
    ty_match = re.search(r"Gains:.*ty:([-\d.]+)", text)
    by_match = re.search(r"Gains:.*by:([-\d.]+)", text)

    if all([cx_match, lx_match, rx_match, cy_match, ty_match, by_match]):
        return CalibrationGains(
            cx=float(cx_match.group(1)),
            lx=float(lx_match.group(1)),
            rx=float(rx_match.group(1)),
            cy=float(cy_match.group(1)),
            ty=float(ty_match.group(1)),
            by=float(by_match.group(1)),
        )
    return None


def parse_prenormalize(text: str) -> tuple[float, float]:
    """Parse prenormalize offsets."""
    # MSG	270129 !CAL Prenormalize: offx, offy = -36.206 -114.3
    match = re.search(r"!CAL Prenormalize: offx, offy =\s+([-\d.e]+)\s+([-\d.e]+)", text)
    if match:
        return float(match.group(1)), float(match.group(2))
    return 0.0, 0.0


def parse_corner_correction(text: str) -> CornerCorrection | None:
    """Parse corner correction coefficients.

    Format in ASC file:
        MSG	270129 !CAL Corner correction:
          -1.3496e-05, -1.6691e-05
          -4.8914e-05, -3.957e-05
          -1.7359e-06, -5.3909e-05
          -1.947e-05,  0.00017288

    4 lines of (x, y) pairs for quadrants:
        0 = top-left, 1 = top-right, 2 = bottom-left, 3 = bottom-right
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "!CAL Corner correction:" not in line or i + 4 >= len(lines):
            continue

        coeffs = []
        for j in range(1, 5):
            coeff_line = lines[i + j].strip()
            # Parse "  -1.3496e-05, -1.6691e-05" format
            # Remove any leading/trailing whitespace and split by comma
            parts = coeff_line.replace(",", " ").split()
            if len(parts) < 2:
                continue
            try:
                coeffs.append((float(parts[0]), float(parts[1])))
            except ValueError:
                return None

        if len(coeffs) == 4:
            return CornerCorrection(
                q0_x=coeffs[0][0],
                q0_y=coeffs[0][1],
                q1_x=coeffs[1][0],
                q1_y=coeffs[1][1],
                q2_x=coeffs[2][0],
                q2_y=coeffs[2][1],
                q3_x=coeffs[3][0],
                q3_y=coeffs[3][1],
            )
    return None


def _parse_eye_calibration(
    text: str, eye: str, full_text: str | None = None
) -> tuple[EyeCalibration | None, str, str]:
    """Parse calibration data for a specific eye.

    Args:
        text: The text block containing calibration data for this eye.
        eye: "LEFT" or "RIGHT".
        full_text: Optional full text of the calibration block to search for result if not found in `text`.

    Returns:
        Tuple of (EyeCalibration object or None, calibration_type, tracking_mode).

    """
    # Result
    # !CAL CALIBRATION HV9 P-CR LEFT  GOOD
    search_text = full_text or text
    res_match = re.search(rf"!CAL CALIBRATION ([A-Z0-9]+) ([\w-]+) {eye}\s+(GOOD|POOR|FAILED|FAIR)", search_text)

    cal_type = "HV9"
    track_mode = "P-CR"
    result = "UNKNOWN"

    if res_match:
        cal_type = res_match.group(1)
        track_mode = res_match.group(2)
        result = res_match.group(3)

    # If we didn't find the result line but have text, we might still try to parse coefficients
    # But usually the result line is present if the eye was calibrated.
    # If the text is empty or doesn't contain calibration data for this eye, we return None.

    # Check if we have coefficients
    poly_x, poly_y = parse_coefficients(text)
    if not poly_x and not poly_y and result == "UNKNOWN":
        return None, cal_type, track_mode

    prenorm_x, prenorm_y = parse_prenormalize(text)
    corner_corr = parse_corner_correction(text)
    gains = parse_gains(text)
    points = parse_calibration_points(text)

    eye_cal = EyeCalibration(
        eye=eye,
        result=result,
        points=points,
        polynomial_x=poly_x,
        polynomial_y=poly_y,
        gains=gains,
        corner_correction=corner_corr,
        prenorm_x=prenorm_x,
        prenorm_y=prenorm_y,
    )
    return eye_cal, cal_type, track_mode


def parse_calibration_block(block: dict[str, Any]) -> CalibrationData:
    """Parse a complete calibration block."""
    text = block["text"]
    timestamp = block["timestamp"]

    # Determine eyes present
    has_left = "FOR LEFT" in text
    has_right = "FOR RIGHT" in text

    # Split text into left and right sections if both exist
    left_text = text
    right_text = text

    if has_left and has_right:
        parts = text.split("FOR RIGHT")
        left_text = parts[0]
        right_text = "FOR RIGHT" + parts[1]
    elif has_right:
        left_text = ""
    elif has_left:
        right_text = ""

    left_eye = None
    right_eye = None

    cal_type = "HV9"  # Default
    track_mode = "P-CR"  # Default

    if has_left:
        left_eye, c_type, t_mode = _parse_eye_calibration(left_text, "LEFT", full_text=text)
        if left_eye:
            cal_type = c_type
            track_mode = t_mode

    if has_right:
        right_eye, c_type, t_mode = _parse_eye_calibration(right_text, "RIGHT", full_text=text)
        if right_eye:
            # If both eyes, they should have same type/mode, but we take the last one or check consistency
            cal_type = c_type
            track_mode = t_mode

    return CalibrationData(
        timestamp=timestamp,
        calibration_type=cal_type,
        tracking_mode=track_mode,
        left_eye=left_eye,
        right_eye=right_eye,
        content=text,
    )


def parse_validation_block(block: dict[str, Any]) -> ValidationData:
    """Parse a complete validation block."""
    text = block["text"]
    timestamp = block["timestamp"]

    summary_left = None
    summary_right = None
    points = []
    target_positions: dict[int, tuple[float, float]] = {}  # {point_number: (x, y)}

    val_type = "HV9"  # Default
    track_mode = "LR"  # Default

    # Summaries
    # MSG	517872 !CAL VALIDATION HV9 LR LEFT  POOR ERROR 0.70 avg. 2.44 max  OFFSET 0.36 deg. -15.4,-14.4 pix.
    summary_pattern = (
        r"!CAL VALIDATION ([A-Z0-9]+) ([\w-]+) (LEFT|RIGHT)\s+(GOOD|POOR|FAILED|FAIR)\s+"
        r"ERROR\s+([-\d.]+)\s+avg\.\s+([-\d.]+)\s+max\s+"
        r"OFFSET\s+([-\d.]+)\s+deg\.\s+([-\d.]+),([-\d.]+)\s+pix\."
    )

    matches = re.findall(summary_pattern, text)
    for match in matches:
        val_type = match[0]
        track_mode = match[1]
        eye = match[2]
        summary = ValidationSummary(
            eye=eye,
            result=match[3],
            error_avg_deg=float(match[4]),
            error_max_deg=float(match[5]),
            offset_deg=float(match[6]),
            offset_pix_x=float(match[7]),
            offset_pix_y=float(match[8]),
        )
        if eye == "LEFT":
            summary_left = summary
        else:
            summary_right = summary

    # Points - extract both target positions and offsets
    # MSG	517872 VALIDATE LR POINT 0  LEFT  at 640,512  OFFSET 0.51 deg.  -8.8,-28.6 pix.
    point_pattern = (
        r"VALIDATE ([\w-]+) (?:4)?POINT (\d+)\s+(LEFT|RIGHT)\s+at\s+([-\d.]+),([-\d.]+)\s+"
        r"OFFSET\s+([-\d.]+)\s+deg\.\s+([-\d.]+),([-\d.]+)\s+pix\."
    )

    point_matches = re.findall(point_pattern, text)
    for match in point_matches:
        # match[0] is mode (e.g. LR), ignored here as we got it from summary or default
        point_num = int(match[1])
        target_x = float(match[3])
        target_y = float(match[4])
        offset_pix_x = float(match[6])
        offset_pix_y = float(match[7])

        # Store unique target positions (same for both eyes)
        if point_num not in target_positions:
            target_positions[point_num] = (target_x, target_y)

        # Create validation point with gaze calculated
        points.append(
            ValidationPoint(
                point_number=point_num,
                eye=match[2],
                offset_deg=float(match[5]),
                offset_pix_x=offset_pix_x,
                offset_pix_y=offset_pix_y,
                gaze_x=target_x + offset_pix_x,
                gaze_y=target_y + offset_pix_y,
            )
        )

    # Calculate PPD for each eye
    def calculate_ppd(points_list: list[ValidationPoint]) -> float | None:
        ppd_values = []
        for p in points_list:
            if p.offset_deg == 0:
                continue
            dist = math.sqrt(p.offset_pix_x**2 + p.offset_pix_y**2)
            ppd_values.append(dist / p.offset_deg)

        if not ppd_values:
            return None
        return sum(ppd_values) / len(ppd_values)

    # Create CalibrationTargets from collected target positions
    targets = None
    if target_positions:
        # Sort by point number to get ordered list
        sorted_targets = [target_positions[i] for i in sorted(target_positions.keys())]
        targets = CalibrationTargets(calibration_type=val_type, targets=sorted_targets)

    return ValidationData(
        timestamp=timestamp,
        validation_type=val_type,
        tracking_mode=track_mode,
        targets=targets,
        summary_left=summary_left,
        summary_right=summary_right,
        points=points,
        content=text,
    )


def parse_display_coords(asc_path: str | Path) -> DisplayCoords | None:
    """Parse DISPLAY_COORDS from ASC file header.

    Looks for line like: MSG 228029 DISPLAY_COORDS 0 0 1279 1023
    """
    with Path(asc_path).open(encoding="utf-8") as f:
        for line in f:
            match = re.match(r"MSG\s+\d+\s+DISPLAY_COORDS\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
            if match:
                return DisplayCoords(
                    left=int(match.group(1)),
                    top=int(match.group(2)),
                    right=int(match.group(3)),
                    bottom=int(match.group(4)),
                )
            # Stop searching after first calibration starts (DISPLAY_COORDS is in header)
            if ">>>>>>> CALIBRATION" in line:
                break
    return None


def parse_asc_file(asc_path: str | Path) -> SessionData:
    """Parse an EyeLink ASC file and return structured session data.

    This is the main entry point for parsing ASC files. It extracts:
    - Display coordinates
    - All calibration blocks with polynomial coefficients, gains, corner correction
    - All validation blocks with per-point errors and summary statistics

    Args:
        asc_path: Path to the ASC file

    Returns:
        SessionData object containing all parsed data

    Example:
        >>> session = parse_asc_file("data/recording.asc")
        >>> print(f"Found {len(session.calibrations)} calibrations")
        >>> session.save_json("output.json")

    """
    asc_path = Path(asc_path)

    # Parse display coordinates from header
    display_coords = parse_display_coords(asc_path)

    # Find all segments
    calibrations, validations, recordings = find_all_segments(asc_path)

    # Parse calibration and validation blocks
    parsed_calibrations = [parse_calibration_block(cal) for cal in calibrations]
    parsed_validations = [parse_validation_block(val) for val in validations]
    parsed_recordings = [
        RecordingData(start_time=rec["start"], end_time=rec["end"], content=rec["text"]) for rec in recordings
    ]

    return SessionData(
        calibrations=parsed_calibrations,
        validations=parsed_validations,
        recordings=parsed_recordings,
        display_coords=display_coords,
    )
