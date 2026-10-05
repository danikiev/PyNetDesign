"""End-to-end tests of phase-resolved magnitude sensitivity on a small grid.

These pin the behaviour introduced with SV/SH support: the composite S mode keeps
the more detectable branch, joint detection takes the stricter branch, and the
radiation-pattern and free-surface options shift the result by known amounts.
"""
import numpy as np
import pandas as pd
import pytest

from pynetdesign.modelling.homo import mag_sensitivity_grid
from pynetdesign.modelling.utils import (
    RAD_PATTERN_SV_DEFAULT,
    generate_grid,
)

VELOCITY = pd.DataFrame({
    'Depth': [0], 'Vp': [2370.0], 'VpVsRatio': [2.0], 'Qp': [100.0], 'Qs': [100.0],
    'Rho': [2500.0], 'Ep': [0.0], 'Dt': [0.0], 'Gm': [0.0],
})


def das_geometry(n=20, spacing=50.0, noise=1.95e-9, gauge_length=10.0):
    """Vertical DAS cable at the origin, Z increasing downwards."""
    z = np.arange(n) * spacing
    df = pd.DataFrame({
        'Name': [f"C{i+1}" for i in range(n)],
        'X': np.zeros(n), 'Y': np.zeros(n), 'Z': z,
        'NoiseLevel': np.full(n, noise),
    })
    df.attrs['noise_type'] = 'strain rate'
    df.attrs['gauge_length'] = gauge_length
    df.attrs['_is_combined'] = False
    return df


def surface_geometry(noise=1e-10):
    """Three 3C receivers on the free surface."""
    df = pd.DataFrame({
        'Name': ['A', 'B', 'C'],
        'X': [0.0, 1000.0, 500.0], 'Y': [0.0, 0.0, 866.0], 'Z': [0.0, 0.0, 0.0],
        'NoiseLevel': np.full(3, noise),
    })
    df.attrs['noise_type'] = 'velocity'
    df.attrs['_is_combined'] = False
    return df


def small_grid():
    return generate_grid(x=np.arange(200.0, 1200.0, 200.0),
                         y=np.array([0.0]),
                         z=np.arange(100.0, 900.0, 200.0))


def run(geometry_df, wave_mode, grid=None, **kwargs):
    grid = small_grid() if grid is None else grid
    n = len(geometry_df)
    amps = geometry_df['NoiseLevel'].to_numpy() * 2.0
    gauge = geometry_df.attrs.get('gauge_length')
    if gauge is not None:
        amps = amps * gauge
    kwargs.setdefault('min_stations_p', 3)
    kwargs.setdefault('min_stations_s', 3)
    return mag_sensitivity_grid(grid_coords=grid, velocity_df=VELOCITY,
                                geometry_df=geometry_df,
                                min_amps_p=amps, min_amps_s=amps,
                                wave_mode=wave_mode, **kwargs)


class TestCompositeS:
    def test_s_equals_sv_on_a_vertical_cable(self):
        """A vertical cable cannot record SH, so the composite S mode must fall
        back to SV everywhere."""
        geom = das_geometry()
        s = run(geom, 'S', fs_mode='off')
        sv = run(geom, 'SV', fs_mode='off')
        np.testing.assert_allclose(s, sv, rtol=1e-12)

    def test_sh_alone_is_undetectable_on_a_vertical_cable(self):
        sh = run(das_geometry(), 'SH', fs_mode='off')
        assert np.all(np.isnan(sh))

    def test_composite_s_is_never_worse_than_either_branch(self):
        geom = das_geometry()
        s = run(geom, 'S', fs_mode='off')
        sv = run(geom, 'SV', fs_mode='off')
        finite = np.isfinite(s) & np.isfinite(sv)
        assert np.all(s[finite] <= sv[finite] + 1e-12)


class TestJointMode:
    def test_ps_is_the_stricter_of_p_and_s(self):
        geom = das_geometry()
        p = run(geom, 'P', fs_mode='off')
        s = run(geom, 'S', fs_mode='off')
        ps = run(geom, 'PS', fs_mode='off')
        np.testing.assert_allclose(ps, np.maximum(p, s), rtol=1e-12)


class TestRadiationPatternOverride:
    def test_combined_s_override_shifts_by_a_known_amount(self):
        """Passing 0.63, the combined S value, reproduces results computed with
        that convention. Since M0 is inversely proportional to R, the shift is
        2/3*log10(0.63 / sqrt(7/30))."""
        geom = das_geometry()
        default = run(geom, 'SV', fs_mode='off')
        overridden = run(geom, 'SV', fs_mode='off', rad_pattern_s=0.63)
        expected = -2 / 3 * np.log10(0.63 / RAD_PATTERN_SV_DEFAULT)
        finite = np.isfinite(default) & np.isfinite(overridden)
        np.testing.assert_allclose(overridden[finite] - default[finite],
                                   expected, rtol=1e-10)
        assert expected == pytest.approx(-0.0769, abs=1e-4)

    def test_p_override_shifts_p_only(self):
        geom = das_geometry()
        default = run(geom, 'P', fs_mode='off')
        overridden = run(geom, 'P', fs_mode='off', rad_pattern_p=0.52)
        finite = np.isfinite(default)
        expected = -2 / 3 * np.log10(0.52 / np.sqrt(4 / 15))
        np.testing.assert_allclose(overridden[finite] - default[finite],
                                   expected, rtol=1e-10)
        assert expected == pytest.approx(-0.00201, abs=1e-5)

    def test_dict_override(self):
        geom = das_geometry()
        a = run(geom, 'SV', fs_mode='off', rad_pattern_s=0.63)
        b = run(geom, 'SV', fs_mode='off', rad_patterns={'SV': 0.63})
        np.testing.assert_allclose(a, b, rtol=1e-12)


class TestFreeSurfaceEffect:
    def test_surface_receivers_gain_exactly_two_thirds_log_two(self):
        geom = surface_geometry()
        off = run(geom, 'P', fs_mode='off')
        on = run(geom, 'P', fs_mode='on')
        expected = -2 / 3 * np.log10(2.0)
        np.testing.assert_allclose(on - off, expected, rtol=1e-12)

    def test_auto_matches_on_for_an_all_surface_geometry(self):
        geom = surface_geometry()
        auto = run(geom, 'P', fs_mode='auto')
        on = run(geom, 'P', fs_mode='on')
        np.testing.assert_allclose(auto, on, rtol=1e-12)

    def test_auto_matches_off_for_a_downhole_geometry(self):
        """No channel of this cable is at the surface, so 'auto' changes nothing."""
        geom = das_geometry(n=20, spacing=50.0)
        geom['Z'] = geom['Z'] + 100.0     # move the whole cable below the surface
        auto = run(geom, 'P', fs_mode='auto')
        off = run(geom, 'P', fs_mode='off')
        np.testing.assert_allclose(auto, off, rtol=1e-12)

    def test_surface_column_overrides_depth(self):
        geom = surface_geometry()
        geom['Surface'] = [0.0, 0.0, 0.0]
        auto = run(geom, 'P', fs_mode='auto')
        off = run(geom, 'P', fs_mode='off')
        np.testing.assert_allclose(auto, off, rtol=1e-12)


class TestWaveModeValidation:
    def test_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            run(das_geometry(), 'Q')

    def test_rejects_bad_fs_mode(self):
        with pytest.raises(ValueError):
            run(das_geometry(), 'P', fs_mode='maybe')

    def test_rejects_too_many_required_stations(self):
        with pytest.raises(ValueError):
            run(das_geometry(n=5), 'P', min_stations_p=99)
