"""Tests for the synthetic geometry generators and the geometry writers."""
import numpy as np
import pandas as pd
import pytest

import pynetdesign.modelling as pndmod
from pynetdesign.modelling.geometry import (
    generate_borehole_geometry,
    generate_geometry,
)
from pynetdesign.modelling.io import (
    combine_geometry,
    decimate_geometry,
    read_geometry,
    save_geometry,
)

STATION_HEADER = "Name\tNorthing(m)\tEasting(m)\tElevation(m)\tNoiseLevel(m/s)"


@pytest.fixture
def written(tmp_path):
    """Write geometry lines to a temporary file and read them back."""
    def _written(lines, name="geometry.txt"):
        path = tmp_path / name
        save_geometry(lines, path)
        return read_geometry(str(path))
    return _written


class TestGenerators:
    @pytest.mark.parametrize("shape", ["line", "zigzag", "L", "square", "double_line"])
    def test_surface_shapes_are_readable(self, shape, written):
        lines = generate_geometry(mode="surface", cable_length=3000.0, spacing=50.0,
                                  surface_shape=shape)
        df = written(lines, f"surface_{shape}.txt")
        assert len(df) > 1
        assert {'X', 'Y', 'Z', 'NoiseLevel'}.issubset(df.columns)

    def test_borehole_channel_count_and_spacing(self, written):
        lines = generate_geometry(mode="borehole", cable_length=999.0, spacing=1.0,
                                  noise_level=1.95e-9, gauge_length=10.0)
        df = written(lines, "borehole.txt")
        assert len(df) == 1000
        assert df.attrs['gauge_length'] == pytest.approx(10.0)
        assert df.attrs['noise_type'] == 'strain rate'
        np.testing.assert_allclose(np.diff(df['Z']), 1.0)

    def test_vertical_borehole_is_a_straight_column(self):
        coords = np.array(generate_borehole_geometry(
            center_x=100.0, center_y=-50.0, spacing=25.0, start_depth=0.0,
            cable_length=500.0, azimuth=0.0, dip=90.0))
        assert np.allclose(coords[:, 0], 100.0)
        assert np.allclose(coords[:, 1], -50.0)
        assert coords[0, 2] == pytest.approx(0.0)
        assert coords[-1, 2] == pytest.approx(-500.0)

    def test_inclined_borehole_steps_out(self):
        """A 60 degree dip advances horizontally by cos(60) per unit of cable."""
        coords = np.array(generate_borehole_geometry(
            center_x=0.0, center_y=0.0, spacing=100.0, start_depth=0.0,
            cable_length=1000.0, azimuth=90.0, dip=60.0))
        measured = 1000.0
        assert coords[-1, 0] == pytest.approx(measured * np.cos(np.radians(60.0)))
        assert coords[-1, 1] == pytest.approx(0.0, abs=1e-9)
        assert coords[-1, 2] == pytest.approx(-measured * np.sin(np.radians(60.0)))

    def test_darkfiber_defaults_work_for_any_cable_length(self):
        """The default turns are fractions of the cable, so the default layout is
        valid whatever length is requested."""
        for length in (4000.0, 5000.0, 24000.0):
            lines = generate_geometry(mode="darkfiber", cable_length=length,
                                      spacing=100.0)
            assert len(lines) > 2

    def test_darkfiber_rejects_turns_beyond_the_cable(self):
        with pytest.raises(ValueError):
            generate_geometry(mode="darkfiber", cable_length=1000.0, spacing=50.0,
                              turns={5000.0: 90.0})

    def test_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            generate_geometry(mode="spiral", cable_length=1000.0)

    def test_rejects_unknown_surface_shape(self):
        with pytest.raises(ValueError):
            generate_geometry(mode="surface", cable_length=1000.0,
                              surface_shape="triangle")


