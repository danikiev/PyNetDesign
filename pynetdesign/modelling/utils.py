import numpy as np
import pandas as pd
import inspect
from fractions import Fraction
from math import gcd
from typing import Union, Optional
import warnings

VALID_WAVE_MODES = ("P", "SV", "SH", "S", "PS")
S_WAVE_PHASES = ("SV", "SH")

# Root-mean-square radiation-pattern magnitudes over the focal sphere of a
# double-couple source, after Boore and Boatwright (1984) and Hallo and Eisner
# (2013). Note that the frequently quoted value sqrt(2/5) ~ 0.63 is the combined
# S-wave magnitude, since <R_SV^2> + <R_SH^2> = 2/5, and therefore does not apply
# to SV or SH individually.
RAD_PATTERN_P_DEFAULT = float(np.sqrt(4.0 / 15.0))    # approx 0.516
RAD_PATTERN_SV_DEFAULT = float(np.sqrt(7.0 / 30.0))   # approx 0.483
RAD_PATTERN_SH_DEFAULT = float(np.sqrt(1.0 / 6.0))    # approx 0.408


def normalize_wave_mode(wave_mode: str) -> str:
    r"""
    Return the canonical form of a wave mode.

    ``'S'`` is a composite mode representing the better recorded of the two
    isotropic S polarizations, SV and SH.

    Parameters
    ----------
    wave_mode : :obj:`str`
        Wave mode, one of ``'P'``, ``'SV'``, ``'SH'``, ``'S'`` or ``'PS'``,
        in any letter case and with surrounding whitespace ignored.

    Returns
    -------
    mode : :obj:`str`
        Canonical upper-case wave mode.

    Raises
    ------
    ValueError
        If ``wave_mode`` is not one of the supported modes.
    """
    mode = str(wave_mode).strip().upper()
    if mode not in VALID_WAVE_MODES:
        raise ValueError(
            f"Invalid wave_mode '{wave_mode}'. Must be one of {VALID_WAVE_MODES}."
        )
    return mode


def wave_mode_phases(wave_mode: str) -> tuple:
    r"""
    Expand a wave mode into the physical phases that must be evaluated.

    Parameters
    ----------
    wave_mode : :obj:`str`
        Wave mode, see :func:`normalize_wave_mode`.

    Returns
    -------
    phases : :obj:`tuple` of :obj:`str`
        Phases to evaluate, drawn from ``'P'``, ``'SV'`` and ``'SH'``.
    """
    mode = normalize_wave_mode(wave_mode)
    if mode == "P":
        return ("P",)
    if mode in S_WAVE_PHASES:
        return (mode,)
    if mode == "S":
        return S_WAVE_PHASES
    return ("P", *S_WAVE_PHASES)


def wave_mode_has_p(wave_mode: str) -> bool:
    r"""Return whether ``wave_mode`` includes the P branch."""
    return "P" in wave_mode_phases(wave_mode)


def wave_mode_s_phases(wave_mode: str) -> tuple:
    r"""Return the S-family phases included in ``wave_mode``."""
    return tuple(phase for phase in wave_mode_phases(wave_mode) if phase in S_WAVE_PHASES)


def wave_mode_has_s(wave_mode: str) -> bool:
    r"""Return whether ``wave_mode`` includes any S-family branch."""
    return bool(wave_mode_s_phases(wave_mode))


def phase_radiation_pattern(phase: str) -> float:
    r"""
    Return the root-mean-square radiation-pattern magnitude of a phase.

    The values are averages over the focal sphere of a double-couple source
    :cite:p:`BooreBoatwright1984`, as used for microseismicity with random source
    orientations :cite:p:`HalloEisner2013`:

    .. math::
        R_P = \sqrt{4/15} \approx 0.52, \quad
        R_{SV} = \sqrt{7/30} \approx 0.48, \quad
        R_{SH} = \sqrt{1/6} \approx 0.41.

    Parameters
    ----------
    phase : :obj:`str`
        Phase, one of ``'P'``, ``'SV'`` or ``'SH'``.

    Returns
    -------
    rad_pattern : :obj:`float`
        Radiation-pattern magnitude of the phase.

    Raises
    ------
    ValueError
        If ``phase`` is a composite mode rather than a single phase.

    Notes
    -----
    The value :math:`\sqrt{2/5} \approx 0.63` often quoted for S-waves is the
    magnitude of the *combined* S-wave amplitude, since
    :math:`\langle R_{SV}^2 \rangle + \langle R_{SH}^2 \rangle = 2/5`, and is
    therefore not applicable to SV or SH individually.
    """
    phase = normalize_wave_mode(phase)
    if phase == "P":
        return RAD_PATTERN_P_DEFAULT
    if phase == "SV":
        return RAD_PATTERN_SV_DEFAULT
    if phase == "SH":
        return RAD_PATTERN_SH_DEFAULT
    raise ValueError("Radiation pattern is only defined for P, SV, and SH.")


