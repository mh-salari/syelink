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

Examples
--------

Check the ``examples/`` directory in the repository for complete usage examples:

- ``basic_usage.py`` -- Parse ASC files, save to JSON/CSV/text, and load data
- ``plot_example.py`` -- Generate calibration and validation plots

.. code-block:: bash

   cd examples
   uv run python basic_usage.py data/both_eyes/both_eyes.asc
   uv run python plot_example.py data/both_eyes/parsed_output.json
