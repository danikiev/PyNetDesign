"""Tests for receiver projection of the arriving polarization.

For a vertical cable the projection factors reduce to the familiar
|cos(theta)| for P and |sin(theta)| for SV, where theta is the angle between the
propagation direction and the cable, and SH cannot be recorded at all. These
closed forms are used as the reference here.
"""
import numpy as np
import pandas as pd
import pytest

from pynetdesign.modelling.utils import (
    geometry_requires_receiver_projection,
    get_phase_station_directionality,
    get_ray_station_directionality,
)


def vertical_cable(n=5, spacing=100.0):
    """Vertical cable at the origin, Z increasing downwards."""
    return np.column_stack([np.zeros(n), np.zeros(n), np.arange(n) * spacing])


def das_geometry(station_coords, gauge_length=10.0):
    df = pd.DataFrame({
        'Name': [f"C{i+1}" for i in range(len(station_coords))],
        'X': station_coords[:, 0],
        'Y': station_coords[:, 1],
        'Z': station_coords[:, 2],
        'NoiseLevel': np.full(len(station_coords), 1e-9),
    })
    df.attrs['noise_type'] = 'strain rate'
    df.attrs['gauge_length'] = gauge_length
    return df


class TestVerticalCable:
    @pytest.mark.parametrize("theta_deg", [15.0, 30.0, 45.0, 60.0, 75.0])
    def test_p_and_sv_match_closed_forms(self, theta_deg):
        theta = np.radians(theta_deg)
        stations = vertical_cable()
        # One grid point at angle theta from the cable, seen from the first channel
        r = 1000.0
        grid = np.array([[r * np.sin(theta), 0.0, stations[0, 2] + r * np.cos(theta)]])

        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, force_tangent=True)

        assert coefficients["P"][0, 0] == pytest.approx(1.0 / abs(np.cos(theta)), rel=1e-12)
        assert coefficients["SV"][0, 0] == pytest.approx(1.0 / abs(np.sin(theta)), rel=1e-12)

    def test_sh_is_unobservable_on_a_vertical_cable(self):
        """SH is horizontal and perpendicular to the ray plane, so a vertical
        cable has no sensitivity to it at all."""
        stations = vertical_cable()
        grid = np.array([[500.0, 0.0, 250.0], [1500.0, 200.0, 800.0]])
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, force_tangent=True)
        assert np.all(np.isnan(coefficients["SH"]))

    def test_axial_ray_is_blind_to_sv(self):
        """A ray travelling along the cable gives sin(theta) = 0, so SV cannot be
        recorded. This is the low-sensitivity zone directly below a vertical array."""
        stations = vertical_cable()
        grid = np.array([[0.0, 0.0, 2000.0]])       # straight below the cable
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, force_tangent=True)
        assert np.all(np.isnan(coefficients["SV"]))
        assert np.allclose(coefficients["P"], 1.0)   # fully axial, perfect for P

    def test_broadside_ray_is_blind_to_p(self):
        """A ray arriving perpendicular to the cable gives cos(theta) = 0."""
        stations = vertical_cable()
        grid = np.array([[1000.0, 0.0, stations[2, 2]]])   # level with channel 3
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, force_tangent=True)
        assert np.isnan(coefficients["P"][0, 2])
        assert coefficients["SV"][0, 2] == pytest.approx(1.0, rel=1e-12)

    def test_coefficients_are_at_least_one(self):
        """Projection can only reduce the recorded amplitude, so the correction
        applied to the threshold is never smaller than one."""
        stations = vertical_cable()
        grid = np.array([[300.0, 100.0, 150.0], [1200.0, -400.0, 900.0]])
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, force_tangent=True)
        for phase in ("P", "SV"):
            finite = coefficients[phase][np.isfinite(coefficients[phase])]
            assert np.all(finite >= 1.0 - 1e-12)


