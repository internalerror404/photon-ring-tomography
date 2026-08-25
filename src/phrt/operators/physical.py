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

Measurement models
------------------
``specific_intensity``  c = g^3.  Pixel area belongs to the likelihood, not the
                        forward row. This is the primary Paper I oracle.
``photon_count``        c = dOmega * g^3, with the area in the row.
``total_flux``          each order is collapsed to one number per observer time
                        by summing dOmega * g^3 over its rays. The deliberately
                        information-poor control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Sequence

import numpy as np
from scipy.sparse.linalg import LinearOperator

MeasurementModel = Literal["specific_intensity", "photon_count", "total_flux"]
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

    def coefficient(self, model: MeasurementModel) -> np.ndarray:
        g3 = np.power(np.abs(self.redshift), 3.0)
        if model == "specific_intensity":
            c = g3
        elif model in ("photon_count", "total_flux"):
            c = self.quadrature * g3
        else:
            raise ValueError(f"unknown measurement model {model!r}")
        return self.amplitude * c


@dataclass
class PhysicalOperator(LinearOperator):
    """Matrix-free forward map from source coefficients to observations.

    Row layout is (order, observer time, ray), order-major. The unresolved arm
    is expressed by a channel mixer over orders, exactly as in the toy, so the
    same collapse identity is testable here.
    """

    orders: Sequence[OrderRays]
    observer_times: np.ndarray
    design: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]
    dimension: int
    model: MeasurementModel = "specific_intensity"
    mixer: np.ndarray | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.orders = list(self.orders)
        self.observer_times = np.asarray(self.observer_times, dtype=float)
        n_orders = len(self.orders)
        self.L = np.eye(n_orders) if self.mixer is None else np.asarray(self.mixer, float)
        if self.L.shape[1] != n_orders:
            raise ValueError("mixer column count must equal the number of orders")
        self.n_channels = int(self.L.shape[0])
        if self.model == "total_flux":
            self._rows_per_order = [1] * n_orders
        else:
            self._rows_per_order = [o.n_rays for o in self.orders]
        if len(set(self._rows_per_order)) != 1 and self.n_channels != n_orders:
            raise ValueError(
                "mixing orders together requires them to share a row layout; "
                "orders have different ray counts, so mix only after collapsing "
                "or subsample to a common count")
        self._rows_per_channel = self._rows_per_order[0] * self.observer_times.size
        super().__init__(dtype=np.float64,
                         shape=(self.n_channels * self._rows_per_channel, self.dimension))

    # -- per-order block ----------------------------------------------------
    def _order_design(self, o: OrderRays, t_obs: float) -> np.ndarray:
        t_source = t_obs - o.delay
        D = self.design(o.source_r, o.source_phi, t_source)
        return D * o.coefficient(self.model)[:, None]

    def order_block(self, index: int) -> np.ndarray:
        """Dense (rows, dimension) block for one order, all observer times."""
        o = self.orders[index]
        blocks = []
        for t in self.observer_times:
            D = self._order_design(o, float(t))
            if self.model == "total_flux":
                D = D.sum(axis=0, keepdims=True)
            blocks.append(D)
        return np.vstack(blocks)

    def to_dense(self) -> np.ndarray:
        per_order = [self.order_block(i) for i in range(len(self.orders))]
        rows = [sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
                for c in range(self.n_channels)]
        return np.vstack(rows)

    def _matvec(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float).ravel()
        per_order = []
        for i, o in enumerate(self.orders):
            acc = []
            for t in self.observer_times:
                D = self._order_design(o, float(t))
                v = D @ x
                acc.append(np.array([v.sum()]) if self.model == "total_flux" else v)
            per_order.append(np.concatenate(acc))
        out = [sum(self.L[c, n] * per_order[n] for n in range(len(self.orders)))
               for c in range(self.n_channels)]
        return np.concatenate(out)

    def _rmatvec(self, y: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=float).ravel()
        chan = y.reshape(self.n_channels, -1)
        out = np.zeros(self.dimension)
        for i, o in enumerate(self.orders):
            w = np.zeros(self._rows_per_channel)
            for c in range(self.n_channels):
                if self.L[c, i] != 0.0:
                    w = w + self.L[c, i] * chan[c]
            per_t = w.reshape(self.observer_times.size, -1)
            for k, t in enumerate(self.observer_times):
                D = self._order_design(o, float(t))
                if self.model == "total_flux":
                    out += float(per_t[k, 0]) * D.sum(axis=0)
                else:
                    out += D.T @ per_t[k]
        return out

    def gram(self, sigma: np.ndarray | float = 1.0) -> np.ndarray:
        """Streamed G = A^T C^{-1} A, symmetrised.

        Never materialises A. With d = 224 this is both cheaper and better
        conditioned than storing every row, and the right singular vectors are
        recoverable from eigh(G).
        """
        A = self.to_dense()
        s = np.broadcast_to(np.asarray(sigma, dtype=float), (A.shape[0],))
        B = A / s[:, None]
        G = B.T @ B
        return 0.5 * (G + G.T)


# ---------------------------------------------------------------------------
# arm construction
# ---------------------------------------------------------------------------
def equalize(orders: Sequence[OrderRays], model: MeasurementModel) -> list[OrderRays]:
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
        scale = float(np.linalg.norm(o.coefficient(model)))
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