def resolve_radiation_pattern(phase: str,
                              rad_pattern_p: float = None,
                              rad_pattern_s: float = None,
                              rad_patterns: dict = None) -> float:
    r"""
    Resolve the radiation-pattern magnitude to use for a phase.

    Overrides take precedence over the root-mean-square defaults of
    :func:`phase_radiation_pattern`, which makes it possible to reproduce results
    published with other conventions, for instance the combined S-wave value
    :math:`R_S = 0.63`.

    Parameters
    ----------
    phase : :obj:`str`
        Phase, one of ``'P'``, ``'SV'`` or ``'SH'``.
    rad_pattern_p : :obj:`float`, optional
        Override for the P phase. If ``None``, the default is used.
    rad_pattern_s : :obj:`float`, optional
        Override applied to both S phases. If ``None``, the defaults are used.
    rad_patterns : :obj:`dict`, optional
        Per-phase overrides, e.g. ``{'SV': 0.63}``. Takes precedence over
        ``rad_pattern_p`` and ``rad_pattern_s``.

    Returns
    -------
    rad_pattern : :obj:`float`
        Radiation-pattern magnitude to use.

    Raises
    ------
    ValueError
        If a resolved value is not in the interval (0, 1].
    """
    phase = normalize_wave_mode(phase)
    value = None
    if rad_patterns:
        normalized = {normalize_wave_mode(key): val for key, val in rad_patterns.items()}
        value = normalized.get(phase)
    if value is None:
        if phase == 'P':
            value = rad_pattern_p
        else:
            value = rad_pattern_s
    if value is None:
        return phase_radiation_pattern(phase)
    value = float(value)
    if not 0 < value <= 1:
        raise ValueError(f"Invalid radiation pattern factor for {phase}: {value}.")
    return value

def calculate_Mw(M0):
    r"""
    Calculates the moment magnitude :math:`M_w` according to :ref:`Kanamori (1977) <Kanamori1977_calculate_Mw>` using formula

    .. math::

        M_w = \frac{2}{3}\left(\log_{10}(M_0)-9.1\right)

    where :math:`M_0` is the seismic moment.

    Parameters
    ----------
    M0 : array_like
        seismic moment

    References
    ----------
    .. _Kanamori1977_calculate_Mw:

    Kanamori, H. (1977). The energy release in great earthquakes.
    Journal of Geophysical Research, 82(20), 2981–2987.
    https://doi.org/10.1029/jb082i020p02981

    Returns
    -------
    Mw : array_like
        moment magnitude

    Notes
    -----
    Replaces all non-positive values of M0 by nan

    """

    # Ensure input is a NumPy array
    M0 = np.asarray(M0)

    # Replace all non-positive values with NaN
    M0 = np.where(M0 <= 0, np.nan, M0)

    return 2/3 * (np.log10(M0) - 9.1)

def calculate_seismic_moment(Mw):
    r"""
    Calculates the seismic moment :math:`M_0` from moment magnitude :math:`M_w` according to :ref:`Kanamori (1977) <Kanamori1977_calculate_M0>`

    .. math::

        M_0 = 10^{\frac{3}{2} M_w + 9.1}

    where :math:`M_w` is the moment magnitude.

    Parameters
    ----------
    Mw : array_like
        moment magnitude

    References
    ----------
    .. _Kanamori1977_calculate_M0:

    Kanamori, H. (1977). The energy release in great earthquakes.
    Journal of Geophysical Research, 82(20), 2981–2987.
    https://doi.org/10.1029/jb082i020p02981

    Returns
    -------
    M0 : array_like
        seismic moment
    """

    # Ensure input is a NumPy array
    Mw = np.asarray(Mw)

    # Compute moment
    M0 = 10**((3/2)*Mw + 9.1)

    return M0

def reshape_data(data: np.ndarray,
                 x: np.ndarray,
                 y: np.ndarray):
    r"""
    Reshape data to 2D array using axes vectors.

    Parameters
    ----------
    data : :obj:`numpy.ndarray`
        1D data array to be reshaped
    x : :obj:`numpy.ndarray`
        x axis vector
    y : :obj:`numpy.ndarray`
        y axis vector

    Returns
    -------
    reshaped_data : :obj:`numpy.ndarray`
        2D reshaped data array

    Raises
    ------
    ValueError
        when data array is not 1D
    """
    if data.ndim!=1:
        raise ValueError("Input data array must be 1D!")
    else:
        return np.reshape(data, (len(x), len(y)))

def generate_grid(x: np.ndarray,
                  y: np.ndarray,
                  z: np.ndarray):
    r"""
    From the grid vectors x,y,z generates an array of grid point coordinates of size (nx*ny*nz,3).

    Parameters
    ----------
    x : :obj:`numpy.ndarray`
        x axis grid vector
    y : :obj:`numpy.ndarray`
        y axis grid vector
    z : :obj:`numpy.ndarray`
        z axis grid vector

    Returns
    -------
    grid_points : :obj:`numpy.ndarray`
        2D grid coordinates array
    """
    # Generate the grid points
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    # Flatten the grid points into an array of coordinates
    grid_points = np.vstack([X.ravel(), Y.ravel(), Z.ravel()]).T

    return grid_points

def reshape_grid(grid_array: np.ndarray,
                 nx: int,
                 ny: int,
                 nz: int):
    r"""
    Reshape a flat grid array into a multidimensional array based on the provided grid vectors.

    Parameters
    ----------
    grid_array : :obj:`numpy.ndarray`
        The flat grid array to reshape. The first dimension should match the total number of grid points.
    nx : :obj:`numpy.int`
        Number of grid points along the x axis.
    ny : :obj:`numpy.int`
        Number of grid points along the y axis.
    nz : :obj:`numpy.int`
        Number of grid points along the z axis.

    Raises
    ------
    ValueError :
        If the number of grid points does not match the product of nx, ny, and nz.

    Returns
    -------
    reshaped_array : :obj:`numpy.ndarray`
        The reshaped array with shape (nx, ny, nz, ...), where "..." corresponds to the remaining dimensions of the input array.
    """
    # Calculate the target shape
    target_shape = (nx, ny, nz) + grid_array.shape[1:]

    # Reshape the array
    try:
        reshaped_array = grid_array.reshape(target_shape)
    except ValueError:
        raise ValueError(
            f"Cannot reshape grid_array with shape {grid_array.shape} to target shape {target_shape}. "
            "Ensure the number of grid points matches the product of nx, ny, and nz."
        )

    return reshaped_array

