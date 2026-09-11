.. _api:

=============
API Reference
=============

The Application Programming Interface (API) of PyNetDesign is composed of the following
modules:

* :ref:`modelling`: algorithms for modelling related to microseismic network design

  * :ref:`core`: high-level drivers for magnitude sensitivity
  * :ref:`homogeneous`: algorithms for a homogeneous velocity model
  * :ref:`geometry_modelling`: synthetic geometry generators
  * :ref:`io`: reading and writing geometry and velocity files
  * :ref:`classes`: parameter containers
  * :ref:`utils_modelling`: wave modes, radiation patterns, amplitudes and grid helpers

* :ref:`visualization`: plotting of results and input

  * :ref:`geometry`: receiver geometry
  * :ref:`sensitivity`: magnitude sensitivity results
  * :ref:`utils_visualization`: general utility functions for visualization

----

.. _modelling:

Modelling
=========

.. _core:

Core
----

.. currentmodule:: pynetdesign.modelling.core

.. autosummary::
   :toctree: generated/

   get_mag_sensitivity
   get_mag_sensitivity_local

.. _homogeneous:

Homogeneous
-----------

.. currentmodule:: pynetdesign.modelling.homo

.. autosummary::
   :toctree: generated/

   mag_sensitivity_grid
   calculate_M0
   calculate_fpeak
   validate_parameters

.. _geometry_modelling:

Geometry generators
-------------------

.. currentmodule:: pynetdesign.modelling.geometry

.. autosummary::
   :toctree: generated/

   generate_geometry
   generate_borehole_geometry
   generate_surface_geometry
   generate_darkfiber_geometry

.. _io:

Input / output
--------------

.. currentmodule:: pynetdesign.modelling.io

.. autosummary::
   :toctree: generated/

   read_geometry
   save_geometry
   read_velocity
   combine_geometry
   is_combined_geometry
   decimate_geometry
   global2local

.. _classes:

Classes
-------

.. currentmodule:: pynetdesign.modelling.classes

.. autosummary::
   :toctree: generated/

   DetectionParameters

.. _utils_modelling:

Modelling utilities
-------------------

Wave modes and radiation patterns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: pynetdesign.modelling.utils

.. autosummary::
   :toctree: generated/

   normalize_wave_mode
   wave_mode_phases
   wave_mode_has_p
   wave_mode_has_s
   wave_mode_s_phases
   phase_radiation_pattern
   resolve_radiation_pattern

Magnitudes and amplitudes
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :toctree: generated/

   calculate_Mw
   calculate_seismic_moment
   get_scaling_displacement
   retrieve_min_amps

Detectability and receiver response
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :toctree: generated/

   mag_detectable
   check_min_stations
   compute_free_surface_coefficients
   get_phase_station_directionality
   geometry_requires_receiver_projection
   get_ray_station_directionality

Grids and helpers
^^^^^^^^^^^^^^^^^

.. autosummary::
   :toctree: generated/

   generate_grid
   reshape_grid
   reshape_data
   get_slice_coordinates
   are_points_inside
   find_indices_of_points
   nth_minimum
   check_zero_values
   contains_only_numeric
   compute_gcd_of_floats

----

.. _visualization:

Visualization
=============

.. _geometry:

Geometry
--------

.. currentmodule:: pynetdesign.visualization.geometry

.. autosummary::
   :toctree: generated/

   plot_stations_view

.. _sensitivity:

Sensitivity
-----------

.. currentmodule:: pynetdesign.visualization.sensitivity

.. autosummary::
   :toctree: generated/

   plot_sensitivity_slice

.. _utils_visualization:

Visualization utilities
-----------------------

.. currentmodule:: pynetdesign.visualization.utils

.. autosummary::
   :toctree: generated/

   generate_colorscale
   is_notebook
   check_spyder
