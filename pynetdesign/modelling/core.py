from pynetdesign.modelling.classes import *
from pynetdesign.modelling.utils import *
from pynetdesign.modelling.io import *

import pynetdesign.modelling.homo as homo

import numpy as np
import pandas as pd
import inspect

def get_mag_sensitivity_local(grid_coords: np.ndarray,
                              geometry_df: pd.DataFrame,
                              velocity_df: pd.DataFrame,
                              params: DetectionParameters,
                              wave_mode: str = 'PS',
                              strict_nan_check: bool = False):
    r"""
    Computes magnitude sensitivity using mag_sensitivity_grid for input local geometry,
    velocity and parameters. Checks if the input geometry is DAS, i.e. has a gauge length and
    uses directionality accordingly.

    Parameters
    ----------
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    geometry_df : :obj:`pandas.DataFrame`
        Geometry DataFrame
    velocity_df : :obj:`pandas.DataFrame`
        Velocity model DataFrame
    params : :obj:`pynetdesign.modelling.classes.DetectionParameters`
        Detection parameters
    wave_mode: :obj:`str`, optional, default: 'PS'
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'
    strict_nan_check: :obj:`bool`, optional, default: False
        flag to check if NaN values appear in the result

    Returns
    -------
    Mw_min_stations : :obj:`numpy.ndarray`
        Array of computed minimum moment magnitudes for individual stations

    Raises
    ------
    ValueError :
        if input velocity model is not homogeneous, i.e. contains more than one layer
    """
    # Validate parameters
    params.validate()

    # Get gauge length if exists
    gauge_length = geometry_df.attrs.get('gauge_length', None)

    # Receiver projection is decided from the geometry itself: a DAS geometry is
    # projected onto the local cable tangent and a single-component station onto
    # the vertical axis, so no explicit flag is needed here.

    # Get minimum detectable amplitudes
    min_amps_p, min_amps_s = retrieve_min_amps(geometry_df=geometry_df,
                                               SNR_p=params.min_SNR_p,
                                               SNR_s=params.min_SNR_s,
                                               f_p=params.f_p,
                                               f_s=params.f_s,
                                               sample_interval=gauge_length)
    # Get model type
    model_type = velocity_df.attrs['model_type']

    # Make processing based on velocity model type
    if model_type=='homo':

        # Double-check velocity model
        if len(velocity_df)>1:
            raise ValueError("Velocity model is not homogeneous!")

        # Get magnitude sensitivity for all stations
        Mw_min_stations = homo.mag_sensitivity_grid(grid_coords=grid_coords,
                                                    velocity_df=velocity_df,
                                                    geometry_df=geometry_df,
                                                    min_amps_p=min_amps_p,
                                                    min_amps_s=min_amps_s,
                                                    min_stations_p=params.min_stations_p,
                                                    min_stations_s=params.min_stations_s,
                                                    f_p=params.f_p,
                                                    f_s=params.f_s,
                                                    f_p_corner=params.f_p_corner,
                                                    f_s_corner=params.f_s_corner,
                                                    wave_mode=wave_mode,
                                                    fs_mode=params.fs_mode,
                                                    fs_level=params.fs_level,
                                                    fs_deviation=params.fs_deviation,
                                                    return_stations=True,
                                                    strict_nan_check=strict_nan_check)
    
    # Check for NaNs
    if strict_nan_check:
        if np.any(np.isnan(Mw_min_stations)):
            current_function = inspect.currentframe().f_code.co_name
            raise RuntimeError(f"Error in function {current_function}: NaN values detected while computing the magnitude sensitivity")

    return Mw_min_stations

def get_mag_sensitivity(grid_coords: np.ndarray,
                        geometry_df: pd.DataFrame,
                        velocity_df: pd.DataFrame,
                        params: DetectionParameters,
                        wave_mode: str = 'PS',
                        strict_nan_check: bool = False):
    r"""
    Computes detectable magnitude sensitivity for input geometry, velocity and parameters.
    It also deals with combined geometries.

    Parameters
    ----------
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    geometry_df : :obj:`pandas.DataFrame`
        Geometry DataFrame
    velocity_df : :obj:`pandas.DataFrame`
        Velocity model DataFrame
    params : :obj:`pynetdesign.modelling.classes.DetectionParameters`
        Detection parameters
    wave_mode: :obj:`str`, optional, default: 'PS'
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'
    strict_nan_check: :obj:`bool`, optional, default: False
        flag to check if NaN values appear in the result

    Returns
    -------
    Mw_min_grid : :obj:`numpy.ndarray`
        Array of computed detectable minimum moment magnitudes on the grid
    """
    # Check if it is a combined geometry or not
    if is_combined_geometry(geometry_df):
        geometry_names = geometry_df.get_names()
        Mw_min_stations_list = []

        # Loop over geometries
        for geometry in geometry_names:
            Mw_min_stations_local = get_mag_sensitivity_local(grid_coords=grid_coords,
                                                              geometry_df=geometry_df.recover(geometry),
                                                              velocity_df=velocity_df,
                                                              params=params,
                                                              wave_mode=wave_mode,
                                                              strict_nan_check=strict_nan_check)
            Mw_min_stations_list.append(Mw_min_stations_local)

        # Concatenate along the last third dimension (axis=2)
        Mw_min_stations = np.concatenate(Mw_min_stations_list, axis=2)
    else:
        Mw_min_stations = get_mag_sensitivity_local(grid_coords=grid_coords,
                                                    geometry_df=geometry_df,
                                                    velocity_df=velocity_df,
                                                    params=params,
                                                    wave_mode=wave_mode,
                                                    strict_nan_check=strict_nan_check)

    # Get detectable minimum magnitudes
    Mw_min_grid = mag_detectable(Mw_min_stations=Mw_min_stations,
                                 min_stations_p=params.min_stations_p,
                                 min_stations_s=params.min_stations_s,
                                 wave_mode=wave_mode)

    # Check for NaNs
    if strict_nan_check:
        if np.any(np.isnan(Mw_min_grid)):
            current_function = inspect.currentframe().f_code.co_name
            raise RuntimeError(f"Error in function {current_function}: NaN values detected while computing the magnitude sensitivity")

    return Mw_min_grid
