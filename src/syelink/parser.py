"""ASC file parser for EyeLink eye tracking data.

Extracts calibrations, validations, and recordings from ASC files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
# Note: Path is used at runtime so it stays at top-level


def find_all_segments(asc_file: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract complete calibration, validation, and recording blocks from an ASC file.

    Args:
        asc_file: Path to the ASC file

    Returns:
        Tuple of (calibrations, validations, recordings) where each is a list of dicts
        with 'timestamp' and 'text' keys (recordings also have 'start' and 'end').

    """
    calibrations: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    recordings: list[dict[str, Any]] = []

    current_cal_block: dict[str, Any] | None = None
    current_val_block: dict[str, Any] | None = None
    current_rec_block: dict[str, Any] | None = None

    with Path(asc_file).open(encoding="utf-8") as f:
        for line in f:
            # CALIBRATION START
            if ">>>>>>> CALIBRATION" in line and "FOR" in line:
                # If we already have a block with results, this is a new calibration
                if current_cal_block is not None and current_cal_block.get("has_results", False):
                    calibrations.append({
                        "timestamp": current_cal_block["timestamp"],
                        "text": "".join(current_cal_block["lines"]),
                    })
                    current_cal_block = None

                if current_cal_block is None:
                    current_cal_block = {"lines": [], "timestamp": None, "has_results": False}
                current_cal_block["lines"].append(line)
                continue

            # CALIBRATION RESULT
            cal_result = re.match(r"MSG\s+(\d+)\s+!CAL CALIBRATION ([A-Z0-9]+) ([\w-]+) (LEFT|RIGHT)\s+(\w+)", line)
            if cal_result and current_cal_block is not None:
                current_cal_block["lines"].append(line)
                current_cal_block["has_results"] = True
                if current_cal_block["timestamp"] is None:
                    current_cal_block["timestamp"] = int(cal_result.group(1))
                continue

            # INPUT after calibration closes the calibration block
            if line.startswith("INPUT") and current_cal_block is not None:
                current_cal_block["lines"].append(line)
                calibrations.append({
                    "timestamp": current_cal_block["timestamp"],
                    "text": "".join(current_cal_block["lines"]),
                })
                current_cal_block = None
                continue

            # If we're in a calibration block, collect MSG lines and continuation lines (not gaze samples)
            if current_cal_block is not None:
                # Skip gaze sample data (lines starting with a digit timestamp)
                if line and line[0].isdigit():
                    continue

                # Collect MSG lines and their continuation lines (indented with whitespace)
                if line.startswith("MSG") or (line and line[0].isspace()):
                    current_cal_block["lines"].append(line)
                    time_match = re.match(r"MSG\s+(\d+)", line)
                    if time_match and current_cal_block["timestamp"] is None:
                        current_cal_block["timestamp"] = int(time_match.group(1))
                continue

            # VALIDATION START
            val_start = re.match(r"MSG\s+(\d+)\s+!CAL VALIDATION ([A-Z0-9]+) ([\w-]+) (LEFT|RIGHT)\s+(\w+)", line)
            if val_start:
                if current_val_block is None:
                    current_val_block = {"timestamp": int(val_start.group(1)), "lines": [line]}
                else:
                    current_val_block["lines"].append(line)
                continue

            # Collect validation-related MSG lines
            if (
                current_val_block is not None
                and line.startswith("MSG")
                and ("VALIDATE" in line or "!CAL VALIDATION" in line)
            ):
                current_val_block["lines"].append(line)
                continue

            # Close validation block on meaningful boundaries (not gaze sample data)
            if current_val_block is not None and (
                line.startswith(("START", "INPUT")) or ">>>>>>> CALIBRATION" in line
            ):
                validations.append({
                    "timestamp": current_val_block["timestamp"],
                    "text": "".join(current_val_block["lines"]),
                })
                current_val_block = None

            # RECORDING START
            if line.startswith("START"):
                start_match = re.match(r"START\s+(\d+)", line)
                if start_match:
                    current_rec_block = {"start": int(start_match.group(1)), "end": None, "lines": [line]}
                continue

            # If we're in a recording block, collect all lines
            if current_rec_block is not None:
                current_rec_block["lines"].append(line)
                if line.startswith("END"):
                    end_match = re.match(r"END\s+(\d+)", line)
                    if end_match:
                        current_rec_block["end"] = int(end_match.group(1))
                        recordings.append({
                            "start": current_rec_block["start"],
                            "end": current_rec_block["end"],
                            "text": "".join(current_rec_block["lines"]),
                        })
                        current_rec_block = None
                continue

    # Close any unclosed validation block at end of file
    if current_val_block is not None:
        validations.append({
            "timestamp": current_val_block["timestamp"],
            "text": "".join(current_val_block["lines"]),
        })

    return calibrations, validations, recordings
