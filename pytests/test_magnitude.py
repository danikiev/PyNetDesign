"""Tests for the magnitude / seismic-moment relations.

The closed-form checks in this module guard against the regression reported in
issue #3, where ``calculate_M0`` applied the amplitude-to-displacement spectral
conversion twice and therefore underestimated the seismic moment by a factor of
``2 * pi * f``.
"""
import numpy as np
import pandas as pd
import pytest

from pynetdesign.modelling.homo import calculate_M0, calculate_fpeak
from pynetdesign.modelling.utils import (
    calculate_Mw,
    calculate_seismic_moment,
    get_scaling_displacement,
    retrieve_min_amps,
)

# Medium of test case 1 (Hallo, 2012)
RHO = 2300.0
VP = 4300.0
QP = 100.0
RAD_P = 0.52


def m0_closed_form(density, v, Q, rad_pattern, r, u, f):
    """M0 = (4 pi rho v^3 r / |R|) * |U(f)| * exp(pi f t*), with t* = r / (v Q).

    Written out independently of the package so that it cannot drift with it.
    """
    t_star = r / (v * Q)
    return 4.0 * np.pi * density * v**3 * r / rad_pattern * u * np.exp(np.pi * f * t_star)


class TestCalculateM0:
    def test_matches_closed_form_explicit_frequency(self):
        """The core relation, with the representative frequency supplied."""
        r, u, f = 1000.0, 1e-9, 10.0
        expected = m0_closed_form(RHO, VP, QP, RAD_P, r, u, f)
        actual = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                              r=r, amps=u, f=f, amps_type='displacement')
        assert actual == pytest.approx(expected, rel=1e-12)

    def test_no_spurious_two_pi_f_factor(self):
        """Regression guard for issue #3.

        The buggy implementation returned ``expected / (2 * pi * f)``. Assert the
        ratio is one and, explicitly, that it is not ``2 * pi * f``.
        """
        r, u, f = 1000.0, 1e-9, 10.0
        expected = m0_closed_form(RHO, VP, QP, RAD_P, r, u, f)
        actual = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                              r=r, amps=u, f=f, amps_type='displacement')
        ratio = expected / actual
        assert ratio == pytest.approx(1.0, rel=1e-12)
        assert ratio != pytest.approx(2.0 * np.pi * f, rel=1e-6)

    def test_peak_frequency_path_below_corner(self):
        """With f=None and f_peak below the corner, pi*f_peak*t* == 1 exactly,
        so the attenuation term collapses to Euler's number."""
        r, u = 5000.0, 1e-9          # f_peak = vQ/(pi r) = 27.4 Hz < 100 Hz
        f_peak = VP * QP / (np.pi * r)
        assert f_peak < 100.0
        expected = 4.0 * np.pi * RHO * VP**3 * r / RAD_P * u * np.e
        actual = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                              r=r, amps=u, f=None, amps_type='displacement')
        assert actual == pytest.approx(expected, rel=1e-12)

    def test_peak_frequency_path_clamped_at_corner(self):
        """Close to the receiver the peak frequency is clamped to the corner."""
        r, u, fcorner = 500.0, 1e-9, 100.0
        assert VP * QP / (np.pi * r) > fcorner
        expected = m0_closed_form(RHO, VP, QP, RAD_P, r, u, fcorner)
        actual = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                              r=r, amps=u, f=None, fcorner=fcorner,
                              amps_type='displacement')
        assert actual == pytest.approx(expected, rel=1e-12)

    def test_explicit_and_automatic_paths_agree(self):
        """Supplying f explicitly must match the automatic path evaluated at the
        same frequency. The two paths scale the amplitudes in different places,
        so this pins them together."""
        r = 5000.0
        f_peak = VP * QP / (np.pi * r)
        noise_velocity = 5e-9
        # automatic path: raw velocity amplitude, converted inside calculate_M0
        auto = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                            r=r, amps=noise_velocity, f=None,
                            amps_type='velocity')
        # explicit path: amplitude pre-converted to a displacement spectrum
        u = noise_velocity * get_scaling_displacement(amps_type='velocity', f=f_peak)
        explicit = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                                r=r, amps=u, f=f_peak, amps_type='displacement')
        assert auto == pytest.approx(explicit, rel=1e-12)

    def test_scales_linearly_with_distance_and_amplitude(self):
        r, u, f = 1000.0, 1e-9, 10.0
        base = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                            r=r, amps=u, f=f, amps_type='displacement')
        doubled = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                               r=r, amps=2 * u, f=f, amps_type='displacement')
        assert doubled == pytest.approx(2.0 * base, rel=1e-12)

    def test_inversely_proportional_to_radiation_pattern(self):
        r, u, f = 1000.0, 1e-9, 10.0
        a = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=0.52,
                         r=r, amps=u, f=f, amps_type='displacement')
        b = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=0.63,
                         r=r, amps=u, f=f, amps_type='displacement')
        assert a / b == pytest.approx(0.63 / 0.52, rel=1e-12)

    def test_array_input(self):
        r = np.array([1000.0, 2000.0, 4000.0])
        u = np.full_like(r, 1e-9)
        f = 10.0
        expected = m0_closed_form(RHO, VP, QP, RAD_P, r, u, f)
        actual = calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                              r=r, amps=u, f=f, amps_type='displacement')
        assert actual.shape == r.shape
        np.testing.assert_allclose(actual, expected, rtol=1e-12)

    def test_rejects_mismatched_shapes(self):
        with pytest.raises(ValueError):
            calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                         r=np.array([1000.0, 2000.0]), amps=1e-9, f=10.0)
        with pytest.raises(ValueError):
            calculate_M0(density=RHO, v=VP, Q=QP, rad_pattern=RAD_P,
                         r=1000.0, amps=None, f=10.0)


