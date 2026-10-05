import numpy as np

# Detection modes for the free surface correction
VALID_FS_MODES = ('auto', 'on', 'off')


class DetectionParameters:
    r"""
    Container for the parameters controlling event detection.

    Parameters
    ----------
    min_SNR_p : :obj:`float`
        Minimum signal-to-noise ratio required to detect a P wave on one receiver.
    min_SNR_s : :obj:`float`
        Minimum signal-to-noise ratio required to detect an S wave on one receiver.
    min_stations_p : :obj:`int`
        Minimum number of receivers on which the event must be detected with P waves.
    min_stations_s : :obj:`int`
        Minimum number of receivers on which the event must be detected with S waves.
    f_p : :obj:`float`, optional
        Representative frequency of the P wave (Hz).
        If ``None``, the peak frequency is computed from the model.
    f_s : :obj:`float`, optional
        Representative frequency of the S wave (Hz).
        If ``None``, the peak frequency is computed from the model.
    f_p_corner : :obj:`float`, optional, default: ``None`` (100 Hz)
        Corner frequency of the P wave (Hz), limiting the peak frequency.
    f_s_corner : :obj:`float`, optional, default: ``None`` (100 Hz)
        Corner frequency of the S wave (Hz), limiting the peak frequency.
    fs_mode : :obj:`str`, optional, default: ``None`` (``'auto'``)
        Free surface correction mode, one of ``'auto'``, ``'on'`` or ``'off'``.
        In ``'auto'`` mode the correction is applied to receivers that are within
        ``fs_deviation`` of the free surface level, or according to the ``Surface``
        column of the geometry when present.
    fs_level : :obj:`float`, optional, default: ``None`` (0.0)
        Level of the free surface in metres above the reference level.
    fs_deviation : :obj:`float`, optional, default: ``None`` (1.0)
        Permitted deviation from the free surface level in metres.
    free_surface : :obj:`bool`, optional
        Deprecated override kept for backward compatibility. ``True`` maps to
        ``fs_mode='on'`` and ``False`` to ``fs_mode='off'``. If ``None``, ``fs_mode``
        is used.

    Notes
    -----
    The free surface correction is applied per receiver, so a geometry combining
    surface and downhole receivers is handled correctly. This differs from
    PyNetDesign 1.0.x, where ``free_surface=True`` amplified every receiver
    irrespective of its depth.
    """

    def __init__(self,
                 min_SNR_p: float,
                 min_SNR_s: float,
                 min_stations_p: int,
                 min_stations_s: int,
                 f_p: float=None,
                 f_s: float=None,
                 f_p_corner: float=None,
                 f_s_corner: float=None,
                 fs_mode: str=None,
                 fs_level: float=None,
                 fs_deviation: float=None,
                 free_surface: bool=None):

        self.min_SNR_p = min_SNR_p
        self.min_SNR_s = min_SNR_s
        self.min_stations_p = min_stations_p
        self.min_stations_s = min_stations_s
        self.f_p = f_p
        self.f_s = f_s
        self.f_p_corner = f_p_corner
        self.f_s_corner = f_s_corner
        self.fs_mode = fs_mode
        self.fs_level = fs_level
        self.fs_deviation = fs_deviation
        self.free_surface = free_surface

    def validate(self):

        if (self.min_SNR_p is None or self.min_SNR_s is None):
            raise ValueError("Minimum S/N ratio can not be None")

        if (self.min_stations_p is None and self.min_stations_s is None):
            raise ValueError("Minimum number of stations can not be None")

        if not (self.min_SNR_p > 0 and self.min_SNR_s > 0):
            raise ValueError("Minimum S/N ratios must be positive")

        if not (self.min_stations_p > 0 and self.min_stations_s > 0):
            raise ValueError("Minimum number of stations must be positive")

        if self.f_p is not None:
            if self.f_p <= 0:
                raise ValueError("P-wave frequency must be positive")

        if self.f_s is not None:
            if self.f_s <= 0:
                raise ValueError("S-wave frequency must be positive")

        if self.f_p_corner is not None:
            if self.f_p_corner <= 0:
                raise ValueError("P-wave corner frequency must be positive")
        else:
            self.f_p_corner = 100

        if self.f_s_corner is not None:
            if self.f_s_corner <= 0:
                raise ValueError("S-wave corner frequency must be positive")
        else:
            self.f_s_corner = 100

        # The deprecated free_surface flag, when given, decides the mode.
        # Written back to fs_mode so that repeated validation is idempotent.
        if self.free_surface is not None:
            mapped = 'on' if self.free_surface else 'off'
            if self.fs_mode is not None and self.fs_mode != mapped:
                raise ValueError("Provide either free_surface or fs_mode, not both")
            self.fs_mode = mapped

        if self.fs_mode is None:
            self.fs_mode = 'auto'
        elif not isinstance(self.fs_mode, str):
            raise ValueError("Free surface correction mode must be a string")
        elif self.fs_mode not in VALID_FS_MODES:
            raise ValueError(
                "Free surface correction mode must be one of the following: "
                + ", ".join(VALID_FS_MODES)
            )

        if self.fs_level is None:
            self.fs_level = 0.0
        elif np.ndim(self.fs_level) != 0:
            raise ValueError("Free surface level must be a scalar")

        if self.fs_deviation is None:
            self.fs_deviation = 1.0
        elif self.fs_deviation < 0:
            raise ValueError("Free surface level deviation must be non-negative")
