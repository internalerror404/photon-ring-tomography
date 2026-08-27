"""The physical historical operator, built from per-ray Kerr transfer maps.

Why this is not the toy operator with different numbers
-------------------------------------------------------
The pilot measured overlapping retarded-time windows: n=0 spans ages 0-58 M,
n=1 spans 46-103 M, n=2 spans 62-120 M. An order therefore does **not**
correspond to one source age, and

    y_n(t_o) = a_n j(t_o - n tau)

is only an asymptotic summary. Each ray carries its own delay, so the operator
is built row by row from the per-ray landing coordinates:

    y_{n,p}(t_o) = c_{n,p} j(r_{n,p}, phi_{n,p}, t_o - Delta t_{n,p})

with the forward coefficient c fixed by the declared measurement model. The
distinction matters: a distributed delay kernel and a delay ladder have
different null spaces.

Measurement model
-----------------
One model, one noise scale, everything else derived by linear propagation.

The datum is the pixel-integrated flux

    z_p = dOmega_p * g_p^3 * j(r_p, phi_p, t_p) + eta_p,
    Var(eta_p) = sigma_Omega^2 * dOmega_p,

i.e. white noise of density ``sigma_Omega`` per unit solid angle. Whitening
gives the row that the audits actually consume:

    Atilde_p = sqrt(dOmega_p) / sigma_Omega * g_p^3 * B(r_p, phi_p, t_p).

**The square root is load-bearing.** An earlier revision used ``c = g^3`` with a
flat per-row sigma, which makes the information matrix scale with the number of
rows: splitting one pixel into k children carrying the same transfer value
multiplied G by k (measured: relative error 1.0, 3.0, 7.0 at k = 2, 4, 8). Under
that convention an adaptive grid manufactures Fisher information out of
pixelization, and since ray counts differ by orders of magnitude between
lensing bands, it silently reweighted the bands against each other. With
sqrt(dOmega) the same test returns 4e-16. Gate
``G10q_continuum_noise_quadrature_invariance`` locks it.

Derived arms are linear maps of the resolved data, never separate models with
their own sigma:

    unresolved image   y_U = L y_R,  C_U = L C_R L^T
    total flux         y_F = S y_R,  C_F = S C_R S^T

with C_R = sigma_Omega^2 diag(dOmega).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Sequence

import numpy as np
from scipy.sparse.linalg import LinearOperator

MeasurementModel = Literal["pixel_integrated"]
CHUNK = 4096


@dataclass
class OrderRays:
    """One order's rays, already subsampled with quadrature weights preserved."""

    order: int
    source_r: np.ndarray
    source_phi: np.ndarray
    delay: np.ndarray
    redshift: np.ndarray
    quadrature: np.ndarray          # dOmega per retained ray, rescaled
    amplitude: float = 1.0          # declared per-order scaling, for equalized arms

    @property
    def n_rays(self) -> int:
        return int(self.source_r.size)

    def coefficient(self, model: MeasurementModel = "pixel_integrated") -> np.ndarray:
        """Unwhitened pixel-integrated forward coefficient, dOmega * g^3."""
        return self.amplitude * self.quadrature * np.power(np.abs(self.redshift), 3.0)

    def row_variance(self, sigma_omega: float = 1.0) -> np.ndarray:
        """Var(eta_p) = sigma_Omega^2 * dOmega_p."""
        return sigma_omega ** 2 * self.quadrature

    def whitened_coefficient(self, sigma_omega: float = 1.0) -> np.ndarray:
        """sqrt(dOmega) * g^3 / sigma_Omega -- the row the audits consume."""
        return self.coefficient() / np.sqrt(self.row_variance(sigma_omega))


