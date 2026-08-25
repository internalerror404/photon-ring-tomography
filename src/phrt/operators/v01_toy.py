"""Independent matrix-free reimplementation of the v0.1 toy operator (gate G1).

What "independent" means here
-----------------------------
The *specification* is not free: which projection matrices and which prior
basis the v0.1 experiment uses are fixed by seed 42 and by the registered
constants, so reconstructing them is reproduction, not invention.  What is
independent is the *implementation*: this module never forms the dense array
the way the original does.  It applies the operator matrix-free through a
hand-written ``matvec``/``rmatvec`` pair, and every rank and singular value is
computed through this repository's own conventions in ``phrt.audits.rank``.

That is the property G1 exists to test.  If the original's dense row-assembly
loop and this factored operator disagree, one of them is wrong.

Layout
------
The v0.1 source vector is **time-major**: ``x[ts * K + k]`` for source-time
index ``ts`` and spatial mode ``k``.  Index 0 is the *oldest* sample and index
``H - 1`` the newest, because order ``n`` reads the window beginning at
``max_delay - n*D``: the direct channel sees the newest ``W`` samples and
deeper orders reach further back.

Note this is the opposite orientation from ``phrt.operators.structured``, which
indexes by retarded age (0 = most recent).  Both are internally consistent and
give identical spectra; the two conventions are kept distinct on purpose rather
than silently reconciled, and ``retarded_age_of_index`` converts between them.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse.linalg import LinearOperator

# Registered v0.1 constants, pinned by the reviewer ruling and by the source.
W = 24          # observer time samples
D = 4           # delay per image order, in samples
NMAX = 5        # deepest image order
H = W + NMAX * D    # 44 source-history samples
K = 6           # spatial source modes
M = 2           # measurements per observer time and image order
GAMMA = 0.6
RT, RS = 8, 3   # prior subspace: RT temporal x RS spatial = 24
SEED = 42

MAX_DELAY = NMAX * D
ATTENUATION = np.exp(-GAMMA * np.arange(NMAX + 1))


def retarded_age_of_index(ts: int) -> int:
    """Convert a v0.1 source-time index to a retarded age (0 = most recent)."""
    return H - 1 - int(ts)


@dataclass(frozen=True)
class V01Spec:
    """The seed-determined ingredients of the v0.1 experiment.

    The draw order matters and is part of the specification: one draw for the
    shared projection, then NMAX+1 draws for the diverse projections, then one
    draw for the prior's spatial factor.  Consuming the stream in any other
    order yields a different -- and wrong -- experiment.
    """

    identical: list[np.ndarray]
    diverse: list[np.ndarray]
    prior_basis: np.ndarray

    @classmethod
    def build(cls, seed: int = SEED) -> "V01Spec":
        rng = np.random.default_rng(seed)
        Q, _ = np.linalg.qr(rng.normal(size=(K, K)))
        P0 = Q[:, :M].T
        identical = [P0.copy() for _ in range(NMAX + 1)]
        diverse = []
        for _ in range(NMAX + 1):
            q, _ = np.linalg.qr(rng.normal(size=(K, K)))
            diverse.append(q[:, :M].T)

        t = np.arange(H)
        Bt = np.column_stack([np.cos(np.pi * (t + 0.5) * k / H) for k in range(RT)])
        Bt, _ = np.linalg.qr(Bt)
        Qs, _ = np.linalg.qr(rng.normal(size=(K, K)))
        Bs = Qs[:, :RS]
        return cls(identical, diverse, np.kron(Bt, Bs))

    def projections(self, name: str) -> list[np.ndarray]:
        if name == "identical":
            return self.identical
        if name == "diverse":
            return self.diverse
        raise ValueError(f"unknown spatial channel set {name!r}")


class V01Operator(LinearOperator):
    """Matrix-free v0.1 forward operator.

    ``resolved`` keeps one output block per (order, observer time); the
    unresolved readout sums the orders into a single block per observer time.
    """

    def __init__(self, max_order: int, projections: list[np.ndarray], resolved: bool):
        if not 0 <= max_order <= NMAX:
            raise ValueError(f"max_order {max_order} outside 0..{NMAX}")
        self.max_order = int(max_order)
        self.projections = [np.asarray(p, dtype=np.float64) for p in projections]
        self.resolved = bool(resolved)
        for p in self.projections[: self.max_order + 1]:
            if p.shape != (M, K):
                raise ValueError(f"projection must be {(M, K)}, got {p.shape}")
        n_rows = ((self.max_order + 1) * W * M) if resolved else (W * M)
        super().__init__(dtype=np.float64, shape=(n_rows, H * K))

    def _source_index(self, n: int, t: int) -> int:
        return MAX_DELAY - n * D + t

    def _matvec(self, x: np.ndarray) -> np.ndarray:
        X = np.asarray(x, dtype=np.float64).reshape(H, K)
        if self.resolved:
            out = np.empty((self.max_order + 1, W, M))
            for n in range(self.max_order + 1):
                lo = MAX_DELAY - n * D
                # one gemm per order rather than a Python loop over observer times
                out[n] = ATTENUATION[n] * (X[lo:lo + W] @ self.projections[n].T)
            return out.reshape(-1)
        acc = np.zeros((W, M))
        for n in range(self.max_order + 1):
            lo = MAX_DELAY - n * D
            acc += ATTENUATION[n] * (X[lo:lo + W] @ self.projections[n].T)
        return acc.reshape(-1)

    def _rmatvec(self, y: np.ndarray) -> np.ndarray:
        out = np.zeros((H, K))
        if self.resolved:
            Y = np.asarray(y, dtype=np.float64).reshape(self.max_order + 1, W, M)
            for n in range(self.max_order + 1):
                lo = MAX_DELAY - n * D
                out[lo:lo + W] += ATTENUATION[n] * (Y[n] @ self.projections[n])
            return out.reshape(-1)
        Y = np.asarray(y, dtype=np.float64).reshape(W, M)
        for n in range(self.max_order + 1):
            lo = MAX_DELAY - n * D
            out[lo:lo + W] += ATTENUATION[n] * (Y @ self.projections[n])
        return out.reshape(-1)

    def to_dense(self) -> np.ndarray:
        return np.column_stack([self._matvec(e) for e in np.eye(self.shape[1])])


def reference_dense(max_order: int, projections: list[np.ndarray],
                    resolved: bool) -> np.ndarray:
    """Dense assembly in the original's own row-major style.

    Kept as the G2 comparison target: it is written the way the v0.1 source
    writes it, so agreement with ``V01Operator`` is a genuine parity check
    between two different ways of expressing the same operator.
    """
    if resolved:
        A = np.zeros(((max_order + 1) * W * M, H * K))
        row = 0
        for n in range(max_order + 1):
            for t in range(W):
                ts = MAX_DELAY - n * D + t
                A[row:row + M, ts * K:(ts + 1) * K] = ATTENUATION[n] * projections[n]
                row += M
        return A
    A = np.zeros((W * M, H * K))
    for n in range(max_order + 1):
        for t in range(W):
            ts = MAX_DELAY - n * D + t
            A[t * M:(t + 1) * M, ts * K:(ts + 1) * K] += ATTENUATION[n] * projections[n]
    return A
