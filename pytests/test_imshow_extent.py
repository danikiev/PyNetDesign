"""The imshow sensitivity slice centres each pixel on its grid node (#9)."""
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pynetdesign.visualization.sensitivity import plot_sensitivity_slice
from pynetdesign.visualization.utils import get_imshow_extent

GX = np.array([0.0, 80.0, 160.0, 240.0])
GZ = np.array([0.0, 40.0, 80.0])
VALUES = np.arange(GX.size * GZ.size, dtype=float).reshape(GX.size, GZ.size)


@pytest.fixture(autouse=True)
def _no_show(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    yield
    plt.close('all')


def _pixel_centres(image):
    """Pixel centres of an image drawn with origin='lower'."""
    n_rows, n_cols = image.get_array().shape
    left, right, bottom, top = image.get_extent()
    cols = left + (np.arange(n_cols) + 0.5) * (right - left) / n_cols
    rows = bottom + (np.arange(n_rows) + 0.5) * (top - bottom) / n_rows
    return cols, rows


def test_get_imshow_extent_reaches_half_a_step_beyond_the_nodes():
    assert get_imshow_extent(GX, GZ) == pytest.approx((-40.0, 280.0, -20.0, 100.0))
    assert get_imshow_extent(GX, GZ[::-1]) == pytest.approx((-40.0, 280.0, 100.0, -20.0))


def test_pixel_centres_on_grid_nodes():
    _, ax, _, _ = plot_sensitivity_slice(VALUES, xi=GX, zi=GZ,
                                         plt_style='imshow', plt_contours=False)
    image = ax.images[0]
    cols, rows = _pixel_centres(image)
    np.testing.assert_allclose(cols, GX)
    np.testing.assert_allclose(rows, GZ)
    assert ax.get_xlim() == pytest.approx((GX[0], GX[-1]))
    assert ax.get_ylim() == pytest.approx((GZ[-1], GZ[0]))
    # Row 0 of the image holds the values of the first node
    np.testing.assert_allclose(image.get_array()[0], VALUES[:, 0])


def test_descending_vector_keeps_rows_at_their_nodes():
    gz = GZ[::-1]
    values = VALUES[:, ::-1]
    _, ax, _, _ = plot_sensitivity_slice(values, xi=GX, zi=gz,
                                         plt_style='imshow', plt_contours=False)
    image = ax.images[0]
    _, rows = _pixel_centres(image)
    np.testing.assert_allclose(rows, gz)
    np.testing.assert_allclose(image.get_array()[0], values[:, 0])
