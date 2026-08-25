"""The registered RayMap record, its conventions, and the validity rule."""
import numpy as np
import pytest

from phrt.geometry.raymap import (EMISSION_R_OUTER, FIELDS, RayMap, horizon_radius,
                                  read, validity, write)


def _map(n=9, **over):
    z = np.arange(n, dtype=float)
    base = dict(geometry_id="a050_i050", order=1, spin=0.5, inclination_deg=50.0,
                profile="test", alpha=z, beta=z, source_r=z + 3.0,
                source_phi=np.mod(z, 2 * np.pi), winding_phi=z * 3,
                delay=z, coordinate_time=-1000 - z, redshift=np.full(n, 0.9),
                transfer_weight=np.full(n, 0.7), pixel_area=np.full(n, 0.01),
                radial_sign=np.sign(z - 4), valid=np.ones(n, bool))
    base.update(over)
    return RayMap(**base)


def test_roundtrip_preserves_every_field(tmp_path):
    rm = _map()
    back = read(write(rm, tmp_path / "m.h5"))
    for f in FIELDS:
        assert np.array_equal(getattr(rm, f), getattr(back, f))
    assert back.geometry_id == rm.geometry_id and back.order == rm.order


def test_mismatched_field_length_is_refused():
    with pytest.raises(ValueError):
        _map(redshift=np.ones(3))


def test_negative_delay_on_valid_rays_is_refused():
    """delay is a retarded age: non-negative, increasing into the past."""
    with pytest.raises(ValueError, match="non-negative"):
        _map(delay=np.arange(9, dtype=float) - 4.0)


def test_horizon_radius_matches_the_kerr_value():
    assert np.isclose(horizon_radius(0.0), 2.0)
    assert np.isclose(horizon_radius(0.5), 1 + np.sqrt(0.75))
    assert np.isclose(horizon_radius(1.0), 1.0)


def test_validity_excludes_grazing_rays_beyond_the_emission_region():
    """AART returns source radii up to 1e5 M for rays grazing a band edge.
    Admitting those lets a handful of rays dominate every quadrature sum."""
    r = np.array([10.0, 1.5, np.nan, 3.5e5, EMISSION_R_OUTER + 1e-9, 49.0])
    phi = np.zeros(6)
    t = np.full(6, -1000.0)
    mask = np.ones(6, bool)
    v = validity(r, phi, t, 0.5, mask)
    assert list(v) == [True, False, False, False, False, True]


def test_validity_respects_the_band_mask():
    r = np.full(4, 10.0); phi = np.zeros(4); t = np.full(4, -1000.0)
    v = validity(r, phi, t, 0.5, np.array([True, False, True, False]))
    assert list(v) == [True, False, True, False]


def test_validity_never_references_agreement():
    """The rule must depend only on the ray, so it cannot be used to drop rays
    that disagree with a cross-check."""
    import inspect

    src = inspect.getsource(validity)
    # strip the docstring: it is allowed -- and required -- to explain that the
    # rule is independent of any cross-check.
    body = src.split('"""')[-1].lower()
    for word in ("kgeo", "reference", "expected", "tolerance", "agree"):
        assert word not in body


def test_subset_keeps_the_record_consistent():
    rm = _map()
    sub = rm.subset(np.array([0, 2, 4]))
    assert sub.n_rays == 3 and sub.geometry_id == rm.geometry_id


def test_summary_reports_quadrature_area_not_ray_count():
    """Different bands use different dx, so the point count is not the weight."""
    rm = _map(pixel_area=np.full(9, 0.04))
    assert np.isclose(rm.summary()["total_quadrature_area"], 9 * 0.04)
