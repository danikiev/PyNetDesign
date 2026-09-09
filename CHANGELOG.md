# Changelog

All notable changes to PyNetDesign will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v1.0.0] - 2025-04-01

Initial public release, archived on Zenodo as
[10.5281/zenodo.14945917](https://doi.org/10.5281/zenodo.14945917). This changelog was
added retroactively so that the release is documented alongside its archived record; the
code itself is unchanged from the deposited version.

### Added

- magnitude sensitivity modelling for a 3D elastic homogeneous medium with attenuation: the minimum moment magnitude of a microseismic event that is theoretically detectable on a given network, evaluated on a 3D grid of potential source locations
- `get_mag_sensitivity` and `get_mag_sensitivity_local` high-level drivers, dispatching on the velocity model type and handling combined geometries
- `mag_sensitivity_grid` vectorized homogeneous-medium engine computing per-station minimum detectable moment magnitudes
- seismic moment to moment magnitude conversion after Kanamori (1977), and its inverse
- peak frequency estimation after Eisner et al. (2013), limited by a corner frequency defaulting to 100 Hz
- conversion of station noise levels to minimum detectable amplitudes for displacement, particle velocity, particle acceleration, strain, and strain-rate inputs, scaled by the required signal-to-noise ratio
- distributed acoustic sensing (DAS) support: gauge length parsing from the geometry header with unit conversion, strain and strain-rate noise types, and a directionality correction accounting for sensitivity along the cable axis
- support for station networks, DAS cables, and combined geometries evaluated together
- free surface amplification correction for receivers recording at the daily surface
- network detectability criterion based on the minimum number of stations required for P-wave, S-wave, or joint P- and S-wave detection
- ASCII readers for network geometry in local and global (WGS84) coordinates, with conversion of geographic to local Cartesian coordinates
- ASCII reader for homogeneous velocity models
- `DetectionParameters` container with validation for signal-to-noise ratios, station counts, and frequencies
- station geometry visualization in map and side views, colour-coded by noise level
- magnitude sensitivity slice visualization with contour and image rendering
- ten worked examples covering surface station networks, vertical, inclined and twice-inclined borehole DAS, depth-varying DAS noise profiles, and combined station plus DAS networks
- conda environment files for user and development installations, and Windows installation scripts
- MIT license

[Unreleased]: https://github.com/danikiev/PyNetDesign/compare/v1.0.0...HEAD
[v1.0.0]: https://github.com/danikiev/PyNetDesign/releases/tag/v1.0.0