@dataclass
class PhysicalOperator(LinearOperator):
    """Whitened forward map from source coefficients to observations.

    Rows are already whitened under the single declared noise model, so the
    audits see C = I and no arm can quietly choose its own sigma. Every derived
    arm is a linear map of the resolved data with its covariance propagated:
    the unresolved image sums orders, the total-flux control sums pixels, and
    both carry the variance that summation implies.
    """

    orders: Sequence[OrderRays]
    observer_times: np.ndarray
    design: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]
    dimension: int
    sigma_omega: float = 1.0
    mixer: np.ndarray | None = None
    collapse: str | None = None          # None or "total_flux"
    model: MeasurementModel = "pixel_integrated"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.orders = list(self.orders)
        self.observer_times = np.asarray(self.observer_times, dtype=float)
        n_orders = len(self.orders)
        self.L = np.eye(n_orders) if self.mixer is None else np.asarray(self.mixer, float)
        if self.L.shape[1] != n_orders:
            raise ValueError("mixer column count must equal the number of orders")
        self.n_channels = int(self.L.shape[0])
        counts = {o.n_rays for o in self.orders}
        if self.n_channels != n_orders and len(counts) != 1:
            raise ValueError(
                "mixing orders together requires a common ray count so that the "
                "same screen pixel is being summed across orders")
        rows_per_channel = 1 if self.collapse == "total_flux" else self.orders[0].n_rays
        self._rows_per_channel = rows_per_channel * self.observer_times.size
        super().__init__(dtype=np.float64,
                         shape=(self.n_channels * self._rows_per_channel, self.dimension))

    # -- unwhitened building blocks ----------------------------------------
    def _order_rows(self, o: OrderRays, t_obs: float) -> np.ndarray:
        """Unwhitened pixel-integrated rows dOmega * g^3 * B for one order."""
        D = self.design(o.source_r, o.source_phi, float(t_obs) - o.delay)
        return D * o.coefficient()[:, None]

    def channel_variance(self) -> np.ndarray:
        """Per-row variance after the arm's linear map, one value per row."""
        s2 = self.sigma_omega ** 2
        if self.collapse == "total_flux":
            # summing every pixel of an order: Var = sigma^2 * sum(dOmega)
            per_order = np.array([s2 * float(o.quadrature.sum()) for o in self.orders])
        else:
            per_order = None
        out = []
        for c in range(self.n_channels):
            w = self.L[c] ** 2
            if self.collapse == "total_flux":
                v = float(np.dot(w, per_order))
                out.append(np.full(self.observer_times.size, v))
            else:
                v = s2 * sum(w[n] * self.orders[n].quadrature for n in range(len(self.orders)))
                out.append(np.tile(v, self.observer_times.size))
        return np.concatenate(out)

    def unwhitened_dense(self) -> np.ndarray:
        per_order = []
        for o in self.orders:
            blocks = []
            for t in self.observer_times:
                R = self._order_rows(o, float(t))
                blocks.append(R.sum(axis=0, keepdims=True)
                              if self.collapse == "total_flux" else R)
            per_order.append(np.vstack(blocks))
        return np.vstack([sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
                          for c in range(self.n_channels)])

    def to_dense(self) -> np.ndarray:
        """The whitened operator."""
        return self.unwhitened_dense() / np.sqrt(self.channel_variance())[:, None]

    def order_block(self, index: int) -> np.ndarray:
        """Unwhitened rows of one order, for the collapse identity."""
        o = self.orders[index]
        blocks = []
        for t in self.observer_times:
            R = self._order_rows(o, float(t))
            blocks.append(R.sum(axis=0, keepdims=True)
                          if self.collapse == "total_flux" else R)
        return np.vstack(blocks)

    def _matvec(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float).ravel()
        per_order = []
        for o in self.orders:
            acc = []
            for t in self.observer_times:
                v = self._order_rows(o, float(t)) @ x
                acc.append(np.array([v.sum()]) if self.collapse == "total_flux" else v)
            per_order.append(np.concatenate(acc))
        mixed = [sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
                 for c in range(self.n_channels)]
        return np.concatenate(mixed) / np.sqrt(self.channel_variance())

    def _rmatvec(self, y: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=float).ravel() / np.sqrt(self.channel_variance())
        chan = y.reshape(self.n_channels, -1)
        out = np.zeros(self.dimension)
        for i, o in enumerate(self.orders):
            w = np.zeros(self._rows_per_channel)
            for c in range(self.n_channels):
                if self.L[c, i] != 0.0:
                    w = w + self.L[c, i] * chan[c]
            per_t = w.reshape(self.observer_times.size, -1)
            for k, t in enumerate(self.observer_times):
                R = self._order_rows(o, float(t))
                if self.collapse == "total_flux":
                    out += float(per_t[k, 0]) * R.sum(axis=0)
                else:
                    out += R.T @ per_t[k]
        return out

    def forward_analytic(self, source_fn) -> np.ndarray:
        """Whitened data for an arbitrary source, not restricted to the class.

        ``matvec`` maps *coefficients* through the class design, so it can only
        produce data for sources the class can express. A validation truth that
        is only analytic -- which is the honest case, since a real history is
        not in anyone's basis -- has to enter the same way the physics does:
        sampled wherever the rays land and weighted by the same dOmega g^3.
        Using this rather than projecting the truth into the class first is what
        makes the representation floor a measurable quantity instead of zero by
        construction.
        """
        per_order = []
        for o in self.orders:
            acc = []
            for t in self.observer_times:
                j = np.asarray(source_fn(o.source_r, o.source_phi,
                                         float(t) - o.delay), dtype=float)
                v = o.coefficient() * j
                acc.append(np.array([v.sum()]) if self.collapse == "total_flux" else v)
            per_order.append(np.concatenate(acc))
        mixed = [sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
                 for c in range(self.n_channels)]
        return np.concatenate(mixed) / np.sqrt(self.channel_variance())

    def noise_from_standard(self, z: np.ndarray) -> np.ndarray:
        """Whitened arm noise from one standard normal draw shared by all arms.

        ``z`` has shape (n_orders, n_rays, n_times). The physical noise is
        ``sigma sqrt(dOmega) z`` on each order's pixels; every arm is a declared
        linear readout of that same physical draw, so the arms stay paired and
        their covariance is propagated exactly rather than resampled.
        """
        z = np.asarray(z, dtype=float)
        per_order = []
        for i, o in enumerate(self.orders):
            e = self.sigma_omega * np.sqrt(o.quadrature)[:, None] * z[i]
            cols = [e[:, k].sum(keepdims=True) if self.collapse == "total_flux"
                    else e[:, k] for k in range(self.observer_times.size)]
            per_order.append(np.concatenate(cols))
        mixed = [sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
                 for c in range(self.n_channels)]
        return np.concatenate(mixed) / np.sqrt(self.channel_variance())

    def gram(self) -> np.ndarray:
        A = self.to_dense()
        G = A.T @ A
        return 0.5 * (G + G.T)


