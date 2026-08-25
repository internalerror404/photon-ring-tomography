"""Age-error scoring via precomputed quadratic forms.

Scoring a reconstruction means evaluating ``||W_a (xhat - x)||`` for every age
window, every truth and every hyperparameter. Materialising the reconstructed
movie on the evaluation grid for each of those is what makes the naive loop
intractable, and it is unnecessary: the quantity is quadratic in the coefficient
vector, so

    ||W_a (D xhat - v)||^2 = xhat^T M_a xhat - 2 xhat^T p_a(v) + s_a(v)

with ``M_a = D^T diag(W_a^2) D`` precomputed once per age, and ``p_a`` and
``s_a`` precomputed once per truth. Nothing is approximated; the algebra is
exact and the cost moves from the evaluation dimension to the class dimension.

The evaluation grid is a declared structured grid over the source domain, not
the ray coordinates of any one arm. Scoring on the resolved arm's own sampling
points would give that arm a home-field advantage in exactly the comparison the
pilot exists to make.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AgeScorer:
    design: np.ndarray          # (n_eval, d) class design on the evaluation grid
    ages: np.ndarray            # (n_ages,)
    M: np.ndarray               # (n_ages, d, d)
    weights: np.ndarray         # (n_ages, n_eval), normalised age windows
    g: np.ndarray               # (n_ages, d), D^T W_a^2 1
    h: np.ndarray               # (n_ages,), <W_a^2 1, 1>

    @classmethod
    def build(cls, design: np.ndarray, source_times: np.ndarray,
              ages: np.ndarray, half_width: float) -> "AgeScorer":
        W = np.exp(-0.5 * ((source_times[None, :] + ages[:, None])
                           / half_width) ** 2)
        W = W / np.maximum(np.linalg.norm(W, axis=1, keepdims=True), 1e-300)
        # Written as one BLAS matmul per age rather than a single einsum: the
        # einsum contraction path materialises an (n_ages, n_eval, d) tensor and
        # spends most of its time in reshape. Same flops, ~20x faster.
        d = design.shape[1]
        M = np.empty((ages.size, d, d))
        W2 = W ** 2
        for a in range(ages.size):
            M[a] = (design * W2[a, :, None]).T @ design
        g = W2 @ design
        h = W2.sum(axis=1)
        return cls(design=design, ages=ages, M=M, weights=W, g=g, h=h)

    def truth_terms(self, values: np.ndarray):
        """p_a and s_a for a stack of rendered truths, one per row."""
        W2 = self.weights ** 2
        n, a, d = values.shape[0], self.ages.size, self.design.shape[1]
        p = np.empty((n, a, d))
        for k in range(a):
            p[:, k, :] = (values * W2[k][None, :]) @ self.design
        s = (values ** 2) @ W2.T
        m = values @ W2.T                      # <W_a^2 v, 1> per truth and age
        return p, s, m

    def errors(self, coefficients: np.ndarray, p: np.ndarray,
               s: np.ndarray) -> np.ndarray:
        """||W_a (D xhat - v)|| for every truth and age, exactly."""
        X = np.atleast_2d(coefficients)
        quad = np.empty((X.shape[0], self.ages.size))
        for k in range(self.ages.size):
            quad[:, k] = np.sum((X @ self.M[k]) * X, axis=1)
        cross = np.sum(p * X[:, None, :], axis=2)
        return np.sqrt(np.maximum(quad - 2.0 * cross + s, 0.0))

    def structure_errors(self, coefficients: np.ndarray, p: np.ndarray,
                         s: np.ndarray, m: np.ndarray):
        """The same error with the age-local constant component removed.

        Every physical movie here sits on a positive baseline, and a constant is
        exactly representable in the class, so the registered normalised error
        divides by a denominator dominated by a DC component that every
        estimator recovers trivially. That makes the registered error small and
        the stable-depth statistic saturate regardless of how badly the
        *structure* is reconstructed.

        Removing the W_a-weighted projection onto the constant from both the
        residual and the truth measures what is actually in dispute. This is a
        diagnostic companion: the registered metric is still computed and
        reported unchanged.
        """
        X = np.atleast_2d(coefficients)
        quad = np.empty((X.shape[0], self.ages.size))
        for k in range(self.ages.size):
            quad[:, k] = np.sum((X @ self.M[k]) * X, axis=1)
        cross = np.sum(p * X[:, None, :], axis=2)
        full = quad - 2.0 * cross + s
        # <W_a^2 (D x - v), 1> = g_a . x - m_a
        proj = (X @ self.g.T) - m
        res_struct = np.maximum(full - proj ** 2 / np.maximum(self.h, 1e-300), 0.0)
        truth_struct = np.maximum(s - m ** 2 / np.maximum(self.h, 1e-300), 0.0)
        return np.sqrt(res_struct), np.sqrt(truth_struct)


def evaluation_grid(r_in: float, r_out: float, t_lo: float, t_hi: float,
                    n_r: int = 10, n_phi: int = 12, n_t: int = 40):
    """A declared structured grid over the source domain.

    Log-spaced in radius because the class's radial knots are, uniform in
    azimuth and in source time. Equal weights: the grid is a scoring device, not
    a quadrature of the physical emission, and pretending otherwise would import
    a weighting nobody declared.
    """
    r = np.exp(np.linspace(np.log(r_in), np.log(r_out), n_r))
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    t = np.linspace(t_lo, t_hi, n_t)
    R, P, T = np.meshgrid(r, phi, t, indexing="ij")
    return R.ravel(), P.ravel(), T.ravel()