def are_points_inside(grid_coords1, grid_coords2):
    r"""Check if all points in ``grid_coords1`` are inside ``grid_coords2``.

    This function checks whether all points in the array ``grid_coords1`` are also present in the array ``grid_coords2``.
    Both arrays should have a shape of ``(n, 3)``, where each row represents a 3D coordinate.

    Parameters
    ----------
    grid_coords1 : :obj:`numpy.ndarray`
        A 2D array of shape (n_grid1, 3) representing the points to check.
    grid_coords2 : :obj:`numpy.ndarray`
        A 2D array of shape (n_grid2, 3) representing the reference points.

    Returns
    -------
    :obj:`bool`
        ``True`` if all points in ``grid_coords1`` are found in ``grid_coords2``, ``False`` otherwise.

    Raises
    ------
    ValueError
        If ``grid_coords1`` or ``grid_coords2`` does not have the required shape of ``(n, 3)``.

    Examples
    --------
    >>> grid_coords1 = np.array([[1, 2, 3], [4, 5, 6]])
    >>> grid_coords2 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> are_points_inside(grid_coords1, grid_coords2)
    True

    >>> grid_coords1 = np.array([[1, 2, 3], [10, 11, 12]])
    >>> grid_coords2 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> are_points_inside(grid_coords1, grid_coords2)
    False
    """
    # Validate input shapes
    if grid_coords1.shape[1] != 3 or grid_coords2.shape[1] != 3:
        raise ValueError("Both input arrays must have a shape of (n, 3).")

    # Convert grid_coords2 to a set of tuples for efficient lookup
    grid_coords2_set = set(map(tuple, grid_coords2))

    # Check if all points in grid_coords1 are in grid_coords2
    return all(tuple(point) in grid_coords2_set for point in grid_coords1)

def find_indices_of_points(grid_coords1, grid_coords2):
    r"""Find indices of points in ``grid_coords1`` that are inside ``grid_coords2``.

    This function finds the indices of points in ``grid_coords1`` that are also present in ``grid_coords2``.

    Parameters
    ----------
    grid_coords1 : :obj:`numpy.ndarray`
        A 2D array of shape ``(n_grid1, 3)`` representing the points to check.
    grid_coords2 : :obj:`numpy.ndarray`
        A 2D array of shape ``(n_grid2, 3)`` representing the reference points.

    Returns
    -------
    indices : :obj:`numpy.ndarray`
        An array of indices corresponding to the points in ``grid_coords1`` that are found in ``grid_coords2``.

    Raises
    ------
    ValueError
        If ``grid_coords1`` or ``grid_coords2`` does not have the required shape of ``(n, 3)``.

    Examples
    --------
    >>> grid_coords1 = np.array([[1, 2, 3], [4, 5, 6], [10, 11, 12]])
    >>> grid_coords2 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    >>> find_indices_of_points(grid_coords1, grid_coords2)
    array([0, 1])
    """
    # Validate input shapes
    if grid_coords1.shape[1] != 3 or grid_coords2.shape[1] != 3:
        raise ValueError("Both input arrays must have a shape of (n, 3).")

    # Convert grid_coords2 to a set of tuples for efficient lookup
    grid_coords2_set = set(map(tuple, grid_coords2))

    # Find indices of points in grid_coords1 that are in grid_coords2
    indices = [i for i, point in enumerate(grid_coords1) if tuple(point) in grid_coords2_set]

    return np.array(indices, dtype=int)


def get_slice_coordinates(grid_points: np.ndarray,
                          slice_dimension: int,
                          slice_coordinate: float):
    r"""
    From the array of grid point coordinates of size (nx*ny*nz,3) retrieve coordinates
    of the slice plane at a given slice coordinate in a given slice dimension.

    Parameters
    ----------
    grid_points : :obj:`numpy.ndarray`
        2D grid coordinates array
    dimension : :obj:`int`
        integer defining the desired slice dimension (0,1 or 2)
    slice_coordinate : :obj:`numpy.ndarray`
        coordinate of the slice to extract in the desired dimension

    Returns
    -------
    plane_points : :obj:`numpy.ndarray`
        2D slice plane coordinates array
    indices : :obj:`numpy.ndarray`
        Indices of plane_points in grid_points

    Raises
    ------
    ValueError
        when slice_dimension is not 0, 1 or 2
    RuntimeError
        when slice can't be extracted (slice coordinate does not coincide with the grid)
    """
    if slice_dimension not in range(3):
        raise ValueError("Slice dimension must be 0,1 or 2. Wrong dimension: " + str(slice_dimension))

    # Find indices where the slice condition is true
    indices = np.where(grid_points[:, slice_dimension] == slice_coordinate)[0]

    # Get coordinates of the slice plane using the indices
    plane_points = grid_points[indices]

    # Check output
    if plane_points.size == 0:
        raise RuntimeError("Slice could not be extracted, check slice coordinate: " + str(slice_coordinate))

    return plane_points, indices

def nth_minimum(arr: np.ndarray, n: int) -> np.ndarray:
    r"""
    Find the n-th minimum value in each row of a given 2D numpy array.

    Parameters
    ----------
    arr : :obj:`numpy.ndarray`
        A 2D numpy array of shape (i, j) where i is the number of rows (features)
        and j is the number of columns (samples).
    n : :obj:`int`
        The order of the minimum value to find (1-based index). For example, if n=2,
        the function finds the 2nd minimum value in each row.

    Returns
    -------
    nth_min_values : :obj:`numpy.ndarray`
        A 1D numpy array of shape (i,) containing the n-th minimum value from each row.

    Raises
    ------
    ValueError
        If n is less than 1 or greater than the number of columns in the array.
    """
    if n < 1 or n > arr.shape[1]:
        raise ValueError("n must be between 1 and the number of columns in the array.")

    # Partially sort each row to get the n-th minimum value
    partitioned_arr = np.partition(arr, n-1, axis=1)

    # Extract the n-th minimum value (zero-based index, so n-1)
    nth_min_values = partitioned_arr[:, n-1]

    return nth_min_values

