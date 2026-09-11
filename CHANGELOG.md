# Changelog

All notable changes to PyNetDesign will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- phase-resolved wave modes: `wave_mode` accepts `'P'`, `'SV'`, `'SH'`, `'S'` and `'PS'`, where `'S'` is a composite mode keeping the more detectable of the SV and SH branches
- root-mean-square radiation-pattern magnitudes per phase, `R_P = sqrt(4/15) ~ 0.52`, `R_SV = sqrt(7/30) ~ 0.48` and `R_SH = sqrt(1/6) ~ 0.41`, averaged over the focal sphere of a double-couple source after Boore and Boatwright (1984) and Hallo and Eisner (2013), exposed through `phase_radiation_pattern`
- `rad_pattern_p`, `rad_pattern_s` and `rad_patterns` overrides on `mag_sensitivity_grid`, so that results computed with another convention stay reproducible; pass `rad_pattern_s=0.63` to use the combined S-wave value
- receiver projection from the arriving polarization vectors, through `get_phase_station_directionality`, which is correct for inclined and curved cables rather than only for a vertical one
- projection of single vertical-component stations onto the vertical axis, driven by a `Components` column; three-component stations record the full vector and are unaffected
- per-station free surface amplification through `compute_free_surface_coefficients`, with `fs_mode`, `fs_level` and `fs_deviation` parameters and an optional `Surface` column carrying per-station weights
- helpers `normalize_wave_mode`, `wave_mode_phases`, `wave_mode_has_p`, `wave_mode_has_s`, `wave_mode_s_phases`, `resolve_radiation_pattern`, `check_min_stations` and `geometry_requires_receiver_projection`
- test modules covering wave modes and radiation patterns, receiver projection, the free surface correction, network detectability, and phase-resolved sensitivity end to end

### Changed

- **S-wave results differ from 1.0.x.** The S branch now uses the phase-resolved radiation patterns instead of the combined value 0.63, which raises S-wave thresholds by `2/3*log10(0.63/sqrt(7/30))`, about 0.077 magnitude units. Pass `rad_pattern_s=0.63` to recover the previous behaviour
- **the free surface correction is applied per receiver.** In 1.0.x `free_surface=True` amplified every receiver irrespective of its depth; it now applies only to receivers at the free surface, so geometries mixing surface and downhole receivers are treated correctly. The default mode is `'auto'`, which derives the indicator from the receiver depths or from the `Surface` column when present
- `DetectionParameters` takes `fs_mode`, `fs_level` and `fs_deviation`; the `free_surface` flag is deprecated but still accepted, mapping to `fs_mode='on'` or `'off'`
- `mag_detectable` accepts the phase-resolved wave modes
- receiver projection is decided from the geometry itself, so `use_station_directionality` is only needed to force tangent projection for a station geometry

### Removed

- the `rays_p` and `rays_s` arguments of `get_ray_station_directionality`, which could never be populated because the homogeneous package has no ray tracer. The function is deprecated in favour of `get_phase_station_directionality` and now emits a `DeprecationWarning`

### Fixed

- the station-count guard in `mag_detectable` compared against the grid axis instead of the station axis, so a request for more receivers than the geometry has was not reported clearly

## [v1.0.1] - 2026-09-10

Bugfix release correcting the seismic moment calculation.

### Fixed

- the seismic moment is no longer underestimated by a factor of `2*pi*f` (#3). `calculate_M0` applied the amplitude-to-displacement spectral conversion a second time, after `retrieve_min_amps` had already applied it through `get_scaling_displacement`. Minimum detectable moment magnitudes reported by v1.0.0 were therefore too low by `dMw = (2/3)*log10(2*pi*f_r)`, which is 1.20 at a representative frequency of 10 Hz and 1.87 at 100 Hz. Because the representative frequency `f_r = min(v*Q/(pi*r), f_c)` depends on the source-receiver distance, the correction varies across the grid and changes the shape of the sensitivity maps, not only their colour scale
- `pynetdesign.visualization` can be imported on Python 3.9 again; `plot_sensitivity_slice` used a `match` statement, which is syntax available only from Python 3.10 onwards

### Changed

- `calculate_M0` now documents the seismic moment relation it evaluates and states that the amplitudes it takes are the displacement amplitude spectrum, with units given for the remaining arguments

### Removed

- `loc_uncertainty_grid`, which called `calculate_pdf` and `get_uncertainty_from_pdf`. Neither function has ever been part of the package, so every call raised `NameError`. Location uncertainty will be reintroduced later together with the functions it depends on

### Added

- `pytests/test_magnitude.py`, covering the seismic moment relation, the moment magnitude conversion and its inverse, the amplitude-type scaling coefficients, the peak frequency and its corner-frequency clamp, and the DAS strain and strain-rate detection thresholds. The closed-form checks fail on the v1.0.0 formula and so guard against a recurrence of #3

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

[Unreleased]: https://github.com/danikiev/PyNetDesign/compare/v1.0.1...HEAD
[v1.0.1]: https://github.com/danikiev/PyNetDesign/compare/v1.0.0...v1.0.1
[v1.0.0]: https://github.com/danikiev/PyNetDesign/releases/tag/v1.0.0