class TestSaveGeometry:
    def test_writes_generated_lines(self, tmp_path):
        lines = generate_geometry(mode="borehole", cable_length=200.0, spacing=50.0)
        path = tmp_path / "out.txt"
        save_geometry(lines, path)
        assert path.read_text().splitlines() == lines

    def test_dataframe_round_trip(self, tmp_path):
        lines = generate_geometry(mode="borehole", cable_length=500.0, spacing=25.0,
                                  noise_level=1.95e-9, gauge_length=10.0)
        first = tmp_path / "a.txt"
        save_geometry(lines, first)
        df = read_geometry(str(first))

        second = tmp_path / "b.txt"
        save_geometry(df, second)
        back = read_geometry(str(second))

        for col in ('X', 'Y', 'Z', 'NoiseLevel'):
            np.testing.assert_allclose(df[col], back[col])
        assert back.attrs['gauge_length'] == pytest.approx(df.attrs['gauge_length'])
        assert back.attrs['noise_type'] == df.attrs['noise_type']

    def test_elevation_sign_survives_the_round_trip(self, tmp_path, written):
        df = written([STATION_HEADER, "A\t0\t0\t-250\t1e-10"], "one.txt")
        assert df['Z'][0] == pytest.approx(250.0)     # Z is depth, positive down
        out = tmp_path / "one_out.txt"
        save_geometry(df, out)
        assert "-250" in out.read_text()              # written back as elevation
        assert read_geometry(str(out))['Z'][0] == pytest.approx(250.0)

    @pytest.mark.parametrize("noise_type,unit", [
        ('velocity', 'm/s'), ('acceleration', 'm/s^2'),
        ('displacement', 'm'), ('strain rate', '1/s'),
    ])
    def test_noise_unit_is_written_from_the_noise_type(self, tmp_path, noise_type, unit):
        df = pd.DataFrame({'Name': ['A'], 'X': [0.0], 'Y': [0.0], 'Z': [0.0],
                           'NoiseLevel': [1e-9]})
        df.attrs['noise_type'] = noise_type
        df.attrs['_is_combined'] = False
        path = tmp_path / "n.txt"
        save_geometry(df, path)
        assert f"NoiseLevel({unit})" in path.read_text().splitlines()[0]

    def test_rejects_geometry_without_noise_metadata(self, tmp_path):
        df = pd.DataFrame({'X': [0.0], 'Y': [0.0], 'Z': [0.0], 'NoiseLevel': [1e-9]})
        df.attrs['_is_combined'] = False
        with pytest.raises(ValueError):
            save_geometry(df, tmp_path / "bad.txt")

    def test_rejects_missing_columns(self, tmp_path):
        df = pd.DataFrame({'X': [0.0], 'Y': [0.0]})
        df.attrs['noise_type'] = 'velocity'
        df.attrs['_is_combined'] = False
        with pytest.raises(ValueError):
            save_geometry(df, tmp_path / "bad.txt")

    def test_rejects_combined_geometry(self, tmp_path, written):
        a = written([STATION_HEADER, "A\t0\t0\t0\t1e-10"], "a.txt")
        b = written([STATION_HEADER, "B\t100\t0\t0\t1e-10"], "b.txt")
        with pytest.raises(ValueError):
            save_geometry(combine_geometry(a, b), tmp_path / "combined.txt")

    def test_rejects_wrong_type(self, tmp_path):
        with pytest.raises(TypeError):
            save_geometry("not a list", tmp_path / "bad.txt")
        with pytest.raises(TypeError):
            save_geometry([1, 2, 3], tmp_path / "bad.txt")

    def test_rejects_empty_lines(self, tmp_path):
        with pytest.raises(ValueError):
            save_geometry([], tmp_path / "bad.txt")


