# syelink

Parse and visualize EyeLink eye tracker data from ASC files.

## Features

- Parse EyeLink ASC files into structured JSON
- Extract calibration, validation, recording, and gaze sample data
- Export gaze samples to CSV with optional raw pupil/CR data
- Visualize calibration and validation results
- Command-line interface for common tasks
- Support for binocular and monocular (left/right only) recordings

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

### Convert an ASC file to JSON, text files, and CSV

```bash
uv run syelink convert data.asc
```

This creates:
- `data.json` - All session data (calibration, validation, recordings, gaze samples)
- `data_samples.csv` - Gaze samples with timestamps, positions, pupil sizes, and optional raw data
- Human-readable text files: `recordings.txt`, `calibrations.txt`, `validations.txt`, `metadata.txt`

To export only specific formats:

```bash
uv run syelink convert data.asc --json      # JSON only
uv run syelink convert data.asc --text      # Text files only
uv run syelink convert data.asc --samples   # CSV samples only
```

### View session information

```bash
uv run syelink info data.json
```

Shows calibration/validation count, display info, and gaze sample statistics.

### Export gaze samples to CSV

```bash
uv run syelink export-samples data.asc -o samples.csv
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
| `syelink convert <asc_file>` | Convert ASC file to JSON, text files, and/or CSV samples |
| `syelink info <data_file>` | Show session information (accepts ASC or JSON) |
| `syelink export-samples <data_file>` | Export gaze samples to CSV |
| `syelink plot-validation <json_file>` | Plot validation data |
| `syelink plot-calibration <json_file>` | Plot calibration data |

### Options

**convert**
- `-o, --output` - Output directory (default: same directory as ASC file)
- `--json` - Export JSON file only
- `--text` - Export text files only
- `--samples` - Export gaze samples CSV only
- Without flags: exports all formats (JSON + text + CSV)

**export-samples**
- `-o, --output` - Output CSV file path (default: `<filename>_samples.csv`)

**info**
- Shows calibration/validation counts, display info, and gaze sample statistics

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
print(f"Gaze samples: {len(session.gaze_samples):,}")

# Save to JSON
session.save_json("data.json")

# Save gaze samples to CSV
session.save_samples_csv("gaze_samples.csv")

# Load from JSON
session = SessionData.load_json("data.json")

# Access validation errors
for val in session.validations:
    if val.summary_left:
        print(f"Left eye avg error: {val.summary_left.error_avg_deg:.2f}°")

# Access gaze samples
for sample in session.gaze_samples[:10]:  # First 10 samples
    print(f"Time: {sample.timestamp}, Left: ({sample.left_gaze_x}, {sample.left_gaze_y})")
```

## Data Structure

The parsed data includes:

- **Display coordinates** - Screen resolution and boundaries
- **Calibrations** - Calibration points, polynomial coefficients, gains, results
- **Validations** - Target positions, gaze offsets, error metrics
- **Recordings** - Start/end timestamps for recording blocks
- **Gaze samples** - Timestamps, gaze positions (x, y), pupil sizes, and optional raw pupil/CR data
  - Supports binocular (both eyes) and monocular (left or right only) recordings
  - CSV export includes 32 columns: metadata, gaze data, and raw camera measurements

## Examples

Check the `examples/` directory for complete usage examples:

- `basic_usage.py` - Parse ASC files, save to JSON/CSV/text, and load data
- `plot_example.py` - Generate calibration and validation plots

Run examples with:

```bash
cd examples
uv run python basic_usage.py data/both_eyes/both_eyes.asc
uv run python plot_example.py data/both_eyes/parsed_output.json
```

Example data includes:
- `both_eyes/` - Binocular tracking data
- `left_eye/` - Left eye only tracking data
- `right_eye/` - Right eye only tracking data

## License

MIT
