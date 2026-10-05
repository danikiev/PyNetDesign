from typing import Union, Optional
from pynetdesign.modelling.classes import *
from pynetdesign.modelling.utils import *
from pynetdesign.modelling.io import *

import numpy as np
import pandas as pd
import inspect

def mag_sensitivity_grid(grid_coords: np.ndarray,
                         velocity_df: pd.DataFrame,
                         geometry_df: pd.DataFrame = None,
                         station_coords: np.ndarray = None,
                         min_amps_p: np.ndarray = None,
                         min_amps_s: np.ndarray = None,
                         min_stations_p: int = None,
                         min_stations_s: int = None,
                         rad_pattern_p: float = None,
                         rad_pattern_s: float = None,
                         rad_patterns: dict = None,
                         f_p: float = None,
                         f_s: float = None,
                         f_p_corner: float = None,
                         f_s_corner: float = None,
                         wave_mode: str = 'PS',
                         fs_mode: str = 'auto',
                         fs_level: float = None,
                         fs_deviation: float = None,
                         use_station_directionality: bool = False,
                         return_stations: bool = False,
                         strict_nan_check: bool = False,
                         amps_type: str = None):

    r"""
    Computes magnitude sensitivity - the minimum moment magnitude (Mw) of a microseismic event
    which will theoretically produce particle velocity amplitudes (of P and/or S waves)
    on stations necessary for event detection assuming 3D elastic homogeneous medium with attenuation.
    It takes into account minimum number of stations on which the event should be detected.
    By request it is possible to output only minimum moment magnitude for each station.

    Parameters
    ----------
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    velocity_df : :obj:`pandas.DataFrame`
        Velocity model DataFrame
    geometry_df : :obj:`pandas.DataFrame`, optional
        Geometry DataFrame, use if station_coords is None
    station_coords : :obj:`numpy.ndarray`, optional
        Array of station coordinates [[xr1, yr1, zr1], [xr2, yr2, zr2], ...], use if geometry_df is None
    min_amps_p : :obj:`numpy.ndarray`, optional
        Minimal measurable displacement amplitudes of on stations [a1, a2, ...] for P waves
    min_amps_s : :obj:`numpy.ndarray`, optional
        Minimal measurable displacement amplitudes on stations [a1, a2, ...] for S waves
    min_stations_p : :obj:`int`, optional, default: None (3)
        Minimum number of stations on which event must be detected with P waves
    min_stations_s : :obj:`int`, optional, default: None (3)
        Minimum number of stations on which event must be detected with S waves
    rad_pattern_p : :obj:`float`, optional
        Override of the radiation pattern factor for P waves.
        If ``None``, the root-mean-square value :math:`\sqrt{4/15} \approx 0.52` is used.
    rad_pattern_s : :obj:`float`, optional
        Override of the radiation pattern factor applied to both S phases.
        If ``None``, the root-mean-square values :math:`\sqrt{7/30} \approx 0.48` for SV
        and :math:`\sqrt{1/6} \approx 0.41` for SH are used. Pass 0.63 to reproduce
        results computed with the combined S-wave value.
    rad_patterns : :obj:`dict`, optional
        Per-phase overrides of the radiation pattern factor, e.g. ``{'SV': 0.63}``.
        Takes precedence over ``rad_pattern_p`` and ``rad_pattern_s``.
    f_p : :obj:`float`, optional
        Frequency of the P wave (Hz)
    f_s : :obj:`float`, optional
        Frequency of the S wave (Hz)
    f_p_corner : :obj:`float`, optional
        Corner frequency of the P wave (Hz)
    f_s_corner : :obj:`float`, optional
        Corner frequency of the S wave (Hz)
    wave_mode: :obj:`str`, optional, default: 'PS'
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'
    fs_mode : :obj:`str`, optional, default: 'auto'
        Free surface correction mode, can be 'auto', 'on' or 'off'.
        The correction accounts for the amplification of amplitudes recorded at the
        daily surface due to the free surface boundary condition, and is applied per
        station so that geometries mixing surface and downhole receivers are handled
        correctly. See :func:`~pynetdesign.modelling.utils.compute_free_surface_coefficients`.
    fs_level : :obj:`float`, optional, default: None (0.0)
        Level of the free surface in metres above the reference level.
    fs_deviation : :obj:`float`, optional, default: None (1.0)
        Permitted deviation from the free surface level in metres.
    use_station_directionality : :obj:`bool`, optional, default: False
        Force projection of the arriving polarization onto the local tangent defined by
        the adjacent stations. Projection is applied automatically for DAS geometries
        and for stations recording a single vertical component, so this is only needed
        to force tangent projection for a station geometry.
    return_stations : :obj:`bool`, optional, default: False
        Return magnitude sensitivity for each station, don't take into account detectability
    strict_nan_check: :obj:`bool`, optional, default: False
        flag to check if NaN values appear in the result
    amps_type : :obj:`str`, optional, default: None
        Type of amplitudes, can be 'displacement', 'velocity', 'acceleration', 'strain rate', 'strain'.

    Returns
    -------
    Mw_min_grid : :obj:`numpy.ndarray`
        Array of computed detectable minimum moment magnitudes on the grid, if return_stations = False
    Mw_min_stations : :obj:`numpy.ndarray`
        Array of computed minimum moment magnitudes for individual stations, if return_stations = True
        Mw_min_stations is of shape (2, npairs) where npairs is a number of of source-grid pairs
        determined from station_coords and grid_coords. First dimension corresponds to P and S waves.

    Raises
    ------
    ValueError :
        if both station_coords and geometry_df are not None or None
    ValueError :
        if there is inconsistency in P/S wave parameters
    ValueError :
        if number of minimal measurable amplitudes do not match number of stations
    ValueError :
        if density, wave velocity or attenuation factor is not positive
    ValueError :
        if radiation pattern factor for P or S wave is less or equal to 0 or higher than 1
    ValueError :
        if number of minimal measurable amplitudes does not match number of stations
    RuntimeError :
        if strict_nan_check is True and NaN appears in the result

    Notes
    -----
    This is a refactored vectorized version of the code
    """

    if (station_coords is not None and geometry_df is not None) or (station_coords is None and geometry_df is None):
        raise ValueError("You must provide either `station_coords` or `geometry_df`, but not both.")

    # Get station coordinates from geometry
    if station_coords is None:
        station_coords = geometry_df[['X', 'Y', 'Z']].to_numpy()

    # Get the free surface information from geometry, if provided
    if geometry_df is not None and 'Surface' in geometry_df.columns:
        station_coords_on_surface = geometry_df['Surface'].to_numpy()
    else:
        station_coords_on_surface = None

    # Handle the case if station_coords has only one point (3 elements)
    if station_coords.ndim == 1 and station_coords.size == 3:
        station_coords = station_coords[np.newaxis, :]  # reshape to (1, 3)

    # Handle the case if grid_coords has only one point (3 elements)
    if grid_coords.ndim == 1 and grid_coords.size == 3:
        grid_coords = grid_coords[np.newaxis, :]  # reshape to (1, 3)

    # Check if amplitudes type is provided
    if geometry_df is None:
        if amps_type is None:
            raise ValueError("You must provide amplitude type if geometry is not provided")
    else:
        amps_type = geometry_df.attrs.get('noise_type')

    # Check velocity model
    if len(velocity_df) != 1:
        raise ValueError("Velocity model is not homogeneous!")

    # Expand the wave mode into the phases that have to be evaluated
    wave_mode = normalize_wave_mode(wave_mode)
    phases = wave_mode_phases(wave_mode)
    s_phases = wave_mode_s_phases(wave_mode)

    # Check the free surface parameters
    if fs_level is None:
        fs_level = 0.0
    if fs_deviation is None:
        fs_deviation = 1.0
    elif fs_deviation < 0:
        raise ValueError("Free surface level deviation must be non-negative")
    if fs_mode not in ('auto', 'on', 'off'):
        raise ValueError("Free surface mode must be 'auto', 'on' or 'off'")

    # Retrieve medium parameters
    density = velocity_df.at[0,'Rho']
    v_p = velocity_df.at[0,'Vp']
    Q_p = velocity_df.at[0,'Qp']
    v_s = velocity_df.at[0,'Vp']/velocity_df.at[0,'VpVsRatio']
    Q_s = velocity_df.at[0,'Qs']

    # Validate parameters
    validate_parameters(density=density,
                        v_p=v_p,                        
                        v_s=v_s,
                        Q_s=Q_s,
                        Q_p=Q_p,
                        min_amps_p=min_amps_p,
                        min_amps_s=min_amps_s,
                        wave_mode=wave_mode,
                        station_coords=station_coords)

    # Check the minimum number of stations required for detection
    if not return_stations:
        check_min_stations(min_stations_p=min_stations_p,
                           min_stations_s=min_stations_s,
                           n_stations=len(station_coords),
                           wave_mode=wave_mode)

    # Precompute distances between all grid points and all stations
    # Shape: (n_grid_points, n_stations)
    distances = np.linalg.norm(grid_coords[:, np.newaxis] - station_coords, axis=2)
    if strict_nan_check:
        if np.any(distances == 0):
            raise ValueError("Zero distance: source and receiver must have different coordinates")

    # Calculate free surface correction coefficients, applied per station
    fs_coef_p, fs_coef_s = compute_free_surface_coefficients(station_coords=station_coords,
                                                             grid_coords=grid_coords,
                                                             station_coords_on_surface=station_coords_on_surface,
                                                             fs_mode=fs_mode,
                                                             fs_level=fs_level,
                                                             fs_deviation=fs_deviation)

    # Calculate receiver projection coefficients if needed. Projection applies
    # automatically to DAS geometries and to single-component stations.
    geometry_projection_required = geometry_requires_receiver_projection(geometry_df)
    if use_station_directionality or geometry_projection_required:
        directionality = get_phase_station_directionality(station_coords=station_coords,
                                                          grid_coords=grid_coords,
                                                          phases=phases,
                                                          geometry_df=geometry_df,
                                                          force_tangent=use_station_directionality and not geometry_projection_required,
                                                          strict_nan_check=strict_nan_check)
    else:
        # If not using projection, use ones (no effect on calculations)
        directionality = {phase: np.ones_like(distances) for phase in phases}

    # Helper function to calculate Mw_min for a given phase
    def calculate_Mw_min(f, fcorner, v, Q, phase, min_amps, fs_coef):
        M0 = calculate_M0(density=density,
                          v=v,
                          Q=Q,
                          rad_pattern=resolve_radiation_pattern(phase,
                                                                rad_pattern_p=rad_pattern_p,
                                                                rad_pattern_s=rad_pattern_s,
                                                                rad_patterns=rad_patterns),
                          r=distances,
                          amps = min_amps * directionality[phase] / fs_coef,
                          f=f,
                          fcorner=fcorner,
                          amps_type=amps_type)
        return calculate_Mw(M0)

    # Preallocate array for Mw_min calculations
    # Shape: (2, n_grid_points, n_stations) where index 0 is for P waves, 1 for S waves
    Mw_min_stations = np.full((2, *distances.shape), np.nan)

    # Calculate Mw_min for P waves if applicable
    if wave_mode_has_p(wave_mode):
        Mw_min_stations[0] = calculate_Mw_min(f=f_p,
                                              fcorner=f_p_corner,
                                              v=v_p,
                                              Q=Q_p,
                                              phase='P',
                                              min_amps=min_amps_p,
                                              fs_coef=fs_coef_p)

    # Calculate Mw_min for S waves if applicable. For the composite S mode the
    # more detectable of the SV and SH branches is kept, i.e. the smaller magnitude.
    if s_phases:
        mw_s = [calculate_Mw_min(f=f_s,
                                 fcorner=f_s_corner,
                                 v=v_s,
                                 Q=Q_s,
                                 phase=phase,
                                 min_amps=min_amps_s,
                                 fs_coef=fs_coef_s)
                for phase in s_phases]
        Mw_min_stations[1] = mw_s[0] if len(mw_s) == 1 else np.fmin(mw_s[0], mw_s[1])

    # Return depending on the request
    if return_stations:
        return Mw_min_stations
    else:
        Mw_min_grid = mag_detectable(Mw_min_stations=Mw_min_stations,
                                     min_stations_p=min_stations_p,
                                     min_stations_s=min_stations_s,
                                     wave_mode=wave_mode)
        # Check for NaNs
        if strict_nan_check:
            if np.any(np.isnan(Mw_min_grid)):
                current_function = inspect.currentframe().f_code.co_name
                raise RuntimeError(f"Error in function {current_function}: NaN values detected while computing the magnitude sensitivity")

        return Mw_min_grid

