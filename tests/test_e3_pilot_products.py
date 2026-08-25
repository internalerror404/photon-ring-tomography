"""Properties the pilot ray maps must have. Skipped if they are not built."""
from pathlib import Path

import numpy as np
import pytest

from phrt.geometry.raymap import horizon_radius, read

MAPS = Path(__file__).resolve().parents[1] / "artifacts" / "raymaps"
GEO = "a050_i050"
pytestmark = pytest.mark.skipif(
    not (MAPS / f"{GEO}_n0_core.h5").exists(),
    reason="pilot ray maps not built in this checkout")


@pytest.mark.parametrize("n", [0, 1, 2])
def test_valid_rays_land_inside_the_declared_emission_annulus(n):
    rm = read(MAPS / f"{GEO}_n{n}_core.h5")
    r = rm.source_r[rm.valid]
    assert r.min() > horizon_radius(rm.spin)
    assert r.max() <= 50.0
    assert np.isfinite(r).all()


@pytest.mark.parametrize("n", [0, 1, 2])
def test_source_azimuth_is_wrapped_and_winding_is_its_preimage(n):
    rm = read(MAPS / f"{GEO}_n{n}_core.h5")
    p = rm.source_phi[rm.valid]
    assert p.min() >= 0.0 and p.max() < 2 * np.pi
    assert np.allclose(p, np.mod(rm.winding_phi[rm.valid], 2 * np.pi))


def test_winding_angle_grows_with_order():
    """The unwrapped angle is kept because it accumulates over half-orbits: the
    direct image turns less than once, and each higher order turns further.
    Wrapping alone would erase that, and it is what an azimuthal Fourier basis
    must not see."""
    spans = []
    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEO}_n{n}_core.h5")
        w = rm.winding_phi[rm.valid]
        spans.append(float(w.max() - w.min()))
    assert spans[0] < spans[1] < spans[2]
    # each additional order contributes close to one further turn
    for lo, hi in zip(spans[:-1], spans[1:]):
        assert 0.8 < (hi - lo) / (2 * np.pi) < 1.2


def test_deeper_orders_see_older_epochs():
    """The physical content of the retarded-time ladder: each higher order's
    window starts further into the past than the one below it."""
    starts = []
    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEO}_n{n}_core.h5")
        starts.append(float(rm.delay[rm.valid].min()))
    assert starts[0] < starts[1] < starts[2]


def test_delay_is_measured_from_one_shared_reference():
    """Per-order references would subtract away the ladder between orders."""
    refs = {read(MAPS / f"{GEO}_n{n}_core.h5").metadata["t_reference"]
            for n in (0, 1, 2)}
    assert len(refs) == 1


@pytest.mark.parametrize("n", [0, 1, 2])
def test_pixel_area_is_the_band_resolution_squared(n):
    rm = read(MAPS / f"{GEO}_n{n}_core.h5")
    dx = rm.metadata["dx"]
    assert np.allclose(rm.pixel_area, dx ** 2)


def test_bands_use_different_resolutions():
    """A single dx across orders would misweight the deep, thin bands."""
    areas = {read(MAPS / f"{GEO}_n{n}_core.h5").metadata["dx"] for n in (0, 1, 2)}
    assert len(areas) == 3


@pytest.mark.parametrize("n", [0, 1, 2])
def test_transfer_weight_is_zero_exactly_where_the_ray_is_invalid(n):
    rm = read(MAPS / f"{GEO}_n{n}_core.h5")
    assert np.all(rm.transfer_weight[~rm.valid] == 0.0)
    assert np.all(rm.transfer_weight[rm.valid] > 0.0)


def test_higher_orders_are_fainter():
    """Solid angle times g^3 falls steeply with order. This is the physical
    analogue of the toy's exp(-Gamma n)."""
    w = []
    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEO}_n{n}_core.h5")
        v = rm.valid
        w.append(float(np.sum(rm.pixel_area[v] * rm.transfer_weight[v])))
    assert w[0] > w[1] > w[2]