class TestGeometryDrivenProjection:
    def test_das_geometry_requires_projection(self):
        stations = vertical_cable()
        assert geometry_requires_receiver_projection(das_geometry(stations)) is True

    def test_plain_station_geometry_does_not(self):
        df = pd.DataFrame({'Name': ['A', 'B'], 'X': [0.0, 1.0], 'Y': [0.0, 0.0],
                           'Z': [0.0, 0.0], 'NoiseLevel': [1e-9, 1e-9]})
        df.attrs['noise_type'] = 'velocity'
        assert geometry_requires_receiver_projection(df) is False

    def test_none_geometry_does_not(self):
        assert geometry_requires_receiver_projection(None) is False

    def test_three_component_stations_are_not_projected(self):
        """A 3C station records the full vector, so no amplitude is lost."""
        stations = vertical_cable(n=3)
        df = pd.DataFrame({'Name': ['A', 'B', 'C'],
                           'X': stations[:, 0], 'Y': stations[:, 1], 'Z': stations[:, 2],
                           'NoiseLevel': np.full(3, 1e-9),
                           'Components': ['3C', '3C', '3C']})
        df.attrs['noise_type'] = 'velocity'
        grid = np.array([[500.0, 0.0, 250.0]])
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, geometry_df=df)
        for phase in ("P", "SV", "SH"):
            assert np.allclose(coefficients[phase], 1.0)

    def test_vertical_component_station_is_projected(self):
        """A Z-only station sees the vertical projection of the polarization."""
        stations = vertical_cable(n=2)
        df = pd.DataFrame({'Name': ['A', 'B'],
                           'X': stations[:, 0], 'Y': stations[:, 1], 'Z': stations[:, 2],
                           'NoiseLevel': np.full(2, 1e-9),
                           'Components': ['Z', '3C']})
        df.attrs['noise_type'] = 'velocity'
        theta = np.radians(35.0)
        r = 1000.0
        grid = np.array([[r * np.sin(theta), 0.0, r * np.cos(theta)]])
        coefficients = get_phase_station_directionality(
            station_coords=stations, grid_coords=grid, geometry_df=df)
        # Station 0 records only Z, so P is scaled by 1/|cos(theta)|
        assert coefficients["P"][0, 0] == pytest.approx(1.0 / abs(np.cos(theta)), rel=1e-12)
        # Station 1 is 3C and therefore unaffected
        assert coefficients["P"][0, 1] == pytest.approx(1.0)

    def test_rejects_invalid_components(self):
        stations = vertical_cable(n=2)
        df = pd.DataFrame({'Name': ['A', 'B'],
                           'X': stations[:, 0], 'Y': stations[:, 1], 'Z': stations[:, 2],
                           'NoiseLevel': np.full(2, 1e-9),
                           'Components': ['Z', 'N']})
        df.attrs['noise_type'] = 'velocity'
        with pytest.raises(ValueError):
            get_phase_station_directionality(station_coords=stations,
                                             grid_coords=np.array([[100.0, 0.0, 50.0]]),
                                             geometry_df=df)

    def test_rejects_components_on_a_das_geometry(self):
        stations = vertical_cable(n=3)
        df = das_geometry(stations)
        df['Components'] = ['Z', 'Z', 'Z']
        with pytest.raises(ValueError):
            get_phase_station_directionality(station_coords=stations,
                                             grid_coords=np.array([[100.0, 0.0, 50.0]]),
                                             geometry_df=df)


class TestValidation:
    def test_rejects_unknown_phase(self):
        with pytest.raises(ValueError):
            get_phase_station_directionality(station_coords=vertical_cable(),
                                             grid_coords=np.array([[100.0, 0.0, 50.0]]),
                                             phases=("P", "S"))

    def test_requires_two_stations_for_tangent(self):
        with pytest.raises(ValueError):
            get_phase_station_directionality(
                station_coords=np.array([[0.0, 0.0, 0.0]]),
                grid_coords=np.array([[100.0, 0.0, 50.0]]),
                force_tangent=True)

    def test_strict_nan_check_raises(self):
        stations = vertical_cable()
        grid = np.array([[0.0, 0.0, 2000.0]])   # axial ray, SV unobservable
        with pytest.raises(RuntimeError):
            get_phase_station_directionality(station_coords=stations, grid_coords=grid,
                                             force_tangent=True, strict_nan_check=True)


class TestDeprecatedWrapper:
    def test_warns_and_returns_p_and_sv(self):
        stations = vertical_cable()
        theta = np.radians(40.0)
        r = 1000.0
        grid = np.array([[r * np.sin(theta), 0.0, r * np.cos(theta)]])
        with pytest.warns(DeprecationWarning):
            dir_p, dir_s = get_ray_station_directionality(station_coords=stations,
                                                          grid_coords=grid)
        assert dir_p[0, 0] == pytest.approx(1.0 / abs(np.cos(theta)), rel=1e-12)
        assert dir_s[0, 0] == pytest.approx(1.0 / abs(np.sin(theta)), rel=1e-12)