def check_zero_values(a: float, ErrorMessage: str=None):
    r"""
    Check if the input value is close to zero and raise an error if true.

    Parameters
    ----------
    a : :obj:`float` or array_like
        The input value or values to be checked.
    ErrorMessage : :obj:`str` , optional
        Custom error message to be raised if the value is close to zero.
        Default is "Array values are close to zero".

    Returns
    -------
    bool
        Returns True if the value is not close to zero.

    Raises
    ------
    RuntimeError
        If the value is close to zero, raises a RuntimeError with the provided or default error message.

    Examples
    --------
    >>> check_zero_values(0.0000001)
    RuntimeError: Array values are close to zero

    >>> check_zero_values(1.0)
    True
    """
    if ErrorMessage is None:
        ErrorMessage = "Array values are close to zero"
    if np.any(np.isclose(a,0)):
        raise RuntimeError(ErrorMessage)
    else:
        return True

def contains_only_numeric(seq):
    r"""
    Check if a sequence (tuple, list, or numpy array) contains only numeric values.

    Parameters
    ----------
    seq : :obj:`tuple`, :obj:`list`, or :obj:`numpy.ndarray`
        The sequence to be checked.

    Returns
    -------
    bool
        True if all elements in the sequence are numeric (int, float, or complex), False otherwise.

    Examples
    --------
    >>> t1 = (1, 2.5, 3+4j)
    >>> contains_only_numeric(t1)
    True

    >>> l1 = [1, 2.5, 3]
    >>> contains_only_numeric(l1)
    True

    >>> a1 = np.array([1, 2.5, 3+4j])
    >>> contains_only_numeric(a1)
    True

    >>> t2 = (1, 'a', 2.5)
    >>> contains_only_numeric(t2)
    False
    """
    if isinstance(seq, (tuple, list, np.ndarray)):
        return all(isinstance(i, (int, float, complex)) for i in seq)
    else:
        raise TypeError("Input must be a tuple, list, or numpy.ndarray")

def compute_gcd_of_floats(rx, ry, rz):
    r"""
    Computes the greatest common divisor (GCD) of three positive float values.

    Parameters
    ----------
    rx : :obj:`float`
        First float value.
    ry : :obj:`float`
        Second float value.
    rz : :obj:`float`
        Third float value.

    Returns
    -------
    :obj:`float`
        The GCD of the three float values.

    """
    # Convert floats to Fractions for exact arithmetic
    frac_rx = Fraction(rx).limit_denominator()
    frac_ry = Fraction(ry).limit_denominator()
    frac_rz = Fraction(rz).limit_denominator()

    # Extract numerators and denominators
    num_rx, den_rx = frac_rx.numerator, frac_rx.denominator
    num_ry, den_ry = frac_ry.numerator, frac_ry.denominator
    num_rz, den_rz = frac_rz.numerator, frac_rz.denominator

    # Compute GCD of numerators
    gcd_num = gcd(gcd(num_rx, num_ry), num_rz)

    # Compute LCM of denominators
    def lcm(a, b):
        return abs(a * b) // gcd(a, b)

    lcm_den = lcm(den_rx, lcm(den_ry, den_rz))

    # Compute GCD as a Fraction
    gcd_fraction = Fraction(gcd_num, lcm_den)

    # Return the GCD as a float
    return float(gcd_fraction)

def get_scaling_displacement(amps_type: str,
                             f: Optional[Union[float, np.ndarray]]):
    r"""
    Get scaling coefficient(s) to convert to the amplitudes to displacement
    provided the type of original amplitudes and the frequency (or array of frequencies).
    If f is an array and is used for computation of scaling, output is also an array of the same size.

    Parameters
    ----------
    amps_type : :obj:`str`
        Type of amplitudes, can be 'displacement', 'velocity', 'acceleration', 'strain rate', 'strain'.
    f : :obj:`float` or :obj:`np.ndarray`
        Frequency or array of frequencies.

    Raises
    ------
    ValueError
        If ``amps_type`` is not one of the supported types.

    Returns
    -------
    scaling : :obj:`float` or :obj:`np.ndarray`
        Resulting scaling coefficient.
    """
    fscaling = 2 * np.pi * f
    if amps_type == 'displacement':
        scaling = 1
    elif amps_type == 'velocity':
        scaling = 1 / fscaling
    elif amps_type == 'acceleration':
        scaling = 1 / fscaling**2
    elif amps_type == 'strain rate':
        scaling = 1 / fscaling
    elif amps_type == 'strain':
        scaling = 1
    else:
        raise ValueError(f"Unsupported amplitude type: {amps_type}")

    return scaling

