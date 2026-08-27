"""An analytic source must enter the operator the way the physics does."""
import numpy as np

from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.operators.physical import PhysicalOperator
from phrt.sources.localized_basis import LocalizedBasis



def _ops():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    rng = np.random.default_rng(20260825)
    raw = [read(root / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
           for n in (0, 1, 2)]
    base = common_count([stratified_subsample(rm, 96, rng) for rm in raw], rng)
    b = LocalizedBasis(1.8660386527060988, 49.98205255591607,
                       -128.82234649196255, 29.0, 4, 7, 8)
    t_obs = np.linspace(0.0, 20.0, 4)
    return b, {"direct": PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                                          design=b.design, dimension=b.dimension),
               "resolved": PhysicalOperator(orders=base, observer_times=t_obs,
                                            design=b.design, dimension=b.dimension),
               "flux": PhysicalOperator(orders=base, observer_times=t_obs,
                                        design=b.design, dimension=b.dimension,
                                        mixer=np.ones((1, 3)), collapse="total_flux")}


def test_forward_analytic_agrees_with_matvec_on_an_in_class_source():
    b, ops = _ops()
    rng = np.random.default_rng(3)
    x = rng.normal(size=b.dimension)
    for name, op in ops.items():
        got = op.forward_analytic(lambda r, p, t: b.design(r, p, t) @ x)
        want = op.matvec(x)
        rel = np.abs(got - want).max() / max(np.abs(want).max(), 1e-300)
        assert rel < 1e-10, (name, rel)


def test_forward_analytic_sees_a_source_the_class_cannot_express():
    # a feature far finer than the class: matvec through the projected
    # coefficients cannot reproduce it, which is the representation floor
    b, ops = _ops()
    op = ops["resolved"]

    def sharp(r, p, t):
        return np.exp(-0.5 * ((t + 100.0) / 0.5) ** 2) * np.cos(11 * p)

    y = op.forward_analytic(sharp)
    assert np.isfinite(y).all() and np.abs(y).max() > 0.0
    A = op.to_dense()
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    assert np.linalg.norm(A @ coef - y) / np.linalg.norm(y) > 1e-6


def test_noise_from_standard_is_unit_variance_after_whitening():
    b, ops = _ops()
    rng = np.random.default_rng(7)
    for name, op in ops.items():
        n_orders, n_rays, n_t = len(op.orders), op.orders[0].n_rays, op.observer_times.size
        draws = np.array([op.noise_from_standard(rng.normal(size=(n_orders, n_rays, n_t)))
                          for _ in range(400)])
        assert abs(draws.std() - 1.0) < 0.05, (name, draws.std())
        assert abs(draws.mean()) < 0.05


def test_arms_are_paired_through_one_physical_draw():
    b, ops = _ops()
    rng = np.random.default_rng(11)
    z = rng.normal(size=(3, ops["resolved"].orders[0].n_rays, 4))
    a = ops["resolved"].noise_from_standard(z)
    c = ops["resolved"].noise_from_standard(z)
    assert np.array_equal(a, c)      # same draw, same noise
    # the direct arm is order 0 of the same physical draw, so its whitened
    # noise is exactly the resolved stack's first channel. That identity is
    # what "paired arms" means; resampling the arms independently would break
    # it and silently inflate every arm-difference interval.
    assert np.array_equal(a[:ops["direct"].shape[0]],
                          ops["direct"].noise_from_standard(z[:1]))
