"""Forward and inverse consistency of the homogeneous magnitude relation.

``calculate_M0`` inverts the far-field displacement spectrum of a point moment-tensor
source in a homogeneous medium. The tests here build the forward model independently
of the package, from the relation stated in the methodology chapter, and check that
the inverse recovers exactly what the forward model produced.

The second group is the reason this module exists. The detection threshold is assembled
in two places: ``retrieve_min_amps`` converts a recorded noise level into a displacement
amplitude spectrum, and ``calculate_M0`` turns that into a moment. The conversion
``S(f)`` must be applied once across the pair, never twice, which is exactly what went
wrong before 1.0.1. Asserting that an event at the threshold magnitude produces exactly
``min_SNR`` in the quantity the instrument actually records pins that down for every
amplitude type, including the gauge-length bridge that DAS needs.
"""
import numpy as np
import pytest

from pynetdesign.modelling.homo import calculate_M0, calculate_fpeak
from pynetdesign.modelling.io import read_geometry
from pynetdesign.modelling.utils import (calculate_Mw, calculate_seismic_moment,
                                         get_scaling_displacement, retrieve_min_amps)

# A homogeneous medium to work in: the parameters of the DAS benchmark example
RHO, V, Q = 2500.0, 2370.0, 100.0
RAD_PATTERN = np.sqrt(4.0 / 15.0)
GAUGE_LENGTH = 10.0


def forward_displacement_spectrum(M0, r, f, density=RHO, v=V, Q=Q,
                                  rad_pattern=RAD_PATTERN):
    """The displacement amplitude spectrum radiated by a moment M0 at distance r.

    This is the relation ``calculate_M0`` inverts, written out here so that the test
    does not depend on the package to state what the answer should be.
    """
    t_star = r / (v * Q)
    return (M0 * rad_pattern / (4.0 * np.pi * density * v**3 * r)
            * np.exp(-np.pi * f * t_star))


def recorded_from_displacement(U, amps_type, f):
    """Convert a displacement amplitude spectrum into what an instrument records."""
    omega = 2.0 * np.pi * f
    if amps_type == 'displacement':
        return U
    if amps_type == 'velocity':
        return U * omega
    if amps_type == 'acceleration':
        return U * omega**2
    if amps_type == 'strain':
        return U / GAUGE_LENGTH
    if amps_type == 'strain rate':
        return U * omega / GAUGE_LENGTH
    raise ValueError(amps_type)


NOISE_UNITS = {
    'displacement': 'm',
    'velocity': 'm/s',
    'acceleration': 'm/s^2',
    'strain': 'strain',
    'strain rate': '1/s',
}


def write_geometry(tmp_path, amps_type, noise_level):
    """One receiver with the given noise type, read back through the package."""
    unit = NOISE_UNITS[amps_type]
    tab = chr(9)
    if amps_type in ('strain', 'strain rate'):
        header = tab.join(['Northing(m)', 'Easting(m)', 'Elevation(m)',
                           f'NoiseLevel({unit})', f'GaugeLength={GAUGE_LENGTH:g}(m)'])
        row = tab.join(['0', '0', '-500', repr(noise_level)])
    else:
        header = tab.join(['Name', 'Northing(m)', 'Easting(m)', 'Elevation(m)',
                           f'NoiseLevel({unit})'])
        row = tab.join(['ST1', '0', '0', '-500', repr(noise_level)])
    path = tmp_path / f"geom_{amps_type.replace(' ', '_')}.txt"
    path.write_text(header + "\n" + row + "\n", encoding="utf-8")
    return read_geometry(str(path))


class TestForwardInverse:
    """calculate_M0 must invert the forward relation exactly."""

    @pytest.mark.parametrize("M0", [1.0e6, 1.0e9, 1.0e12])
    @pytest.mark.parametrize("r", [100.0, 1000.0, 5000.0])
    @pytest.mark.parametrize("f", [5.0, 25.0, 100.0])
    def test_inverse_recovers_the_moment(self, M0, r, f):
        U = forward_displacement_spectrum(M0, r, f)
        recovered = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                 r=r, amps=U, f=f, amps_type='displacement')
        assert recovered == pytest.approx(M0, rel=1e-12)

    def test_inverse_recovers_the_moment_over_a_grid_of_distances(self):
        r = np.array([50.0, 250.0, 1000.0, 4000.0])
        M0, f = 5.0e8, 20.0
        U = forward_displacement_spectrum(M0, r, f)
        recovered = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                 r=r, amps=U, f=f, amps_type='displacement')
        np.testing.assert_allclose(recovered, np.full(r.shape, M0), rtol=1e-12)

    @pytest.mark.parametrize("Mw", [-3.0, -1.5, 0.0, 2.5, 5.0])
    def test_magnitude_round_trip_through_the_forward_model(self, Mw):
        """Mw -> M0 -> |U| -> M0 -> Mw must return the magnitude it started from."""
        r, f = 800.0, 30.0
        U = forward_displacement_spectrum(calculate_seismic_moment(Mw), r, f)
        recovered = calculate_Mw(calculate_M0(density=RHO, v=V, Q=Q,
                                              rad_pattern=RAD_PATTERN, r=r, amps=U,
                                              f=f, amps_type='displacement'))
        assert recovered == pytest.approx(Mw, abs=1e-12)