class TestOptionalColumns:
    def test_surface_and_components_round_trip(self, tmp_path, written):
        lines = [
            STATION_HEADER + "\tSurface\tComponents",
            "A\t0\t0\t0\t1e-10\t1.0\t3C",
            "B\t1000\t0\t-500\t1e-10\t0.0\tZ",
            "C\t500\t866\t0\t1e-10\t0.5\t3C",
        ]
        df = written(lines, "stations.txt")
        assert list(df['Surface']) == [1.0, 0.0, 0.5]
        assert list(df['Components']) == ['3C', 'Z', '3C']

        out = tmp_path / "stations_out.txt"
        save_geometry(df, out)
        back = read_geometry(str(out))
        assert list(back['Surface']) == [1.0, 0.0, 0.5]
        assert list(back['Components']) == ['3C', 'Z', '3C']

    def test_surface_must_be_a_weight(self, written):
        with pytest.raises(ValueError):
            written([STATION_HEADER + "\tSurface", "A\t0\t0\t0\t1e-10\t1.5"], "bad.txt")

    def test_components_must_be_3c_or_z(self, written):
        with pytest.raises(ValueError):
            written([STATION_HEADER + "\tComponents", "A\t0\t0\t0\t1e-10\tN"], "bad.txt")

    def test_components_not_allowed_on_das(self, written):
        lines = [
            "Northing(m)\tEasting(m)\tElevation(m)\tNoiseLevel(1/s)\tComponents\tGaugeLength=10(m)",
            "0\t0\t0\t1e-9\tZ",
        ]
        with pytest.raises(ValueError):
            written(lines, "das_components.txt")

    def test_save_rejects_components_on_das(self, tmp_path, written):
        df = written([
            "Northing(m)\tEasting(m)\tElevation(m)\tNoiseLevel(1/s)\tGaugeLength=10(m)",
            "0\t0\t0\t1e-9", "0\t0\t-10\t1e-9",
        ], "das.txt")
        df['Components'] = ['Z', 'Z']
        with pytest.raises(ValueError):
            save_geometry(df, tmp_path / "bad.txt")


class TestDecimate:
    def test_keeps_every_nth_station(self, written):
        lines = generate_geometry(mode="borehole", cable_length=990.0, spacing=10.0,
                                  gauge_length=10.0, noise_level=1e-9)
        df = written(lines, "das.txt")
        dec = decimate_geometry(df, 5)
        assert len(dec) == int(np.ceil(len(df) / 5))
        np.testing.assert_allclose(dec['Z'].to_numpy(), df['Z'].to_numpy()[::5])

    def test_preserves_attributes(self, written):
        lines = generate_geometry(mode="borehole", cable_length=200.0, spacing=10.0,
                                  gauge_length=10.0, noise_level=1e-9)
        df = written(lines, "das.txt")
        dec = decimate_geometry(df, 2)
        assert dec.attrs['gauge_length'] == df.attrs['gauge_length']
        assert dec.attrs['noise_type'] == df.attrs['noise_type']

    def test_step_of_one_is_a_copy(self, written):
        df = written([STATION_HEADER, "A\t0\t0\t0\t1e-10", "B\t10\t0\t0\t1e-10"], "s.txt")
        dec = decimate_geometry(df, 1)
        assert len(dec) == len(df)
        assert dec is not df

    @pytest.mark.parametrize("bad", [0, -1, 2.5, "5", True])
    def test_rejects_invalid_step(self, bad, written):
        df = written([STATION_HEADER, "A\t0\t0\t0\t1e-10"], "s.txt")
        with pytest.raises(ValueError):
            decimate_geometry(df, bad)

    def test_rejects_combined_geometry(self, written):
        a = written([STATION_HEADER, "A\t0\t0\t0\t1e-10"], "a.txt")
        b = written([STATION_HEADER, "B\t100\t0\t0\t1e-10"], "b.txt")
        with pytest.raises(ValueError):
            decimate_geometry(combine_geometry(a, b), 2)


class TestGeneratorsAreUsable:
    def test_generated_das_drives_a_sensitivity_computation(self, written):
        """The generators feed straight into the modelling path."""
        lines = generate_geometry(mode="borehole", cable_length=500.0, spacing=50.0,
                                  noise_level=1.95e-9, gauge_length=10.0)
        geometry_df = written(lines, "das.txt")
        velocity_df = pd.DataFrame({
            'Depth': [0], 'Vp': [2370.0], 'VpVsRatio': [2.0], 'Qp': [100.0],
            'Qs': [100.0], 'Rho': [2500.0], 'Ep': [0.0], 'Dt': [0.0], 'Gm': [0.0]})
        velocity_df.attrs['model_type'] = 'homo'
        params = pndmod.classes.DetectionParameters(
            min_SNR_p=2, min_SNR_s=2, min_stations_p=3, min_stations_s=3)
        grid = pndmod.utils.generate_grid(x=np.array([500.0, 1000.0]),
                                          y=np.array([0.0]),
                                          z=np.array([250.0, 500.0]))
        mw = pndmod.core.get_mag_sensitivity(grid_coords=grid, geometry_df=geometry_df,
                                             velocity_df=velocity_df, params=params,
                                             wave_mode='PS')
        assert mw.shape == (4,)
        assert np.all(np.isfinite(mw))