def retrieve_min_amps(geometry_df: pd.DataFrame,
                      SNR_p: float,
                      SNR_s: float,
                      f_p: float=None,
                      f_s: float=None,
                      sample_interval: float=None):
    r"""
    Retrieve minimum amplitudes for P and S waves from geometry data,
    scaled based on noise type.

    This function takes geometry data frame with noise levels, then scales these
    noise levels based on the noise type to displacement
    using the provided frequencies for P and S waves (optional),
    and applies SNR scaling for P and S waves.

    Parameters
    ----------
    geometry_df : :obj:`pandas.DataFrame`
        The path to the input CSV (ASCII) file containing the geometry data.
    SNR_p : :obj:`float`
        Signal-to-Noise Ratio for P waves
    SNR_s : :obj:`float`
        Signal-to-Noise Ratio for S waves
    f_p: :obj:`float`, optional, default: ``None``
        Frequency of the P-wave.
        If ``None``, scaling is postponed to be later done with peak frequency
    f_s: :obj:`float`, optional, default: ``None``
        Frequency of the S-wave.
        If ``None``, scaling is postponed to be later done with peak frequency
    sample_interval : :obj:`float`
        Interval along the cable at which strain measurements are made

    Returns
    -------
    min_amps_p : :obj:`numpy.ndarray`
        Minimum displacement amplitudes for P waves
    min_amps_s : :obj:`numpy.ndarray`
        Minimum displacement amplitudes for S waves

    Raises
    ------
    ValueError
        If an unsupported noise type is encountered.
    ValueError
        If the 'NoiseLevel' column is missing in geometry_df.
    ValueError
        If the sample_interval is None for strain and strain rate noise types
    """
    # Check if 'NoiseLevel' column exists
    if 'NoiseLevel' not in geometry_df.columns:
        raise ValueError("The 'NoiseLevel' column is missing from the geometry data.")

    # Get the noise levels and type
    noise_levels = geometry_df['NoiseLevel'].to_numpy()
    noise_type = geometry_df.attrs.get('noise_type')

    # Check sample_interval
    if (noise_type == 'strain rate' or noise_type == 'strain') and sample_interval is None:
        raise ValueError(f"Sample interval must be provided for {noise_type} data type." )

    # Scale noise levels to displacement based on noise type
    if f_p is None:
        scaling_p = 1 # scaling will be done later using peak frequency
    else:
        scaling_p = get_scaling_displacement(amps_type=noise_type,f=f_p)

    if f_s is None:
        scaling_s = 1 # scaling will be done later using peak frequency
    else:
        scaling_s = get_scaling_displacement(amps_type=noise_type,f=f_s)

    # Apply sample interval for strain and strain rate
    if noise_type == 'strain rate' or noise_type == 'strain':
        scaling_p *= sample_interval
        scaling_s *= sample_interval

    # Calculate final minimum amplitudes for P and S waves by applying scaling and SNR
    min_amps_p = noise_levels * scaling_p * SNR_p
    min_amps_s = noise_levels * scaling_s * SNR_s

    return min_amps_p, min_amps_s

def mag_detectable(Mw_min_stations: np.ndarray,
                   min_stations_p: int = None,
                   min_stations_s: int = None,
                   wave_mode: str = 'PS'):
    r"""
    Computes detectable minimum magnitudes from magnitude sensitivities for individual stations
    with respect to number of stations necessary for event detection using P and/or S waves.

    Parameters
    ----------
    Mw_min_stations : :obj:`numpy.ndarray`
        Array of computed minimum magnitudes for individual stations
    min_stations_p : :obj:`int`, optional, default: 3
        Minimum number of stations on which event must be detected with P waves
    min_stations_s : :obj:`int`, optional, default: 3
        Minimum number of stations on which event must be detected with S waves
    wave_mode: :obj:`str`, optional, default: 'PS'
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'

    Returns
    -------
    Mw_min_grid : :obj:`numpy.ndarray`
        Array of detectable minimum magnitudes on the grid

    Raises
    ------
    ValueError :
        if minimum number of stations on which event must be detected with P or S waves is less than 1 or exceeds number of stations
    """
    wave_mode = normalize_wave_mode(wave_mode)

    if min_stations_p is None:
        min_stations_p = 3
    if min_stations_s is None:
        min_stations_s = 3

    # Number of stations is the last axis of the (2, n_grid_points, n_stations) array
    check_min_stations(min_stations_p=min_stations_p,
                       min_stations_s=min_stations_s,
                       n_stations=Mw_min_stations.shape[2],
                       wave_mode=wave_mode)

    # Compute final Mw_min_grid based on wave mode
    if wave_mode == 'P':
        # For P waves, find the nth smallest value (where n = min_stations_p)
        Mw_min_grid = np.partition(Mw_min_stations[0], min_stations_p - 1, axis=1)[:, min_stations_p - 1]
    elif wave_mode in ('S', 'SV', 'SH'):
        # For S waves, find the nth smallest value (where n = min_stations_s)
        Mw_min_grid = np.partition(Mw_min_stations[1], min_stations_s - 1, axis=1)[:, min_stations_s - 1]
    else:  # wave_mode == 'PS'
        # For both P and S waves, find the maximum of the nth smallest values for each
        Mw_min_grid_p = np.partition(Mw_min_stations[0], min_stations_p - 1, axis=1)[:, min_stations_p - 1]
        Mw_min_grid_s = np.partition(Mw_min_stations[1], min_stations_s - 1, axis=1)[:, min_stations_s - 1]
        Mw_min_grid = np.maximum(Mw_min_grid_p, Mw_min_grid_s)

    return Mw_min_grid

