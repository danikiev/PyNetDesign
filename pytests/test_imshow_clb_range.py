"""The imshow sensitivity slice applies clb_range to the image and its colorbar (#10)."""
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pynetdesign.visualization.sensitivity import plot_sensitivity_slice

GX = np.array([0.0, 80.0, 160.0, 240.0])
GZ = np.array([0.0, 40.0, 80.0])
VALUES = np.linspace(-0.5, 1.5, GX.size * GZ.size).reshape(GX.size, GZ.size)
CLB_RANGE = (-3.0, 3.0)


@pytest.fixture(autouse=True)
def _no_show(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    yield
    plt.close('all')


def test_imshow_uses_clb_range():
    _, ax, _, cbar = plot_sensitivity_slice(VALUES, xi=GX, zi=GZ, clb_range=CLB_RANGE,
                                            plt_style='imshow', plt_contours=False)
    assert ax.images[0].get_clim() == pytest.approx(CLB_RANGE)
    assert cbar.ax.get_ylim() == pytest.approx(CLB_RANGE)


def test_imshow_without_clb_range_scales_to_data():
    _, ax, _, cbar = plot_sensitivity_slice(VALUES, xi=GX, zi=GZ,
                                            plt_style='imshow', plt_contours=False)
    assert ax.images[0].get_clim() == pytest.approx((VALUES.min(), VALUES.max()))
    assert cbar.ax.get_ylim() == pytest.approx((VALUES.min(), VALUES.max()))


def test_contourf_levels_span_clb_range():
    _, _, _, cbar = plot_sensitivity_slice(VALUES, xi=GX, zi=GZ, clb_range=CLB_RANGE,
                                           plt_style='contourf', plt_contours=False)
    levels = cbar.mappable.levels
    assert (levels[0], levels[-1]) == pytest.approx(CLB_RANGE)
