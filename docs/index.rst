SyeLink Documentation
=====================

|PyPI| |Downloads| |License| |Documentation| |DOI|

.. |PyPI| image:: https://img.shields.io/pypi/v/syelink
   :target: https://pypi.org/project/syelink/
   :alt: PyPI version

.. |Downloads| image:: https://static.pepy.tech/badge/syelink
   :target: https://pepy.tech/project/syelink
   :alt: Downloads

.. |License| image:: https://img.shields.io/pypi/l/syelink
   :target: https://github.com/mh-salari/syelink/blob/main/LICENSE
   :alt: License

.. |Documentation| image:: https://readthedocs.org/projects/syelink/badge/?version=latest
   :target: https://syelink.readthedocs.io/
   :alt: Documentation

.. |DOI| image:: https://img.shields.io/badge/DOI-TODO-blue
   :target: https://doi.org/TODO
   :alt: DOI

**SyeLink** is a Python library for parsing EyeLink eye tracker data from ASC files.
It extracts calibration, validation, recording, and gaze sample data into structured
Python objects, with export to JSON and CSV.

Features
--------

- Parse EyeLink ASC files into structured dataclasses
- Extract calibration, validation, recording, and gaze sample data
- Export gaze samples to CSV with optional raw pupil/CR data
- Visualize calibration and validation results
- Command-line interface for common tasks
- Support for binocular and monocular recordings

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting_started
   cli

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

----

.. note::

   This project has received funding from the European Union's Horizon Europe
   research and innovation funding program under grant agreement No 101072410,
   Eyes4ICU project.

| Author: `Mohammadhossein Salari <https://mh-salari.ir>`_