def calculate_fpeak(v: float,
                    Q: float,
                    r: float,
                    fcorner: float=None):
    r"""
    Calculates the peak frequency :math:`f_{peak}` for particle velocity
    in a homogeneous medium
    given the wave velocity :math:`v`,
    the attenuation factor :math:`Q`,
    and the distance from a source :math:`r` using:

    .. math::
        f_{peak} = \frac{vQ}{\pi r}.

    The peak frequency estimate is only valid for frequencies below the corner frequency :cite:p:`EisnerGeiEtAl2013`.

    Parameters
    ----------
    v : :obj:`float`
        wave velocity
    Q : :obj:`float`
        attenuation factor
    r : :obj:`float`
        distance from the source
    fcorner : :obj:`float`, optional, default: ``None``
        Corner frequency that limits the peak frequency.
        If ``None``, defaults to 100 Hz.

    References
    ----------
    Eisner, L., Gei, D., Hallo, M., Opršal, I., & Ali, M. Y. (2013).
    The peak frequency of direct waves for microseismic events.
    Geophysics, 78(6), A45–A49.
    https://doi.org/10.1190/geo2013-0197.1

    Returns
    -------
    fpeak : :obj:`float`
        Peak frequency for particle velocity
    """
    # Compute the peak frequency for particle velocity
    fpeak = v*Q/(np.pi*r)

    # Default corner frequency
    if fcorner is None:
        fcorner = 100

    # Limit to corner frequency
    fpeak = np.minimum(fpeak,fcorner)

    return fpeak

