"""Tests for the network detectability criterion.

The network threshold at a grid point is the N-th smallest per-station threshold,
so that the event is required to be detected on at least N receivers. For joint
P and S detection the stricter of the two thresholds applies.
"""
import numpy as np
import pytest

from pynetdesign.modelling.utils import check_min_stations, mag_detectable


def stations_grid(p_values, s_values):
    """Build a (2, n_grid, n_stations) array from per-station values."""
    p = np.asarray(p_values, dtype=float)
    s = np.asarray(s_values, dtype=float)
    if p.ndim == 1:
        p = p[np.newaxis, :]
    if s.ndim == 1:
        s = s[np.newaxis, :]
    return np.stack([p, s])


class TestNthSmallest:
    def test_p_mode_picks_nth_smallest(self):
        mw = stations_grid([0.5, -1.0, 0.2, -0.4], [9.0, 9.0, 9.0, 9.0])
        # sorted P: -1.0, -0.4, 0.2, 0.5
        assert mag_detectable(mw, min_stations_p=1, wave_mode='P')[0] == pytest.approx(-1.0)
        assert mag_detectable(mw, min_stations_p=2, wave_mode='P')[0] == pytest.approx(-0.4)
        assert mag_detectable(mw, min_stations_p=3, wave_mode='P')[0] == pytest.approx(0.2)
        assert mag_detectable(mw, min_stations_p=4, wave_mode='P')[0] == pytest.approx(0.5)

    def test_more_stations_required_means_higher_threshold(self):
        mw = stations_grid(np.linspace(-2.0, 1.0, 8), np.full(8, 9.0))
        thresholds = [mag_detectable(mw, min_stations_p=n, wave_mode='P')[0]
                      for n in range(1, 9)]
        assert np.all(np.diff(thresholds) > 0)

    @pytest.mark.parametrize("mode", ["S", "SV", "SH"])
    def test_s_family_modes_use_the_s_row(self, mode):
        mw = stations_grid([9.0, 9.0, 9.0], [0.3, -0.7, 0.1])
        assert mag_detectable(mw, min_stations_s=2, wave_mode=mode)[0] == pytest.approx(0.1)

    def test_default_is_three_stations(self):
        mw = stations_grid([0.5, -1.0, 0.2, -0.4], [0.5, -1.0, 0.2, -0.4])
        assert mag_detectable(mw, wave_mode='P')[0] == pytest.approx(0.2)


class TestJointDetection:
    def test_ps_takes_the_stricter_branch(self):
        mw = stations_grid([0.0, 0.0, 0.0], [-1.0, -1.0, -1.0])
        # P needs the larger magnitude, so P governs
        assert mag_detectable(mw, min_stations_p=3, min_stations_s=3,
                              wave_mode='PS')[0] == pytest.approx(0.0)

    def test_ps_is_never_easier_than_either_branch(self):
        rng = np.random.default_rng(0)
        p = rng.normal(0.0, 1.0, (20, 6))
        s = rng.normal(-0.5, 1.0, (20, 6))
        mw = np.stack([p, s])
        ps = mag_detectable(mw, min_stations_p=3, min_stations_s=3, wave_mode='PS')
        only_p = mag_detectable(mw, min_stations_p=3, wave_mode='P')
        only_s = mag_detectable(mw, min_stations_s=3, wave_mode='S')
        assert np.all(ps >= only_p - 1e-12)
        assert np.all(ps >= only_s - 1e-12)

    def test_independent_station_counts(self):
        mw = stations_grid([0.5, -1.0, 0.2, -0.4], [0.9, -1.2, 0.4, -0.2])
        # P with 2 stations -> -0.4 ; S with 4 stations -> 0.9 ; max -> 0.9
        assert mag_detectable(mw, min_stations_p=2, min_stations_s=4,
                              wave_mode='PS')[0] == pytest.approx(0.9)


class TestGuards:
    def test_rejects_more_stations_than_available(self):
        """Regression guard: the check must look at the station axis, not the grid
        axis. This array has 2 grid points and 3 stations."""
        mw = np.full((2, 2, 3), 0.0)
        with pytest.raises(ValueError):
            mag_detectable(mw, min_stations_p=4, wave_mode='P')

    def test_accepts_exactly_all_stations(self):
        mw = np.full((2, 2, 3), 0.0)
        assert mag_detectable(mw, min_stations_p=3, wave_mode='P').shape == (2,)

    def test_rejects_non_positive(self):
        mw = np.full((2, 2, 3), 0.0)
        with pytest.raises(ValueError):
            mag_detectable(mw, min_stations_p=0, wave_mode='P')

    def test_only_the_requested_branch_is_checked(self):
        """An impossible S count must not break a P-only request."""
        mw = np.full((2, 2, 3), 0.0)
        assert mag_detectable(mw, min_stations_p=2, min_stations_s=99,
                              wave_mode='P').shape == (2,)

    def test_rejects_invalid_wave_mode(self):
        mw = np.full((2, 2, 3), 0.0)
        with pytest.raises(ValueError):
            mag_detectable(mw, wave_mode='Q')

    def test_check_min_stations_directly(self):
        check_min_stations(min_stations_p=3, min_stations_s=3, n_stations=3, wave_mode='PS')
        with pytest.raises(ValueError):
            check_min_stations(min_stations_p=4, min_stations_s=1, n_stations=3, wave_mode='PS')
        # None means "unset" and is skipped
        check_min_stations(min_stations_p=None, min_stations_s=None, n_stations=1, wave_mode='PS')