def check_min_stations(min_stations_p: int,
                       min_stations_s: int,
                       n_stations: int,
                       wave_mode: str = 'PS'):
    r"""
    Check that the minimum numbers of stations required for detection are valid.

    Parameters
    ----------
    min_stations_p : :obj:`int`
        Minimum number of stations on which event must be detected with P waves.
    min_stations_s : :obj:`int`
        Minimum number of stations on which event must be detected with S waves.
    n_stations : :obj:`int`
        Total number of stations in the geometry.
    wave_mode : :obj:`str`, optional, default: ``'PS'``
        Wave mode to use, can be 'P', 'SV', 'SH', 'S' or 'PS'.

    Raises
    ------
    ValueError
        If a minimum number of stations is not positive or exceeds the number of stations.

    Notes
    -----
    Each of ``min_stations_p`` and ``min_stations_s`` is checked only if it is not
    ``None`` and only if the corresponding branch is part of ``wave_mode``.
    """
    wave_mode = normalize_wave_mode(wave_mode)
    if wave_mode_has_p(wave_mode) and min_stations_p is not None:
        if min_stations_p <= 0:
            raise ValueError("Minimum number of stations on which event must be detected with P waves must be positive.")
        if min_stations_p > n_stations:
            raise ValueError("Minimum number of stations on which event must be detected with P waves must not exceed number of stations.")
    if wave_mode_has_s(wave_mode) and min_stations_s is not None:
        if min_stations_s <= 0:
            raise ValueError("Minimum number of stations on which event must be detected with S waves must be positive.")
        if min_stations_s > n_stations:
            raise ValueError("Minimum number of stations on which event must be detected with S waves must not exceed number of stations.")


def compute_free_surface_coefficients(station_coords: np.ndarray,
                                      grid_coords: np.ndarray,
                                      station_coords_on_surface: np.ndarray = None,
                                      fs_mode: str = 'auto',
                                      fs_level: float = 0.0,
                                      fs_deviation: float = 1.0):
    r"""
    Compute free surface amplification coefficients for each station and grid point.

    A receiver recording at the free surface sees an amplitude approximately twice
    that of the incident wave, which is the exact amplification for normal or
    near-normal incidence. The coefficient is applied per station, so that a
    geometry combining surface receivers with receivers at depth is treated
    correctly.

    Parameters
    ----------
    station_coords : :obj:`numpy.ndarray`
        Array of station coordinates [[xr1, yr1, zr1], [xr2, yr2, zr2], ...]
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    station_coords_on_surface : :obj:`numpy.ndarray`, optional
        Per-station indicator of whether the station is on the free surface, as a
        1D array of the same length as the number of stations, with values in
        [0, 1]. Values between 0 and 1 act as a weighting factor between no
        amplification and full amplification. If ``None``, the indicator is
        derived from the station depths.
    fs_mode : :obj:`str`, optional, default: ``'auto'``
        Free surface correction mode, can be ``'auto'``, ``'on'`` or ``'off'``.
        If ``'on'``, the correction is applied to stations close to the free
        surface irrespective of ``station_coords_on_surface``. If ``'off'``, the
        correction is never applied. If ``'auto'``, ``station_coords_on_surface``
        is used when available, otherwise stations are considered to be on the
        free surface when their Z coordinate deviates from the free surface level
        by no more than ``fs_deviation``.
    fs_level : :obj:`float`, optional, default: 0.0
        Level of the free surface in metres above the reference level.
    fs_deviation : :obj:`float`, optional, default: 1.0
        Permitted deviation from the free surface level in metres, must be
        non-negative.

    Returns
    -------
    fs_coef_p : :obj:`numpy.ndarray`
        Free surface coefficients for P waves, of shape (n_grid_points, n_stations)
    fs_coef_s : :obj:`numpy.ndarray`
        Free surface coefficients for S waves, of shape (n_grid_points, n_stations)

    Raises
    ------
    ValueError
        If ``fs_level`` is not a scalar, ``fs_deviation`` is negative,
        ``station_coords_on_surface`` has the wrong shape or values outside
        [0, 1], or ``fs_mode`` is not one of the supported modes.

    Notes
    -----
    The free surface level is negated internally to match the convention that Z
    increases downwards.
    """
    if station_coords.ndim == 1 and station_coords.size == 3:
        station_coords = station_coords[np.newaxis, :]
    if grid_coords.ndim == 1 and grid_coords.size == 3:
        grid_coords = grid_coords[np.newaxis, :]

    n_stations = station_coords.shape[0]
    n_grid_points = grid_coords.shape[0]

    # Negate the free surface level to match the downward-positive Z convention
    if np.ndim(fs_level) != 0:
        raise ValueError("Free surface level must be a scalar.")
    fs_depth = -fs_level

    if fs_deviation < 0:
        raise ValueError("Free surface level deviation must be non-negative.")

    # Check and normalize the optional per-station weights
    surface_weights = None
    if station_coords_on_surface is not None:
        station_coords_on_surface = np.asarray(station_coords_on_surface)
        if station_coords_on_surface.ndim != 1 or station_coords_on_surface.shape[0] != n_stations:
            raise ValueError("station_coords_on_surface must be a 1D array with the same length as the number of stations.")
        surface_weights = station_coords_on_surface.astype(float, copy=False)
        if np.any((surface_weights < 0) | (surface_weights > 1)):
            raise ValueError("station_coords_on_surface must contain only values in the range [0, 1].")

    # Simple free-surface approximation: amplitudes are doubled at the surface
    full_fs_coef = 2.0

    # Decide how much of the full amplification applies to each station
    if fs_mode == 'auto':
        if surface_weights is None:
            surface_weights = (np.abs(station_coords[:, 2] - fs_depth) <= fs_deviation).astype(float)
    elif fs_mode == 'on':
        surface_weights = (np.abs(station_coords[:, 2] - fs_depth) <= fs_deviation).astype(float)
    elif fs_mode == 'off':
        surface_weights = np.zeros(n_stations, dtype=float)
    else:
        raise ValueError("Invalid free surface mode. Must be 'auto', 'on', or 'off'.")

    # Interpolate between no amplification (1.0) and full amplification
    fs_coef = np.broadcast_to(
        1.0 + (full_fs_coef - 1.0) * surface_weights[np.newaxis, :],
        (n_grid_points, n_stations)
    ).astype(float, copy=True)

    # The same coefficients are used for P and S waves
    return fs_coef, fs_coef


