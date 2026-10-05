.. _contributing:

============
Contributing
============

Contributions, bug reports and suggestions are welcome.

Reporting a problem
===================

Please open an issue at
`github.com/danikiev/PyNetDesign/issues <https://github.com/danikiev/PyNetDesign/issues>`_.
A useful report states the PyNetDesign version, the Python version, what you expected,
what happened instead, and a small script or input file that reproduces the behaviour.

For a suspected error in the physics, the most useful report compares the computed result
against a closed-form expectation, because that makes the discrepancy measurable.

Development setup
=================

.. code-block:: bash

   git clone https://github.com/danikiev/PyNetDesign.git
   cd PyNetDesign
   conda env create -f environment.yml -n pnd
   conda activate pnd
   pip install -e ".[dev,docs]"

Branches and releases
=====================

Development happens on ``dev``, which is merged into ``main`` through a pull request.
Release tags follow strict semantic versioning as ``vMAJOR.MINOR.PATCH`` and must point
at a commit contained in ``main``; the version itself is derived from the tag by
``setuptools_scm``. The full procedure is described in ``RELEASE.md``.

Tests
=====

Run the suite from the repository root:

.. code-block:: bash

   pytest pytests/

Continuous integration runs the same suite on Python 3.9 to 3.12, validates the Zenodo
metadata, and builds this documentation.

Please add a test with any change to the algorithms. The convention in this project is to
assert against an independently written closed form rather than against a recorded
output, so that a test states the physics instead of freezing the current behaviour.

Documentation
=============

Build the documentation locally and view it with the helper scripts:

.. code-block:: bash

   ./build-docs.sh          # Linux, macOS;  build-docs.bat on Windows
   ./serve-docs.sh          # rebuilds incrementally, then serves on port 8000

``serve-docs`` accepts ``--port`` and ``--no-build``, and both scripts pass
``SPHINXOPTS`` through to Sphinx. Without the scripts the equivalent is
``python -m sphinx -M html docs/source docs/build``.

Docstrings follow the
`numpydoc <https://numpydoc.readthedocs.io>`_ style; equations use ``.. math::`` and
literature is cited with ``:cite:t:`` or ``:cite:p:`` against
``docs/source/references.bib``.

Changelog
=========

``CHANGELOG.md`` follows `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_. Add
your entry under ``[Unreleased]`` in the appropriate section, referencing the issue or
pull request number. The documentation page is generated from this file, so there is
nothing else to update.
