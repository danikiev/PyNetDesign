.. _getting_started:

===============
Getting Started
===============

This chapter explains how to install PyNetDesign, how to describe a monitoring network
and a velocity model, and how to run a first sensitivity calculation.

----

.. _installation:

Installation
============

Requirements
------------

PyNetDesign works with Python 3.9 to 3.12. Cloning the repository requires
`Git <https://git-scm.com/>`_, and the recommended way to create the environment is the
`Conda <https://conda.io>`_ package manager, for example through
`Miniforge <https://github.com/conda-forge/miniforge>`_.

Dependencies
------------

The runtime dependencies are declared in ``pyproject.toml`` and installed by ``pip``:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Package
     - Purpose
   * - `numpy <https://numpy.org/>`_
     - vectorized numerical core
   * - `pandas <https://pandas.pydata.org/>`_
     - geometry and velocity model tables, and their metadata
   * - `matplotlib <https://matplotlib.org/>`_
     - plotting
   * - `cmcrameri <https://pypi.org/project/cmcrameri/>`_
     - perceptually uniform scientific colour maps

Two optional groups are available: ``dev`` adds ``pytest`` and an interactive Jupyter
stack, and ``docs`` adds the Sphinx toolchain used to build this documentation.

The author is grateful to the developers of these packages.

Install using conda and pip
---------------------------

``environment.yml`` pins only the interpreter; every package dependency comes from
``pyproject.toml``. Clone the repository:

.. code-block:: bash

   git clone https://github.com/danikiev/PyNetDesign.git
   cd PyNetDesign

create and activate the environment:

.. code-block:: bash

   conda env create -f environment.yml -n pnd
   conda activate pnd

and install the package:

.. code-block:: bash

   pip install -e .

To also install the test and documentation tools:

.. code-block:: bash

   pip install -e ".[dev,docs]"

.. tip::

   Using ``mamba`` instead of ``conda`` speeds up environment creation considerably.

Install using script
--------------------

The helper scripts perform the steps above, creating the ``pnd`` environment and
asking whether to add the development tools:

.. code-block:: bash

   ./install.sh            # Linux, macOS
   install.bat             # Windows, from a Miniforge prompt

Pass ``--dev`` or ``--no-dev`` to ``install.sh`` to answer in advance.

Uninstall
---------

Deactivate and remove the environment:

.. code-block:: bash

   conda deactivate
   conda remove -n pnd --all

``./uninstall.sh`` on Linux and macOS, or ``uninstall.bat`` on Windows, finds every
environment whose name starts with ``pnd`` and asks about each one.

----

.. _package_design:

Package Design
==============

PyNetDesign is organised into two subpackages:

* :mod:`pynetdesign.modelling` contains the algorithms:

  * :mod:`~pynetdesign.modelling.core` provides the high-level drivers,
  * :mod:`~pynetdesign.modelling.homo` implements the homogeneous-medium engine,
  * :mod:`~pynetdesign.modelling.geometry` generates synthetic receiver layouts,
  * :mod:`~pynetdesign.modelling.io` reads and writes input files,
  * :mod:`~pynetdesign.modelling.utils` holds the wave-mode, amplitude and grid helpers.

* :mod:`pynetdesign.visualization` plots receiver geometry and sensitivity results.

Both subpackages are re-exported at the top level, so either style works:

.. code-block:: python

   import pynetdesign.modelling as pndmod
   import pynetdesign.visualization as pndvis

----

.. _input_files:

Input Files
===========

PyNetDesign reads two whitespace-delimited ASCII files: a velocity model and a
monitoring network geometry.

.. _velocity_model:

Velocity model
--------------

The velocity model file has a fixed header and, for a homogeneous medium, exactly one
row of values:

.. code-block:: text

   Depth(m) Vp(m/s) Vp/Vs Qp Qs density(kg/m^3) Ep(anisotropy) Dt(anisotropy) Gm(anisotropy)
   0        2370    2     100 100 2500           0              0              0

The columns are the layer top depth, the P-wave velocity, the P-to-S velocity ratio, the
P- and S-wave quality factors, the density, and three Thomsen anisotropy parameters.

.. note::

   The Thomsen parameters are read and stored but not used in the calculation: the
   medium is treated as isotropic. Supplying more than one row raises an error, because
   PyNetDesign models a homogeneous medium only.

Read it with :func:`~pynetdesign.modelling.io.read_velocity`:

.. code-block:: python

   velocity_df = pndmod.io.read_velocity('velocity_model.txt')

The S-wave velocity is derived as ``Vp / VpVsRatio`` and added as a ``Vs`` column.

.. _geometry_file:

Monitoring network geometry
---------------------------

The geometry file describes the receivers, one per row. A local-coordinate station
network looks like this:

.. code-block:: text

   Name  Northing(m) Easting(m) Elevation(m) NoiseLevel(m/s)
   ST1   0           0          0            5.0E-09
   ST2   5000        0          0            5.0E-09
   ST3   2500        4330       0            5.0E-09

and a DAS cable declares its gauge length in the header:

.. code-block:: text

   Northing(m) Easting(m) Elevation(m) NoiseLevel(1/s) GaugeLength=10(m)
   0           0          0           1.95E-09
   0           0          -1          1.95E-09
   0           0          -2          1.95E-09

Required columns are a northing or latitude, an easting or longitude, an elevation and a
noise level. Optional columns are:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Meaning
   * - ``Name``
     - receiver label, used in plots
   * - ``Surface``
     - weight in [0, 1] marking receivers at the free surface; a fractional value blends
       between no amplification and full amplification
   * - ``Components``
     - ``3C`` or ``Z``; a ``Z`` receiver records only the vertical component and is
       projected accordingly. Not allowed together with a gauge length

