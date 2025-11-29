# syelink

Parse and visualize EyeLink eye tracker data from ASC files.

## Features

- Parse EyeLink ASC files into structured JSON
- Extract calibration, validation, and recording data
- Visualize calibration and validation results
- Preserve all numerical precision through JSON serialization
- Command-line interface for common tasks

## Installation

```bash
uv pip install syelink
```

Or install from source:

```bash
git clone https://github.com/mh-salari/syelink.git
cd syelink
uv pip install -e .
```

## Quick Start

### Parse an ASC file

```bash
uv run syelink parse data.asc
```

This creates `data.json` with all calibration, validation, and recording data.

### View session information

```bash
uv run syelink info data.json
```

### Generate validation plot

```bash
uv run syelink plot-validation data.json -i 0 -o validation.png
```

### Generate calibration plot

```bash
uv run syelink plot-calibration data.json -i 0 -o calibration.png
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `syelink parse <asc_file>` | Parse ASC file to JSON |
| `syelink info <json_file>` | Show session information |
| `syelink plot-validation <json_file>` | Plot validation data |
| `syelink plot-calibration <json_file>` | Plot calibration data |

### Options

**parse**
- `-o, --output` - Output JSON file path (default: same name as ASC file)

**plot-validation / plot-calibration**
- `-i, --index` - Calibration/validation index (default: 0)
- `-o, --output` - Output image path
- `--show` - Show plot interactively
- `--target-image` - Custom target image (validation only)

## Python API

```python
from syelink import parse_asc_file, SessionData

# Parse ASC file
session = parse_asc_file("data.asc")

# Access data
print(f"Display: {session.display_coords.width}x{session.display_coords.height}")
print(f"Calibrations: {len(session.calibrations)}")
print(f"Validations: {len(session.validations)}")

# Save to JSON
session.save_json("data.json")

# Load from JSON
session = SessionData.load_json("data.json")

# Access validation errors
for val in session.validations:
    if val.summary_left:
        print(f"Left eye avg error: {val.summary_left.error_avg_deg:.2f}°")
```

## Data Structure

The parsed data includes:

- **Display coordinates** - Screen resolution and boundaries
- **Calibrations** - Calibration points, polynomial coefficients, gains, results
- **Validations** - Target positions, gaze offsets, error metrics
- **Recordings** - Start/end timestamps for recording blocks

All numerical values are preserved with full precision through JSON serialization.

## License

MIT