def calculate_M0(density: float,
                 v: float,
                 Q: float,
                 rad_pattern: float,
                 r: Optional[Union[float, np.ndarray]],
                 amps: Optional[Union[float, np.ndarray]],
                 f: float = None,
                 fcorner: float = None,
                 amps_type: str='displacement'):
    r"""
    Calculates the seismic moment :math:`M_0` in a homogeneous medium given the density :math:`\rho`, wave velocity :math:`v`, distance from the source :math:`r` and the displacement amplitude spectrum :math:`\left|U(f)\right|` using:

    .. math::
        M_0 = \frac{4 \pi \rho v^3 r}{\left|R\right|}\,\left|U(f)\right|\,e^{\pi f t^*},

    where :math:`R` is the provided radiation pattern factor and the exponential term corrects
    for the intrinsic attenuation accumulated along the ray path.

    The amplitudes passed in ``amps`` are the displacement amplitude spectrum
    :math:`\left|U(f)\right|`. Amplitudes of another type are converted to it with the
    coefficients of :func:`~pynetdesign.modelling.utils.get_scaling_displacement`, which
    follow from :math:`\left|V(f)\right| = 2 \pi f \left|U(f)\right|`.

    The term :math:`t^*` is the integral along the ray path of the inverse value of attenuation factor :math:`Q` multiplied by the inverse of the wave velocity :math:`v`:

    .. math::
        t^* = \int_R \frac{dr}{v(r) Q(r)},

    which in a homogenous medium reads as

    .. math::
        t^* = \frac{r}{vQ}.

    Frequency :math:`f` is the representative frequency of the wave.
    If it is not provided, it defaults to the peak frequency computed from the model,
    and limited by the corner frequency.

    Parameters
    ----------
    density : :obj:`float`
        Density (kg/m^3)
    v : :obj:`float`
        Wave velocity (m/s)
    Q : :obj:`float`
        Attenuation factor
    rad_pattern : :obj:`float`
        Radiation pattern factor
    r : :obj:`float` or :obj:`numpy.ndarray`
        Distance(s) from the source (m)
    amps : :obj:`float` or :obj:`numpy.ndarray`
        Displacement amplitude spectrum :math:`\left|U(f)\right|`, single value or array of
        amplitudes, one for each ray.
        If ``r`` is a single float, ``amps`` must be a single float
        If ``r`` is an array, ``amps`` must be an array of the same shape.
    f : :obj:`float`, optional, default: ``None``
        Frequency. If ``None``, peak frequency is computed from the model
    fcorner : :obj:`float`, optional, default: ``None``
        Corner frequency, limit for peak frequency.
    amps_type : :obj:`str`, optional, default: ``displacement``
        Type of amplitudes in ``amps``, can be 'displacement', 'velocity', 'acceleration', 'strain rate', 'strain'.
        Used for scaling of amplitudes in case ``f`` is ``None``.

    Returns
    -------
    M0 : :obj:`float` or array_like
        Seismic moment (N m)
    """
    # Check validity of 'r' and 'amps'
    if amps is None:
        raise ValueError("Missing amplitude values: 'amps' cannot be None.")

    if r is None:
        raise ValueError("Missing distances: 'r' cannot be None.")

    # Check shape and type consistency between 'r' and 'amps'
    r_is_array = isinstance(r, np.ndarray)
    amps_is_array = isinstance(amps, np.ndarray)

    if r_is_array and not amps_is_array:
        raise ValueError("If 'r' is an array, 'amps' must also be an array.")
    if not r_is_array and amps_is_array:
        raise ValueError("If 'r' is a float, 'amps' must also be a float.")
    if r_is_array and amps_is_array:
        if r.shape != amps.shape:
            raise ValueError("If 'r' is an array, 'amps' must have the same shape as 'r'.")

    # Default corner frequency
    if fcorner is None:
        fcorner = 100

    # Compute t*
    t_star = r / (v * Q)

    # Get peak frequency and amplitude scaling
    if f is None:
        # Get fpeak. A grid point that coincides with a receiver gives r = 0, hence
        # t* = 0 and an infinite peak frequency, which the clamp below turns into the
        # corner frequency. That is the intended answer, so the division is allowed to
        # reach infinity quietly rather than warning about it. Coincidence is easy to
        # hit with a dense DAS cable, where every channel sits on a grid line.
        with np.errstate(divide='ignore'):
            fpeak = 1/(np.pi*t_star)
        # Limit to corner frequency
        fpeak = np.minimum(fpeak,fcorner)
        # Final scaling coefficient(s)
        scaling = get_scaling_displacement(amps_type=amps_type,f=fpeak)
    else:
        fpeak = f
        scaling = 1.0

    # Precompute constants
    pif = np.pi * fpeak
    constant = 4 * np.pi * density * v**3 / rad_pattern

    # Compute exp(pi * f * t*)
    exp_term = np.exp(pif * t_star)

    # Compute seismic moment: M0 = (4 pi rho v^3 r / |R|) * |U(f)| * exp(pi f t*)
    M0 = constant * r * scaling * amps * exp_term

    return M0

