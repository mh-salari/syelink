Command-Line Interface
======================

SyeLink provides a CLI for common tasks. All commands are available via ``syelink`` or ``uv run syelink``.

Commands
--------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Command
     - Description
   * - ``syelink convert <asc_file>``
     - Convert ASC file to JSON, text files, and/or CSV samples
   * - ``syelink info <data_file>``
     - Show session information (accepts ASC or JSON)
   * - ``syelink export-samples <data_file>``
     - Export gaze samples to CSV
   * - ``syelink plot-validation <json_file>``
     - Plot validation data
   * - ``syelink plot-calibration <json_file>``
     - Plot calibration data

convert
-------

Convert an ASC file to structured output formats.

.. code-block:: bash

   syelink convert data.asc            # Export all formats
   syelink convert data.asc --json     # JSON only
   syelink convert data.asc --text     # Text files only
   syelink convert data.asc --samples  # CSV samples only

   # Merge HREF coordinates from a matching `edf2asc -sh` export:
   syelink convert data_gaze.asc --href data_href.asc

Options:

- ``-o, --output`` -- Output directory (default: same directory as ASC file)
- ``--json`` -- Export JSON file only
- ``--text`` -- Export text files only
- ``--samples`` -- Export gaze samples CSV only
- ``--href`` -- Path to a matching ``edf2asc -sh`` HREF ASC; merges per-sample HREF coordinates into the gaze samples and exports them alongside in the JSON and CSV
- Without flags: exports all formats (JSON + text + CSV)

info
----

Show session information.

.. code-block:: bash

   syelink info data.json
   syelink info data.asc
   syelink info data_gaze.asc --href data_href.asc

Shows calibration/validation counts, display info, and gaze sample statistics
(including how many samples carry HREF coordinates when ``--href`` is used).

Options:

- ``--href`` -- Path to a matching ``edf2asc -sh`` HREF ASC (only valid when the input is an ASC; JSON inputs already carry HREF if it was merged at parse time)

export-samples
--------------

Export gaze samples to CSV.

.. code-block:: bash

   syelink export-samples data.asc -o samples.csv
   syelink export-samples data_gaze.asc --href data_href.asc -o samples.csv

Options:

- ``-o, --output`` -- Output CSV file path (default: ``<filename>_samples.csv``)
- ``--href`` -- Path to a matching ``edf2asc -sh`` HREF ASC (only valid when the input is an ASC)

plot-validation
---------------

Generate a validation plot.

.. code-block:: bash

   syelink plot-validation data.json -i 0 -o validation.png

Options:

- ``-i, --index`` -- Validation index (default: 0)
- ``-o, --output`` -- Output image path
- ``--show`` -- Show plot interactively
- ``--target-image`` -- Custom target image

plot-calibration
----------------

Generate a calibration plot.

.. code-block:: bash

   syelink plot-calibration data.json -i 0 -o calibration.png

Options:

- ``-i, --index`` -- Calibration index (default: 0)
- ``-o, --output`` -- Output image path
- ``--show`` -- Show plot interactively