def _unit_vectors(vectors: np.ndarray) -> np.ndarray:
    r"""Normalize vectors along the last axis, leaving zero-length rows as NaN."""
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        return vectors / norms


def _station_reference_vectors(station_coords: np.ndarray) -> np.ndarray:
    r"""
    Estimate the local cable tangent at each channel from its neighbours.

    The forward difference to the next channel is used by default. Where the cable
    turns by more than 30 degrees, or where the forward step exceeds ten times the
    backward step, the backward difference is used instead, so that a channel at a
    kink or at the end of a segment still receives a sensible tangent.
    """
    if len(station_coords) < 2:
        raise ValueError("There must be at least two stations.")

    station_vectors = np.diff(station_coords, axis=0)
    cn_vectors = np.vstack([station_vectors, station_vectors[-1]])
    cp_vectors = np.vstack([station_vectors[0], station_vectors])

    eps = 1e-12
    cn_distances = np.linalg.norm(cn_vectors, axis=1) + eps
    cp_distances = np.linalg.norm(cp_vectors, axis=1) + eps

    cos_vals = np.sum(cn_vectors * cp_vectors, axis=1) / (cn_distances * cp_distances)
    cos_vals = np.clip(cos_vals, -1.0, 1.0)
    angles_cn_cp = np.arccos(cos_vals)
    use_cp = (angles_cn_cp > np.radians(30)) | (cn_distances > 10 * cp_distances)
    return np.where(use_cp[:, np.newaxis], cp_vectors, cn_vectors)


def _polarization_vectors(ray_vectors: np.ndarray, phase: str) -> np.ndarray:
    r"""
    Arriving polarization unit vectors for a phase.

    P is polarized along the ray, SH horizontally and perpendicular to the vertical
    ray plane, and SV perpendicular to both. For a vertical ray the SH direction is
    degenerate, so a stable horizontal fallback basis is used instead.
    """
    phase = normalize_wave_mode(phase)
    n = _unit_vectors(ray_vectors)
    if phase == "P":
        return n

    vertical = np.array([0.0, 0.0, 1.0])
    sh = np.cross(vertical, n)
    sh_norm = np.linalg.norm(sh, axis=-1)

    fallback_x = np.cross(np.array([1.0, 0.0, 0.0]), n)
    fallback_y = np.cross(np.array([0.0, 1.0, 0.0]), n)
    fallback_x_norm = np.linalg.norm(fallback_x, axis=-1)
    fallback = np.where((fallback_x_norm > 1e-12)[..., np.newaxis], fallback_x, fallback_y)
    sh = np.where((sh_norm > 1e-12)[..., np.newaxis], sh, fallback)
    sh = _unit_vectors(sh)

    if phase == "SH":
        return sh
    if phase == "SV":
        return _unit_vectors(np.cross(sh, n))

    raise ValueError("Polarization vectors are defined only for P, SV, and SH.")


def _validate_station_components(components) -> pd.Series:
    r"""Validate a ``Components`` column, filling missing entries with ``'3C'``."""
    component_series = pd.Series(components).dropna()
    invalid_components = sorted(set(component_series).difference({'3C', 'Z'}))
    if invalid_components:
        raise ValueError(
            "Components values must be either '3C' or 'Z'. "
            f"Invalid values: {', '.join(invalid_components)}"
        )
    return pd.Series(components).fillna('3C')


def geometry_requires_receiver_projection(geometry_df: Optional[pd.DataFrame]) -> bool:
    r"""
    Return whether a geometry needs receiver-component projection.

    A DAS geometry, identified by the presence of a gauge length, always requires
    projection onto the local cable tangent. A station geometry requires projection
    only if at least one station records a single vertical component.

    Parameters
    ----------
    geometry_df : :obj:`pandas.DataFrame` or ``None``
        Geometry DataFrame.

    Returns
    -------
    required : :obj:`bool`
        Whether projection is required.
    """
    if geometry_df is None:
        return False
    if geometry_df.attrs.get('gauge_length') is not None:
        return True
    if 'Components' not in geometry_df.columns:
        return False
    components = _validate_station_components(geometry_df['Components'])
    return bool((components == 'Z').any())