def validate_parameters(density, v_p, v_s, Q_p, Q_s, min_amps_p, min_amps_s, wave_mode, station_coords):
    r"""
    Validates the input parameters.

    Parameters
    ----------
    density : :obj:`float`
        Density of the medium
    v_p : :obj:`float`
        P wave velocity
    v_s : :obj:`float`  
        S wave velocity
    Q_p : :obj:`float`
        P wave attenuation factor
    Q_s : :obj:`float`
        S wave attenuation factor
    min_amps_p : :obj:`numpy.ndarray`
        Minimal measurable displacement amplitudes of on stations [a1, a2, ...] for P waves
    min_amps_s : :obj:`numpy.ndarray`
        Minimal measurable displacement amplitudes on stations [a1, a2, ...] for S waves
    wave_mode: :obj:`str`
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'    
    station_coords : :obj:`numpy.ndarray`
        Array of station coordinates [[xr1, yr1, zr1], [xr2, yr2, zr2], ...]    

    Raises
    ------
    ValueError :
        if density, wave velocity or attenuation factor is not positive
    ValueError :
        if number of minimal measurable amplitudes does not match number of stations
    ValueError :
        if there is inconsistency in P/S wave parameters
    
    """
    # Check density
    if density <= 0:
        raise ValueError("Density must be positive.")
    if v_p is None and v_s is None:
        raise ValueError("Both P wave and S wave velocities can not be None.")
    if Q_p is None and Q_s is None:
        raise ValueError("Both P wave and S wave attenuation factors can not be None.")

    # Validate P wave parameters if applicable
    if wave_mode_has_p(wave_mode):
        if any(x <= 0 for x in (v_p, Q_p)):
            raise ValueError("P wave parameters must be positive.")
        if min_amps_p is None:
            raise ValueError("Invalid minimal measurable amplitudes for P waves.")
        if np.isscalar(min_amps_p):
            if len(station_coords)!=1:
                raise ValueError("Invalid minimal measurable amplitudes for P waves.")
        elif len(min_amps_p) != len(station_coords):
            raise ValueError("Invalid minimal measurable amplitudes for P waves.")

    # Validate S wave parameters if applicable
    if wave_mode_has_s(wave_mode):
        if any(x <= 0 for x in (v_s, Q_s)):
            raise ValueError("S wave parameters must be positive.")
        if min_amps_s is None:
            raise ValueError("Invalid minimal measurable amplitudes for S waves.")
        if np.isscalar(min_amps_s):
            if len(station_coords)!=1:
                raise ValueError("Invalid minimal measurable amplitudes for S waves.")
        elif len(min_amps_s) != len(station_coords):
            raise ValueError("Invalid minimal measurable amplitudes for S waves.")
