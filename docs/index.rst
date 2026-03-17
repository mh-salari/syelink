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

.. |DOI| image:: https://img.shields.io/badge/DOI-coming_soon-blue
   :target: #
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

.. note::

   If you use SyeLink in your research, please cite:

   Salari, M., Nyström, M., Niehorster, D. C., & Bednarik, R. (2026).
   PyeLink and SyeLink: Open-source Python tools for low-level EyeLink experiment control and data parsing.
   In *Proceedings of the 2026 Eye Tracking Research & Applications (ETRA 2026) Late-Breaking Work*. ACM.
   *[Accepted; DOI forthcoming]*

| Author: `Mohammadhossein Salari <https://mh-salari.ir>`_