def get_phase_station_directionality(station_coords: np.ndarray,
                                     grid_coords: np.ndarray,
                                     phases=("P", "SV", "SH"),
                                     geometry_df: Optional[pd.DataFrame] = None,
                                     force_tangent: bool = False,
                                     strict_nan_check: bool = False) -> dict:
    r"""
    Derive receiver projection coefficients for P, SV and SH polarizations.

    The recorded amplitude of a phase is the projection of its arriving
    polarization onto the direction the receiver is sensitive to. For a phase
    :math:`\phi` the correction applied to the minimum detectable amplitude is

    .. math::
        C_{\phi} = \frac{1}{\left| \mathbf{d} \cdot \mathbf{e}_{\phi} \right|},

    where :math:`\mathbf{e}_{\phi}` is the arriving polarization and
    :math:`\mathbf{d}` is the local cable tangent for DAS, or the vertical axis for
    a single-component station. Three-component stations record the full vector and
    therefore use a coefficient of one.

    Parameters
    ----------
    station_coords : :obj:`numpy.ndarray`
        Array of station coordinates [[xr1, yr1, zr1], [xr2, yr2, zr2], ...]
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    phases : sequence of :obj:`str`, optional, default: ``("P", "SV", "SH")``
        Phases to compute coefficients for. Must be drawn from 'P', 'SV' and 'SH'.
    geometry_df : :obj:`pandas.DataFrame`, optional
        Geometry DataFrame, used to detect a DAS geometry from its gauge length and
        to read a ``Components`` column for station geometries. If ``None``,
        projection onto the local tangent is used.
    force_tangent : :obj:`bool`, optional, default: ``False``
        Force projection onto the local tangent even when ``geometry_df`` describes
        a station geometry.
    strict_nan_check : :obj:`bool`, optional, default: ``False``
        Flag to check whether NaN values appear in the result.

    Returns
    -------
    coefficients : :obj:`dict`
        Mapping from phase name to an array of coefficients of shape
        (n_grid_points, n_stations).

    Raises
    ------
    ValueError
        If a requested phase is not P, SV or SH, if the geometry and station
        coordinates disagree in length, or if a DAS geometry also carries a
        ``Components`` column.
    RuntimeError
        If ``strict_nan_check`` is True and NaN appears in the result.

    Notes
    -----
    A vanishing projection means the phase cannot be recorded at all, for example
    SH on a vertical cable, and yields NaN so that the phase is excluded rather
    than reported as infinitely detectable.

    Straight rays between each station and each grid point are assumed, which is
    exact in a homogeneous medium.
    """
    station_coords = np.asarray(station_coords, dtype=float)
    grid_coords = np.asarray(grid_coords, dtype=float)
    if station_coords.ndim == 1 and station_coords.size == 3:
        station_coords = station_coords[np.newaxis, :]
    if grid_coords.ndim == 1 and grid_coords.size == 3:
        grid_coords = grid_coords[np.newaxis, :]

    phases = tuple(dict.fromkeys(normalize_wave_mode(phase) for phase in phases))
    if any(phase not in ("P", "SV", "SH") for phase in phases):
        raise ValueError("Directionality phases must be P, SV, or SH.")

    use_tangent_projection = force_tangent or geometry_df is None
    components = None
    if geometry_df is not None:
        if len(geometry_df) != len(station_coords):
            raise ValueError("Geometry and station coordinates must have the same number of stations.")
        has_gauge_length = geometry_df.attrs.get('gauge_length') is not None
        has_components = 'Components' in geometry_df.columns
        if has_gauge_length:
            if has_components and geometry_df['Components'].notna().any():
                raise ValueError("Components column is only allowed for station geometries, not DAS geometries.")
            use_tangent_projection = True
        elif has_components:
            components = _validate_station_components(geometry_df['Components']).to_numpy()
        else:
            components = np.full(len(station_coords), '3C', dtype=object)

    if use_tangent_projection:
        reference_unit = _unit_vectors(_station_reference_vectors(station_coords))
    else:
        vertical_unit = np.array([0.0, 0.0, 1.0])

    # Straight rays from each station to each grid point
    ray_vectors = grid_coords[:, np.newaxis, :] - station_coords[np.newaxis, :, :]

    result = {}
    for phase in phases:
        polarization = _polarization_vectors(ray_vectors, phase)
        if use_tangent_projection:
            projection = np.abs(
                np.sum(polarization * reference_unit[np.newaxis, :, :], axis=2)
            )
            projection[np.isclose(projection, 0.0)] = np.nan
            result[phase] = 1.0 / projection
        else:
            coefficients = np.ones(polarization.shape[:2], dtype=float)
            z_mask = components == 'Z'
            if np.any(z_mask):
                projection = np.abs(
                    np.sum(polarization[:, z_mask, :] * vertical_unit, axis=2)
                )
                projection[np.isclose(projection, 0.0)] = np.nan
                coefficients[:, z_mask] = 1.0 / projection
            result[phase] = coefficients

    if strict_nan_check:
        if any(np.any(np.isnan(values)) for values in result.values()):
            current_function = inspect.currentframe().f_code.co_name
            raise RuntimeError(
                f"NaN values detected while computing directionality coefficients in {current_function}."
            )

    return result


def get_ray_station_directionality(station_coords: np.ndarray,
                                   grid_coords: np.ndarray,
                                   strict_nan_check: bool = False):
    r"""
    Derive directionality coefficients for P and S waves along a cable.

    .. deprecated::
        Use :func:`get_phase_station_directionality`, which resolves SV and SH
        separately and projects the actual polarization vectors.

    Parameters
    ----------
    station_coords : :obj:`numpy.ndarray`
        Array of station coordinates [[xr1, yr1, zr1], [xr2, yr2, zr2], ...]
    grid_coords : :obj:`numpy.ndarray`
        Array of grid coordinates [[xs1, ys1, zs1], [xs2, ys2, zs2], ...]
    strict_nan_check : :obj:`bool`, optional, default: ``False``
        Flag to check whether NaN values appear in the result.

    Returns
    -------
    dir_coef_p : :obj:`numpy.ndarray`
        Directionality coefficients for P waves, of shape (n_grid_points, n_stations)
    dir_coef_s : :obj:`numpy.ndarray`
        Directionality coefficients for SV waves, of shape (n_grid_points, n_stations)

    Notes
    -----
    Returns the P and SV coefficients of
    :func:`get_phase_station_directionality` with tangent projection forced. For a
    vertical cable these are the familiar :math:`1/|\cos\theta|` and
    :math:`1/|\sin\theta|`; for an inclined or curved cable they are the correct
    polarization projections rather than that approximation.
    """
    warnings.warn(
        "get_ray_station_directionality is deprecated; use "
        "get_phase_station_directionality, which resolves SV and SH separately.",
        DeprecationWarning,
        stacklevel=2,
    )
    coefficients = get_phase_station_directionality(
        station_coords=station_coords,
        grid_coords=grid_coords,
        phases=("P", "SV"),
        geometry_df=None,
        force_tangent=True,
        strict_nan_check=strict_nan_check,
    )
    return coefficients["P"], coefficients["SV"]