class TestSpectralConversionAppliedOnce:
    """S(f) must be applied exactly once between the recording and the moment."""

    @pytest.mark.parametrize("amps_type", list(NOISE_UNITS))
    def test_peak_frequency_path_matches_an_explicit_displacement_call(self, amps_type):
        """Passing a recorded amplitude is the same as passing its displacement value.

        With ``f=None`` the representative frequency is derived from the distance and
        ``S(f)`` is applied inside ``calculate_M0``; with an explicit ``f`` the
        amplitude is taken as displacement already. Feeding the second form the
        converted amplitude must reproduce the first exactly.
        """
        r = 1000.0
        f_r = calculate_fpeak(v=V, Q=Q, r=r)
        recorded = 3.0e-9
        # The displacement equivalent, including the gauge-length bridge for DAS
        scaling = get_scaling_displacement(amps_type=amps_type, f=f_r)
        if amps_type in ('strain', 'strain rate'):
            scaling = scaling * GAUGE_LENGTH
        U = recorded * scaling

        via_amps_type = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                     r=r, amps=recorded * (GAUGE_LENGTH if amps_type in
                                     ('strain', 'strain rate') else 1.0),
                                     f=None, amps_type=amps_type)
        via_displacement = calculate_M0(density=RHO, v=V, Q=Q,
                                        rad_pattern=RAD_PATTERN, r=r, amps=U,
                                        f=f_r, amps_type='displacement')
        assert via_amps_type == pytest.approx(via_displacement, rel=1e-12)


class TestThresholdReachesMinSNR:
    """An event at the threshold magnitude must record exactly min_SNR."""

    @pytest.mark.parametrize("amps_type", list(NOISE_UNITS))
    @pytest.mark.parametrize("min_SNR", [1.0, 2.0, 5.0])
    def test_threshold_magnitude_gives_exactly_min_snr(self, tmp_path, amps_type,
                                                       min_SNR):
        noise_level = 2.5e-9
        r = 900.0
        geometry_df = write_geometry(tmp_path, amps_type, noise_level)
        assert geometry_df.attrs['noise_type'] == amps_type

        f_r = calculate_fpeak(v=V, Q=Q, r=r)
        gauge_length = geometry_df.attrs.get('gauge_length')

        # The displacement threshold, assembled the way core.py assembles it
        min_amps_p, _ = retrieve_min_amps(geometry_df=geometry_df, SNR_p=min_SNR,
                                          SNR_s=min_SNR, f_p=f_r, f_s=f_r,
                                          sample_interval=gauge_length)
        U_min = float(min_amps_p[0])

        # The smallest detectable moment, and the magnitude it corresponds to
        M0_min = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN, r=r,
                              amps=U_min, f=f_r, amps_type='displacement')
        Mw_min = calculate_Mw(M0_min)

        # Forward-model an event of exactly that magnitude and read it back off the
        # instrument: the signal-to-noise ratio must land on the requested threshold
        U = forward_displacement_spectrum(calculate_seismic_moment(Mw_min), r, f_r)
        recorded = recorded_from_displacement(U, amps_type, f_r)
        assert recorded / noise_level == pytest.approx(min_SNR, rel=1e-9)

    def test_doubling_the_noise_raises_the_threshold_by_a_fixed_amount(self, tmp_path):
        """Twice the noise needs 2/3*log10(2) more magnitude, whatever else holds."""
        r = 900.0
        f_r = calculate_fpeak(v=V, Q=Q, r=r)
        magnitudes = []
        for noise_level in (1.0e-9, 2.0e-9):
            geometry_df = write_geometry(tmp_path, 'velocity', noise_level)
            min_amps_p, _ = retrieve_min_amps(geometry_df=geometry_df, SNR_p=2.0,
                                              SNR_s=2.0, f_p=f_r, f_s=f_r)
            M0 = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN, r=r,
                              amps=float(min_amps_p[0]), f=f_r,
                              amps_type='displacement')
            magnitudes.append(calculate_Mw(M0))
        assert magnitudes[1] - magnitudes[0] == pytest.approx(2 / 3 * np.log10(2.0))


class TestCoincidentReceiver:
    """A grid point sitting on a receiver gives r = 0, which must stay quiet.

    With a dense DAS cable every channel lies on a grid line, so this is ordinary
    rather than exotic. The peak frequency goes to infinity and is clamped to the
    corner frequency, which is the intended answer, so no warning belongs here.
    """

    def test_zero_distance_does_not_warn(self):
        r = np.array([0.0, 100.0, 500.0])
        amps = np.full(r.shape, 1.0e-9)
        with np.errstate(all='raise'):
            M0 = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN, r=r,
                              amps=amps, f=None, amps_type='velocity')
        assert M0[0] == 0.0
        assert np.all(np.isfinite(M0))

    def test_zero_distance_uses_the_corner_frequency(self):
        """At r = 0 the clamp must pick the corner frequency, not infinity."""
        r = np.array([0.0])
        amps = np.array([1.0e-9])
        for fcorner in (50.0, 100.0, 250.0):
            M0_zero = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                   r=r, amps=amps, f=None, fcorner=fcorner,
                                   amps_type='velocity')
            # r = 0 zeroes the moment, so compare the frequency the clamp chose by
            # evaluating a distance short enough that the peak frequency is clamped too
            r_short = np.array([1.0e-6])
            M0_short = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                    r=r_short, amps=amps, f=None, fcorner=fcorner,
                                    amps_type='velocity')
            expected = calculate_M0(density=RHO, v=V, Q=Q, rad_pattern=RAD_PATTERN,
                                    r=r_short, amps=amps, f=fcorner,
                                    amps_type='displacement') / (2 * np.pi * fcorner)
            assert M0_zero[0] == 0.0
            assert M0_short[0] == pytest.approx(expected[0], rel=1e-9)