class TestMomentMagnitude:
    def test_kanamori_relation(self):
        """Mw = (2/3) (log10 M0 - 9.1)."""
        assert calculate_Mw(10**9.1) == pytest.approx(0.0, abs=1e-12)
        assert calculate_Mw(10**(9.1 + 1.5)) == pytest.approx(1.0, rel=1e-12)
        assert calculate_Mw(10**(9.1 - 1.5)) == pytest.approx(-1.0, rel=1e-12)

    @pytest.mark.parametrize("mw", [-2.0, -1.0, -0.5, 0.0, 1.0, 2.5, 5.0])
    def test_roundtrip(self, mw):
        assert calculate_Mw(calculate_seismic_moment(mw)) == pytest.approx(mw, rel=1e-12)

    def test_non_positive_moment_gives_nan(self):
        out = calculate_Mw(np.array([-1.0, 0.0, 10**9.1]))
        assert np.isnan(out[0]) and np.isnan(out[1])
        assert out[2] == pytest.approx(0.0, abs=1e-12)

    def test_moment_is_monotonic_in_magnitude(self):
        mws = np.array([-1.0, 0.0, 1.0, 2.0])
        assert np.all(np.diff(calculate_seismic_moment(mws)) > 0)


class TestScalingToDisplacement:
    @pytest.mark.parametrize("amps_type,expected", [
        ('displacement', 1.0),
        ('velocity', 1.0 / (2 * np.pi * 10.0)),
        ('acceleration', 1.0 / (2 * np.pi * 10.0) ** 2),
        ('strain', 1.0),
        ('strain rate', 1.0 / (2 * np.pi * 10.0)),
    ])
    def test_values(self, amps_type, expected):
        assert get_scaling_displacement(amps_type=amps_type, f=10.0) == pytest.approx(
            expected, rel=1e-12)

    def test_rejects_unknown_type(self):
        with pytest.raises(ValueError):
            get_scaling_displacement(amps_type='nonsense', f=10.0)


class TestPeakFrequency:
    def test_formula_below_corner(self):
        r = 5000.0
        assert calculate_fpeak(v=VP, Q=QP, r=r) == pytest.approx(
            VP * QP / (np.pi * r), rel=1e-12)

    def test_clamped_to_corner(self):
        assert calculate_fpeak(v=VP, Q=QP, r=100.0) == pytest.approx(100.0, rel=1e-12)
        assert calculate_fpeak(v=VP, Q=QP, r=100.0, fcorner=50.0) == pytest.approx(
            50.0, rel=1e-12)

    def test_decreases_with_distance(self):
        r = np.array([2000.0, 4000.0, 8000.0])
        assert np.all(np.diff(calculate_fpeak(v=VP, Q=QP, r=r)) < 0)


class TestDasThreshold:
    """End-to-end noise -> displacement-spectrum threshold for a DAS channel,
    locking in S(f) = L_g / (2 pi f) for strain rate."""

    @staticmethod
    def das_geometry(noise_type, noise_level, gauge_length):
        df = pd.DataFrame({'Name': ['C1'], 'X': [0.0], 'Y': [0.0], 'Z': [0.0],
                           'NoiseLevel': [noise_level]})
        df.attrs['noise_type'] = noise_type
        df.attrs['gauge_length'] = gauge_length
        return df

    def test_strain_rate_threshold(self):
        a_n, l_g, snr, f = 1.95e-9, 10.0, 2.0, 10.0
        df = self.das_geometry('strain rate', a_n, l_g)
        min_p, min_s = retrieve_min_amps(geometry_df=df, SNR_p=snr, SNR_s=snr,
                                         f_p=f, f_s=f, sample_interval=l_g)
        expected = snr * a_n * l_g / (2 * np.pi * f)
        assert min_p[0] == pytest.approx(expected, rel=1e-12)
        assert min_s[0] == pytest.approx(expected, rel=1e-12)

    def test_strain_threshold(self):
        a_n, l_g, snr, f = 5e-9, 10.0, 2.0, 10.0
        df = self.das_geometry('strain', a_n, l_g)
        min_p, _ = retrieve_min_amps(geometry_df=df, SNR_p=snr, SNR_s=snr,
                                     f_p=f, f_s=f, sample_interval=l_g)
        assert min_p[0] == pytest.approx(snr * a_n * l_g, rel=1e-12)

    def test_requires_gauge_length_for_strain(self):
        df = self.das_geometry('strain rate', 1.95e-9, 10.0)
        with pytest.raises(ValueError):
            retrieve_min_amps(geometry_df=df, SNR_p=2.0, SNR_s=2.0,
                              f_p=10.0, f_s=10.0, sample_interval=None)

    def test_threshold_is_linear_in_snr(self):
        df = self.das_geometry('strain rate', 1.95e-9, 10.0)
        a, _ = retrieve_min_amps(geometry_df=df, SNR_p=2.0, SNR_s=2.0,
                                 f_p=10.0, f_s=10.0, sample_interval=10.0)
        b, _ = retrieve_min_amps(geometry_df=df, SNR_p=4.0, SNR_s=4.0,
                                 f_p=10.0, f_s=10.0, sample_interval=10.0)
        assert b[0] == pytest.approx(2.0 * a[0], rel=1e-12)
