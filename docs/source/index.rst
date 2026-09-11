.. _overview:

========
Overview
========

.. only:: html

   .. container:: pynetdesign-index-logo

      .. image:: _static/pynetdesign-logo.svg
         :alt: PyNetDesign logo
         :align: center
         :width: 520px

PyNetDesign is an open-source Python framework for testing and designing microseismic
monitoring networks in homogeneous velocity models.

PyNetDesign determines the **magnitude sensitivity** of a monitoring network, that is the
minimum moment magnitude that a given set of receivers can theoretically detect. It works
with conventional station networks and with distributed acoustic sensing (DAS) cables,
including both at the same time, and accounts for the directional sensitivity that makes
a DAS cable behave differently from a three-component station. Results are presented as
horizontal or vertical slices through a 3D grid of potential source locations.

The modelling API also provides synthetic geometry generators for borehole, surface and
dark-fibre layouts, so that trial networks can be built from code rather than from
hand-written tables.

The core algorithms are vectorized with `NumPy <https://numpy.org/>`_, input and output
rely on `Pandas <https://pandas.pydata.org/>`_, and visualization is based on
`Matplotlib <https://matplotlib.org/>`_ with perceptually uniform colour maps from
`cmcrameri <https://pypi.org/project/cmcrameri/>`_.

**Current PyNetDesign version:** |release|

----

.. toctree::
   :maxdepth: 3
   :hidden:
   :caption: Contents

   self
   getting_started.rst
   methodology.rst
   examples/index.rst
   api/index.rst

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Project

   changelog.rst
   citing.rst
   contributing.rst
   credits.rst

.. only:: html

   .. grid:: 1 2 4 4

      .. grid-item-card::
         :link: getting_started
         :link-type: doc
         :link-alt: Getting started

         :fas:`play;pst-color-primary` **Getting Started**
         ^^^
         Install PyNetDesign and prepare geometry and velocity input files.

      .. grid-item-card::
         :link: methodology
         :link-type: doc
         :link-alt: Methodology

         :fas:`book;pst-color-primary` **Methodology**
         ^^^
         The theory behind the detectability calculation, phase by phase.

      .. grid-item-card::
         :link: examples/index
         :link-type: doc
         :link-alt: Examples

         :fas:`lightbulb;pst-color-primary` **Examples**
         ^^^
         Worked examples for station and DAS monitoring networks.

      .. grid-item-card::
         :link: api/index
         :link-type: doc
         :link-alt: API Reference

         :fas:`code;pst-color-primary` **API Reference**
         ^^^
         Reference documentation for every public function.

   .. grid:: 1

      .. grid-item-card::
         :link: _static/pynetdesign.pdf
         :link-alt: pdf

         :fas:`file-pdf;pst-color-primary` **Download as PDF**
         ^^^
         Download this documentation as a standalone :fas:`file-pdf` PDF file.
