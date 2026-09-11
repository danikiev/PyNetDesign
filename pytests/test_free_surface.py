"""Tests for the per-station free surface amplification.

A receiver at the free surface records approximately twice the amplitude of the
incident wave, which lowers its detection threshold by 2/3*log10(2) ~ 0.201
magnitude units. The correction must apply only to receivers that are actually at
the surface, so that a geometry mixing surface and downhole receivers is handled
correctly.
"""
import numpy as np
import pytest

from pynetdesign.modelling.utils import compute_free_surface_coefficients

GRID = np.array([[500.0, 0.0, 250.0], [1500.0, 200.0, 900.0]])


def mixed_geometry():
    """Two receivers at the surface and two at depth."""
    return np.array([
        [0.0, 0.0, 0.0],
        [100.0, 0.0, 0.5],      # within the default 1 m deviation
        [0.0, 0.0, 500.0],
        [100.0, 0.0, 1000.0],
    ])


class TestModes:
    def test_auto_gates_on_depth(self):
        fs_p, fs_s = compute_free_surface_coefficients(
            station_coords=mixed_geometry(), grid_coords=GRID, fs_mode='auto')
        assert fs_p.shape == (len(GRID), 4)
        np.testing.assert_allclose(fs_p[0], [2.0, 2.0, 1.0, 1.0])
        np.testing.assert_allclose(fs_p, fs_s)

    def test_off_disables_everything(self):
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=mixed_geometry(), grid_coords=GRID, fs_mode='off')
        assert np.all(fs_p == 1.0)

    def test_on_ignores_supplied_weights(self):
        """'on' re-derives the indicator from depth rather than trusting weights."""
        weights = np.zeros(4)
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=mixed_geometry(), grid_coords=GRID,
            station_coords_on_surface=weights, fs_mode='on')
        np.testing.assert_allclose(fs_p[0], [2.0, 2.0, 1.0, 1.0])

    def test_auto_honours_supplied_weights(self):
        weights = np.array([0.0, 1.0, 1.0, 0.0])
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=mixed_geometry(), grid_coords=GRID,
            station_coords_on_surface=weights, fs_mode='auto')
        np.testing.assert_allclose(fs_p[0], [1.0, 2.0, 2.0, 1.0])

    def test_fractional_weights_blend(self):
        weights = np.array([0.5, 0.25, 0.0, 1.0])
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=mixed_geometry(), grid_coords=GRID,
            station_coords_on_surface=weights, fs_mode='auto')
        np.testing.assert_allclose(fs_p[0], [1.5, 1.25, 1.0, 2.0])

    def test_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            compute_free_surface_coefficients(station_coords=mixed_geometry(),
                                              grid_coords=GRID, fs_mode='sometimes')


class TestLevelAndDeviation:
    def test_level_shifts_the_surface(self):
        """fs_level is measured upwards, Z downwards, so a level of 100 m puts the
        surface at Z = -100 m."""
        stations = np.array([[0.0, 0.0, -100.0], [0.0, 0.0, 0.0]])
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=stations, grid_coords=GRID, fs_mode='auto', fs_level=100.0)
        np.testing.assert_allclose(fs_p[0], [2.0, 1.0])

    def test_deviation_widens_the_band(self):
        stations = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 5.0], [0.0, 0.0, 50.0]])
        tight, _ = compute_free_surface_coefficients(
            station_coords=stations, grid_coords=GRID, fs_mode='auto', fs_deviation=1.0)
        loose, _ = compute_free_surface_coefficients(
            station_coords=stations, grid_coords=GRID, fs_mode='auto', fs_deviation=10.0)
        np.testing.assert_allclose(tight[0], [2.0, 1.0, 1.0])
        np.testing.assert_allclose(loose[0], [2.0, 2.0, 1.0])

    def test_rejects_negative_deviation(self):
        with pytest.raises(ValueError):
            compute_free_surface_coefficients(station_coords=mixed_geometry(),
                                              grid_coords=GRID, fs_deviation=-1.0)

    def test_rejects_non_scalar_level(self):
        with pytest.raises(ValueError):
            compute_free_surface_coefficients(station_coords=mixed_geometry(),
                                              grid_coords=GRID,
                                              fs_level=np.array([0.0, 1.0]))


class TestWeightValidation:
    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError):
            compute_free_surface_coefficients(
                station_coords=mixed_geometry(), grid_coords=GRID,
                station_coords_on_surface=np.zeros(3))

    @pytest.mark.parametrize("bad", [-0.1, 1.1])
    def test_rejects_out_of_range(self, bad):
        with pytest.raises(ValueError):
            compute_free_surface_coefficients(
                station_coords=mixed_geometry(), grid_coords=GRID,
                station_coords_on_surface=np.full(4, bad))


class TestMagnitudeEffect:
    def test_amplification_lowers_threshold_by_expected_amount(self):
        """Doubling the recorded amplitude halves the required moment, which is
        2/3*log10(2) ~ 0.2007 magnitude units."""
        expected = 2 / 3 * np.log10(2.0)
        assert expected == pytest.approx(0.200686, abs=1e-6)

    def test_single_station_input_is_accepted(self):
        fs_p, _ = compute_free_surface_coefficients(
            station_coords=np.array([0.0, 0.0, 0.0]),
            grid_coords=np.array([100.0, 0.0, 50.0]), fs_mode='auto')
        assert fs_p.shape == (1, 1)
        assert fs_p[0, 0] == pytest.approx(2.0)