# ---------------------------------------------------------------------------
# arm construction
# ---------------------------------------------------------------------------
def equalize(orders: Sequence[OrderRays], model: MeasurementModel = "pixel_integrated") -> list[OrderRays]:
    """Normalise each order's total sensitivity, leaving everything else alone.

    Only the declared per-order amplitude changes. Coordinates, delays, masks
    and quadrature weights are untouched, so the arm isolates attenuation from
    geometry rather than quietly altering the geometry too.
    """
    import copy

    out = [copy.replace(o) if hasattr(copy, "replace") else OrderRays(**vars(o))
           for o in orders]
    ref = None
    for o in out:
        scale = float(np.linalg.norm(o.whitened_coefficient()))
        ref = scale if ref is None else ref
        o.amplitude = o.amplitude * (ref / max(scale, 1e-300))
    return out


def substitute_spatial(orders: Sequence[OrderRays], donor: OrderRays) -> list[OrderRays]:
    """DELAY_ONLY: keep each order's physical delays, take the direct order's
    spatial map. Requires a common ray count."""
    out = []
    for o in orders:
        if o.n_rays != donor.n_rays:
            raise ValueError("delay-only substitution needs a common ray count")
        out.append(OrderRays(o.order, donor.source_r.copy(), donor.source_phi.copy(),
                             o.delay.copy(), o.redshift.copy(), o.quadrature.copy(),
                             o.amplitude))
    return out


def substitute_delay(orders: Sequence[OrderRays], donor: OrderRays) -> list[OrderRays]:
    """SPATIAL_ONLY: keep each order's physical spatial map, flatten every delay
    onto the direct order's delay field."""
    out = []
    for o in orders:
        if o.n_rays != donor.n_rays:
            raise ValueError("spatial-only substitution needs a common ray count")
        out.append(OrderRays(o.order, o.source_r.copy(), o.source_phi.copy(),
                             donor.delay.copy(), o.redshift.copy(),
                             o.quadrature.copy(), o.amplitude))
    return out


def destroy_pairing(orders: Sequence[OrderRays], seed: int) -> list[OrderRays]:
    """PAIRING_DESTROYED: permute delay, position and weight independently within
    each order, preserving all three marginals and destroying their pairing."""
    out = []
    for k, o in enumerate(orders):
        rng = np.random.default_rng([seed, o.order])
        p1, p2, p3 = (rng.permutation(o.n_rays) for _ in range(3))
        out.append(OrderRays(o.order, o.source_r[p1], o.source_phi[p1],
                             o.delay[p2], o.redshift[p3], o.quadrature[p3],
                             o.amplitude))
    return out
