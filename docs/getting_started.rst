Getting Started
===============

Installation
------------

Install from PyPI:

.. code-block:: bash

   uv pip install syelink

Or install from source:

.. code-block:: bash

   git clone https://github.com/mh-salari/syelink.git
   cd syelink
   uv pip install -e .

Quick Start
-----------

Convert an ASC file
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv run syelink convert data.asc

This creates:

- ``data.json`` -- All session data (calibration, validation, recordings, gaze samples)
- ``data_samples.csv`` -- Gaze samples with timestamps, positions, pupil sizes, and optional raw data
- Human-readable text files: ``recordings.txt``, ``calibrations.txt``, ``validations.txt``, ``metadata.txt``

Python API
^^^^^^^^^^

.. code-block:: python

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

Accessing validation errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   for val in session.validations:
       if val.summary_left:
           print(f"Left eye avg error: {val.summary_left.error_avg_deg:.2f}")

Accessing gaze samples
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   for sample in session.gaze_samples[:10]:
       print(f"Time: {sample.timestamp}, Left: ({sample.left_gaze_x}, {sample.left_gaze_y})")

Including HREF coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^^

The default ``edf2asc`` export writes screen-pixel gaze coordinates only. To also
get head-referenced angular coordinates (HREF) per sample, export the same EDF a
second time with ``edf2asc -sh`` and pass that file alongside the gaze ASC.

Both invocations of ``edf2asc`` write to the same default filename
(``recording.asc``), so the gaze export must be renamed before running the HREF
export to avoid overwriting it:

.. code-block:: bash

   edf2asc recording.edf            # writes recording.asc (gaze)
   mv recording.asc recording_gaze.asc

   edf2asc -sh recording.edf        # writes recording.asc (HREF)
   mv recording.asc recording_href.asc

.. code-block:: python

   session = parse_asc_file("recording_gaze.asc", href_asc_path="recording_href.asc")

   for sample in session.gaze_samples[:10]:
       print(
           f"Time: {sample.timestamp}, "
           f"left HREF: ({sample.left_href_x}, {sample.left_href_y})"
       )

HREF coordinates are merged by timestamp into the existing gaze samples and exposed
as ``left_href_x``, ``left_href_y``, ``right_href_x``, ``right_href_y``. The pupil-area
column is cross-checked between the two ASCs to make sure they were exported from
the same EDF; a mismatch raises ``ValueError``. HREF units are EyeLink's internal
angular units (~261.8 units / deg of visual angle).

Examples
--------

Check the ``examples/`` directory in the repository for complete usage examples:

- ``basic_usage.py`` -- Parse ASC files, save to JSON/CSV/text, and load data
- ``plot_example.py`` -- Generate calibration and validation plots

.. code-block:: bash

   cd examples
   uv run python basic_usage.py data/both_eyes/both_eyes.asc
   uv run python plot_example.py data/both_eyes/parsed_output.json