Geographic coordinates are given as ``Latitude(WGS84)`` and ``Longitude(WGS84)`` and are
converted to a local Cartesian frame with
:func:`~pynetdesign.modelling.io.global2local`. Latitude and longitude must both be
present, or neither.

.. note::

   ``Elevation`` is positive upwards, while the internal ``Z`` coordinate is depth,
   positive downwards. A receiver written with ``Elevation = -500`` is stored as
   ``Z = 500``. The writer reverses this, so a round trip through
   :func:`~pynetdesign.modelling.io.save_geometry` is lossless.

Distance units
^^^^^^^^^^^^^^

Coordinate columns and the gauge length accept a unit in parentheses and are converted to
metres: ``m``, ``km``, ``cm``, ``mm``, ``ft`` and ``in``. All coordinate columns of one
file must use the same unit.

Amplitude units
^^^^^^^^^^^^^^^

The unit of ``NoiseLevel`` selects how the noise is converted to a displacement amplitude
spectrum, as described in Section :ref:`detection_threshold`:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Unit in header
     - Interpreted as
     - Typical receiver
   * - ``m``
     - displacement
     - displacement sensor
   * - ``m/s``
     - particle velocity
     - geophone, seismometer
   * - ``m/s^2``
     - particle acceleration
     - accelerometer
   * - ``1/s``
     - strain rate
     - DAS
   * - ``strain``, ``1``, ``units``, ``none``
     - strain
     - DAS

A gauge length is required for strain and strain-rate data, and its presence is what
marks a geometry as DAS.

Read geometry files
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   geometry_df = pndmod.io.read_geometry('net_geometry.txt')
   print(geometry_df.attrs)

The returned DataFrame has columns ``Name``, ``X``, ``Y``, ``Z`` and ``NoiseLevel``, plus
any optional columns, and carries metadata in ``attrs``: the file path, the original
coordinate unit, the noise unit and type, the coordinate system, and the gauge length
when present.

Generate and save geometry files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Trial layouts can be built from code with
:func:`~pynetdesign.modelling.geometry.generate_geometry`, which returns geometry text
lines that :func:`~pynetdesign.modelling.io.save_geometry` writes to disk:

.. code-block:: python

   lines = pndmod.geometry.generate_geometry(
       mode='borehole',        # 'borehole', 'surface' or 'darkfiber'
       cable_length=999.0,     # m of cable
       spacing=1.0,            # m between channels
       noise_level=1.95e-9,    # strain rate
       gauge_length=10.0,      # m
   )
   pndmod.io.save_geometry(lines, 'das_geometry.txt')
   geometry_df = pndmod.io.read_geometry('das_geometry.txt')

Surface layouts accept a ``surface_shape`` of ``line``, ``zigzag``, ``L``, ``square`` or
``double_line``; boreholes accept an ``azimuth`` and ``dip``, and can apply a
depth-dependent noise profile. A dense cable can be thinned with
:func:`~pynetdesign.modelling.io.decimate_geometry`:

.. code-block:: python

   sparse_df = pndmod.io.decimate_geometry(geometry_df, 5)   # every 5th channel

Combine geometries
^^^^^^^^^^^^^^^^^^

Several networks can be evaluated together, for instance a surface station array and a
borehole DAS cable, with :func:`~pynetdesign.modelling.io.combine_geometry`:

.. code-block:: python

   combined_df = pndmod.io.combine_geometry(stations_df, das_df)

Each contributing geometry keeps its own noise type and gauge length, and the
per-receiver thresholds are concatenated before the network criterion is applied.

----

.. _quickstart:

Quickstart
==========

The following computes the minimum detectable moment magnitude on a vertical section
through a borehole DAS array and plots it:

.. code-block:: python

   import numpy as np
   import pynetdesign.modelling as pndmod
   import pynetdesign.visualization as pndvis

   # Input
   geometry_df = pndmod.io.read_geometry('das_geometry.txt')
   velocity_df = pndmod.io.read_velocity('velocity_model.txt')

   # Grid of potential source locations
   gx = np.arange(0.0, 2000.0 + 25.0, 25.0)
   gy = np.array([0.0])
   gz = np.arange(25.0, 1500.0 + 25.0, 25.0)
   grid_points = pndmod.utils.generate_grid(x=gx, y=gy, z=gz)

   # Detection criteria
   params = pndmod.classes.DetectionParameters(
       min_SNR_p=2,          # SNR required on one channel
       min_SNR_s=2,
       min_stations_p=60,    # channels required for detection
       min_stations_s=60,
   )

   # Minimum detectable magnitude, requiring both P and S
   mw_min = pndmod.core.get_mag_sensitivity(
       grid_coords=grid_points,
       geometry_df=geometry_df,
       velocity_df=velocity_df,
       params=params,
       wave_mode='PS',
   )

   # Vertical section at Y = 0
   _ = pndvis.sensitivity.plot_sensitivity_slice(
       sens_data=mw_min, xi=gx, zi=gz,
       geometry_df=geometry_df, clb_title='$M_w$')

``wave_mode`` selects the phases: ``'P'``, ``'SV'``, ``'SH'``, ``'S'`` for the composite
S branch, or ``'PS'`` for joint P and S detection. See Section
:ref:`network_detectability` for how the per-receiver thresholds are combined, and the
:ref:`examples <examples>` for complete scripts.
