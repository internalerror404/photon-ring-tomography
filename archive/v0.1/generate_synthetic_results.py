from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
RES = ROOT / 'results'
FIG.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# -----------------------------------------------------------------------------
# Paper I: discrete retarded-time operator
# -----------------------------------------------------------------------------
W = 24                    # observer time samples
D = 4                     # delay per image order (samples)
NMAX = 5
H = W + NMAX * D          # total source-history samples
K = 6                     # spatial source modes
M = 2                     # measurements per observer time and image order
GAMMA = 0.6
ATT = np.exp(-GAMMA * np.arange(NMAX + 1))

Q, _ = np.linalg.qr(rng.normal(size=(K, K)))
P0 = Q[:, :M].T
P_IDENT = [P0.copy() for _ in range(NMAX + 1)]
P_DIVERSE = []
for _ in range(NMAX + 1):
    q, _ = np.linalg.qr(rng.normal(size=(K, K)))
    P_DIVERSE.append(q[:, :M].T)


def build_operator(N: int, projections: list[np.ndarray], resolved: bool) -> np.ndarray:
    """Build a finite-window delay-and-projection operator.

    The direct channel samples the newest W source times. Order n samples a window
    shifted nD samples into the past. Each order is attenuated by exp(-gamma n).
    """
    max_delay = NMAX * D
    if resolved:
        A = np.zeros(((N + 1) * W * M, H * K))
        row = 0
        for n in range(N + 1):
            for t in range(W):
                ts = max_delay - n * D + t
                A[row:row + M, ts * K:(ts + 1) * K] = ATT[n] * projections[n]
                row += M
        return A

    A = np.zeros((W * M, H * K))
    for n in range(N + 1):
        for t in range(W):
            ts = max_delay - n * D + t
            A[t * M:(t + 1) * M, ts * K:(ts + 1) * K] += ATT[n] * projections[n]
    return A


# Smooth low-dimensional source model used only as a controlled prior subspace.
RT, RS = 8, 3
t = np.arange(H)
Bt = np.column_stack([np.cos(np.pi * (t + 0.5) * k / H) for k in range(RT)])
Bt, _ = np.linalg.qr(Bt)
Qs, _ = np.linalg.qr(rng.normal(size=(K, K)))
Bs = Qs[:, :RS]
B = np.kron(Bt, Bs)       # (H K) x (RT RS)

records = []
for spatial_name, projections in [('identical', P_IDENT), ('diverse', P_DIVERSE)]:
    for resolved in (True, False):
        for N in range(NMAX + 1):
            A = build_operator(N, projections, resolved)
            singular = np.linalg.svd(A, compute_uv=False)
            tol = max(A.shape) * np.finfo(float).eps * singular[0]
            rank = int(np.sum(singular > tol))
            smallest_nonzero = float(singular[rank - 1]) if rank else 0.0

            AB = A @ B
            sb = np.linalg.svd(AB, compute_uv=False)
            rank_b = int(np.linalg.matrix_rank(AB))
            smallest_restricted = float(sb[-1]) if rank_b == B.shape[1] else 0.0
            records.append({
                'spatial_channels': spatial_name,
                'readout': 'resolved' if resolved else 'unresolved',
                'max_order': N,
                'rank': rank,
                'smallest_nonzero_singular_value': smallest_nonzero,
                'prior_subspace_rank': rank_b,
                'prior_subspace_smallest_singular_value': smallest_restricted,
            })

ident_df = pd.DataFrame(records)
ident_df.to_csv(RES / 'paper1_identifiability.csv', index=False)

# Figure: rank versus maximum order.
plt.figure(figsize=(7.2, 4.6))
for spatial, readout, marker, label in [
    ('identical', 'resolved', 'o', 'Resolved, identical spatial channel'),
    ('diverse', 'resolved', 's', 'Resolved, diverse spatial channels'),
    ('diverse', 'unresolved', '^', 'Unresolved sum, diverse channels'),
]:
    d = ident_df[(ident_df.spatial_channels == spatial) & (ident_df.readout == readout)]
    plt.plot(d.max_order, d['rank'], marker=marker, label=label)
plt.xlabel('Highest included image order N')
plt.ylabel('Rank of the finite-dimensional forward operator')
plt.title('Order resolution and channel diversity control identifiability')
plt.grid(alpha=0.25)
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG / 'paper1_rank_vs_order.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper1_rank_vs_order.png', dpi=240, bbox_inches='tight')
plt.close()

# Figure: restricted lower frame bound on a smooth source model.
# Only the resolved-diverse arm is injective on the chosen 24D subspace.
plt.figure(figsize=(7.2, 4.6))
d = ident_df[(ident_df.spatial_channels == 'diverse') & (ident_df.readout == 'resolved')].copy()
vals = d.prior_subspace_smallest_singular_value.to_numpy()
vals[vals <= 0] = np.nan
plt.semilogy(d.max_order, vals, marker='s', label='Resolved, diverse spatial channels')
plt.xlabel('Highest included image order N')
plt.ylabel('Restricted smallest singular value')
plt.title('Channel diversity stabilizes the 24D smooth source model')
plt.grid(alpha=0.25, which='both')
plt.legend(frameon=False, loc='upper left')
plt.text(0.03, 0.06,
         'Resolved-identical and unresolved-diverse arms remain\n'
         'rank deficient on this subspace for every tested N.',
         transform=plt.gca().transAxes, ha='left', va='bottom', fontsize=9,
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='0.5', alpha=0.9))
plt.tight_layout()
plt.savefig(FIG / 'paper1_restricted_stability.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper1_restricted_stability.png', dpi=240, bbox_inches='tight')
plt.close()


def oracle_ridge_errors(A: np.ndarray, prior_basis: np.ndarray, relative_noise: np.ndarray,
                        samples: int = 200, seed: int = 123) -> pd.DataFrame:
    local_rng = np.random.default_rng(seed)
    latent = local_rng.normal(size=(prior_basis.shape[1], samples))
    truth = prior_basis @ latent
    clean = A @ truth
    y_scale = float(np.sqrt(np.mean(clean ** 2)))
    truth_norm = np.linalg.norm(truth, axis=0)

    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    AB = A @ prior_basis
    Ub, sb, Vtb = np.linalg.svd(AB, full_matrices=False)
    lambdas = np.logspace(-12, 1, 40)

    rows = []
    for rel in relative_noise:
        noisy = clean + local_rng.normal(scale=rel * y_scale, size=clean.shape)
        best_full = (np.inf, None)
        for lam in lambdas:
            estimate = (Vt.T * (s / (s * s + lam))) @ (U.T @ noisy)
            error = float(np.mean(np.linalg.norm(estimate - truth, axis=0) / truth_norm))
            if error < best_full[0]:
                best_full = (error, float(lam))

        best_prior = (np.inf, None)
        for lam in lambdas:
            zhat = (Vtb.T * (sb / (sb * sb + lam))) @ (Ub.T @ noisy)
            estimate = prior_basis @ zhat
            error = float(np.mean(np.linalg.norm(estimate - truth, axis=0) / truth_norm))
            if error < best_prior[0]:
                best_prior = (error, float(lam))

        rows.append({
            'relative_noise': float(rel),
            'full_space_oracle_tikhonov_error': best_full[0],
            'full_space_lambda': best_full[1],
            'prior_subspace_oracle_ridge_error': best_prior[0],
            'prior_subspace_lambda': best_prior[1],
        })
    return pd.DataFrame(rows)

noise_levels = np.array([0.0, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1])
resolved_errors = oracle_ridge_errors(build_operator(NMAX, P_DIVERSE, True), B, noise_levels)
unresolved_errors = oracle_ridge_errors(build_operator(NMAX, P_DIVERSE, False), B, noise_levels)
resolved_errors['readout'] = 'resolved'
unresolved_errors['readout'] = 'unresolved'
recon_df = pd.concat([resolved_errors, unresolved_errors], ignore_index=True)
recon_df.to_csv(RES / 'paper1_reconstruction.csv', index=False)

plt.figure(figsize=(7.2, 4.6))
# Skip exactly zero on logarithmic x-axis; display it separately in the table.
r = resolved_errors[resolved_errors.relative_noise > 0]
u = unresolved_errors[unresolved_errors.relative_noise > 0]
plt.loglog(r.relative_noise, r.full_space_oracle_tikhonov_error, marker='o',
           label='Resolved data, full-space Tikhonov')
plt.loglog(r.relative_noise, r.prior_subspace_oracle_ridge_error, marker='s',
           label='Resolved data, restricted source prior')
plt.loglog(u.relative_noise, u.prior_subspace_oracle_ridge_error, marker='^',
           label='Unresolved data, same restricted prior')
plt.xlabel('Noise standard deviation / clean-data RMS')
plt.ylabel('Mean relative reconstruction error')
plt.title('A learned/restricted prior helps only after the forward map is injective on it')
plt.grid(alpha=0.25, which='both')
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG / 'paper1_reconstruction_error.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper1_reconstruction_error.png', dpi=240, bbox_inches='tight')
plt.close()

# Operator schematic: the same source history can be observed as an order-resolved
# stack or collapsed into a cancellation-prone mixture.
fig, ax = plt.subplots(figsize=(9.4, 4.8))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Top panel: order-resolved readout.
ax.text(0.02, 0.94, 'A. Order-resolved observation', ha='left', va='center',
        fontsize=11, fontweight='bold')
ax.text(0.10, 0.72, 'Source history\n$j(x,t)$', ha='center', va='center', fontsize=11,
        bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='black'))
order_y = [0.84, 0.76, 0.68, 0.60]
for n, y in enumerate(order_y):
    ax.annotate('', xy=(0.34, y), xytext=(0.18, 0.72),
                arrowprops=dict(arrowstyle='->', lw=1.05))
    ax.text(0.43, y, rf'$\mathcal{{T}}_{n}j$' + '\n' + rf'$\Delta_{n},\ a_{n}$',
            ha='center', va='center', fontsize=9.6,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='black'))
    ax.annotate('', xy=(0.76, 0.72), xytext=(0.52, y),
                arrowprops=dict(arrowstyle='->', lw=1.0))
ax.text(0.87, 0.72,
        'Retain order labels\n' + r'$\mathcal{A}^{(N)}j=(\mathcal{T}_0j,\ldots,\mathcal{T}_Nj)$',
        ha='center', va='center', fontsize=9.8,
        bbox=dict(boxstyle='round,pad=0.32', facecolor='white', edgecolor='black'))

# Bottom panel: unresolved readout.
ax.text(0.02, 0.43, 'B. Unresolved observation', ha='left', va='center',
        fontsize=11, fontweight='bold')
ax.text(0.10, 0.22, 'Source history\n$j(x,t)$', ha='center', va='center', fontsize=11,
        bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='black'))
ax.annotate('', xy=(0.34, 0.22), xytext=(0.18, 0.22),
            arrowprops=dict(arrowstyle='->', lw=1.2))
ax.text(0.48, 0.31, 'Collapse image orders',
        ha='center', va='center', fontsize=9.8)
ax.text(0.48, 0.22, r'$\sum_{n=0}^{N}M_n\mathcal{T}_n j$',
        ha='center', va='center', fontsize=11,
        bbox=dict(boxstyle='round,pad=0.34', facecolor='white', edgecolor='black'))
ax.annotate('', xy=(0.76, 0.22), xytext=(0.62, 0.22),
            arrowprops=dict(arrowstyle='->', lw=1.2))
ax.text(0.87, 0.22, 'Unresolved mixture\n' + r'$\mathcal{U}^{(N)}j$',
        ha='center', va='center', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.34', facecolor='white', edgecolor='black'))

ax.text(0.5, 0.025,
        'Order resolution converts one mixed observation into a stack of independently weighted constraints.',
        ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.savefig(FIG / 'paper1_operator_schematic.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper1_operator_schematic.png', dpi=240, bbox_inches='tight')
plt.close()

# -----------------------------------------------------------------------------
# Paper II: temporal-depth law
# -----------------------------------------------------------------------------
SNR_GRID = np.logspace(1, 7, 240)
THRESHOLD = 5.0
GAMMAS = [0.4, 0.7, 1.0]
TAU = 1.0

rows = []
for gamma in GAMMAS:
    nmax = np.maximum(-1, np.floor(np.log(SNR_GRID / THRESHOLD) / gamma)).astype(int)
    depth = np.maximum(0, nmax) * TAU
    for snr, n, dep in zip(SNR_GRID, nmax, depth):
        rows.append({'snr0': float(snr), 'gamma': gamma, 'tau': TAU,
                     'threshold': THRESHOLD, 'n_max': int(n), 'temporal_depth': float(dep)})
depth_df = pd.DataFrame(rows)
depth_df.to_csv(RES / 'paper2_depth_law.csv', index=False)

plt.figure(figsize=(7.2, 4.6))
for gamma in GAMMAS:
    d = depth_df[depth_df.gamma == gamma]
    plt.semilogx(d.snr0, d.temporal_depth, label=rf'$\Gamma={gamma}$')
plt.xlabel('Leading-order effective SNR')
plt.ylabel(r'Recoverable depth in units of $\tau$')
plt.title(r'Ideal order-separated depth grows as $(\tau/\Gamma)\log(\mathrm{SNR})$')
plt.grid(alpha=0.25, which='both')
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG / 'paper2_depth_vs_snr.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper2_depth_vs_snr.png', dpi=240, bbox_inches='tight')
plt.close()

# Heat map of n_max over SNR and gamma.
gamma_grid = np.linspace(0.25, 1.25, 160)
logsnr_grid = np.linspace(1, 7, 220)
G, L = np.meshgrid(gamma_grid, logsnr_grid)
N = np.floor((np.log(10.0) * L - np.log(THRESHOLD)) / G)
N = np.maximum(0, N)
plt.figure(figsize=(7.2, 4.8))
im = plt.imshow(N, origin='lower', aspect='auto',
                extent=[gamma_grid.min(), gamma_grid.max(), logsnr_grid.min(), logsnr_grid.max()])
plt.xlabel(r'Effective attenuation exponent $\Gamma$ per order')
plt.ylabel(r'$\log_{10}(\mathrm{SNR}_0)$')
plt.title('Maximum detectable image order in the ideal threshold model')
cb = plt.colorbar(im)
cb.set_label(r'$N_{\mathrm{SNR}}$')
plt.tight_layout()
plt.savefig(FIG / 'paper2_order_heatmap.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper2_order_heatmap.png', dpi=240, bbox_inches='tight')
plt.close()

# Monte Carlo validation of order-wise RMSE.
MC_GAMMA = 0.7
MC_SNR0 = 1e4
MC_ORDERS = np.arange(0, 18)
MC_TRIALS = 200_000
sigma = 1.0 / MC_SNR0
mc_rows = []
for n in MC_ORDERS:
    a_n = np.exp(-MC_GAMMA * n)
    noise = rng.normal(scale=sigma, size=MC_TRIALS)
    estimate = 1.0 + noise / a_n
    empirical_rmse = float(np.sqrt(np.mean((estimate - 1.0) ** 2)))
    theoretical_rmse = float(np.exp(MC_GAMMA * n) / MC_SNR0)
    mc_rows.append({'order': int(n), 'empirical_rmse': empirical_rmse,
                    'theoretical_rmse': theoretical_rmse,
                    'effective_snr': float(MC_SNR0 * np.exp(-MC_GAMMA * n))})
mc_df = pd.DataFrame(mc_rows)
mc_df.to_csv(RES / 'paper2_monte_carlo_rmse.csv', index=False)

plt.figure(figsize=(7.2, 4.6))
plt.semilogy(mc_df['order'], mc_df.empirical_rmse, marker='o', label='Monte Carlo RMSE')
plt.semilogy(mc_df['order'], mc_df.theoretical_rmse, linestyle='--', label=r'$e^{\Gamma n}/\mathrm{SNR}_0$')
plt.axhline(1.0 / THRESHOLD, linestyle=':', label='20% error threshold')
plt.xlabel('Image order n')
plt.ylabel('Relative RMSE of an order-specific historical coefficient')
plt.title(r'Noise amplification is exponential in image order ($\Gamma=0.7$)')
plt.grid(alpha=0.25, which='both')
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG / 'paper2_monte_carlo_rmse.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper2_monte_carlo_rmse.png', dpi=240, bbox_inches='tight')
plt.close()

# Combined bottleneck map (explicitly illustrative, not an astrophysical forecast).
B_RATIO = 1e4                   # maximum baseline / leading subring baseline scale
N_GEOMETRY = 18                # cumulative delay-calibration ceiling
N_WINDOW = 15                  # source/observation-window ceiling
N_RES = np.floor(np.log(B_RATIO) / G).astype(int)
N_SNR = np.maximum(0, np.floor((np.log(10.0) * L - np.log(THRESHOLD)) / G)).astype(int)
NSTAR = np.minimum.reduce([N_SNR, N_RES, np.full_like(N_SNR, N_GEOMETRY), np.full_like(N_SNR, N_WINDOW)])
# 0=SNR, 1=resolution, 2=geometry, 3=window. Ties broken by this ordering.
stack = np.stack([N_SNR, N_RES, np.full_like(N_SNR, N_GEOMETRY), np.full_like(N_SNR, N_WINDOW)], axis=0)
bottleneck = np.argmin(stack, axis=0)
plt.figure(figsize=(7.2, 4.8))
im = plt.imshow(bottleneck, origin='lower', aspect='auto', interpolation='nearest',
                extent=[gamma_grid.min(), gamma_grid.max(), logsnr_grid.min(), logsnr_grid.max()],
                vmin=-0.5, vmax=3.5)
plt.xlabel(r'Effective attenuation exponent $\Gamma$ per order')
plt.ylabel(r'$\log_{10}(\mathrm{SNR}_0)$')
plt.title('Illustrative dominant limit on temporal depth')
cb = plt.colorbar(im, ticks=[0, 1, 2, 3])
cb.ax.set_yticklabels(['SNR', 'angular resolution', 'delay calibration', 'finite window'])
plt.tight_layout()
plt.savefig(FIG / 'paper2_bottleneck_map.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper2_bottleneck_map.png', dpi=240, bbox_inches='tight')
plt.close()

# Gaussian-prior illustration: posterior variance and data-dominance ratio.
N_PRIOR = 24
orders = np.arange(N_PRIOR)
a_diag = np.exp(-MC_GAMMA * orders)
noise_var = (1.0 / MC_SNR0) ** 2
prior_rows = []
for rho in [0.0, 0.8, 0.98]:
    if rho == 0.0:
        Kprior = np.eye(N_PRIOR)
    else:
        Kprior = rho ** np.abs(np.subtract.outer(orders, orders))
    precision = np.linalg.inv(Kprior) + np.diag(a_diag ** 2 / noise_var)
    post = np.linalg.inv(precision)
    post_var = np.diag(post)
    data_fraction = 1.0 - post_var / np.diag(Kprior)
    for n in orders:
        prior_rows.append({'rho': rho, 'order': int(n), 'posterior_sd': float(np.sqrt(post_var[n])),
                           'data_fraction': float(data_fraction[n])})
prior_df = pd.DataFrame(prior_rows)
prior_df.to_csv(RES / 'paper2_prior_information.csv', index=False)

plt.figure(figsize=(7.2, 4.6))
for rho in [0.0, 0.8, 0.98]:
    d = prior_df[prior_df.rho == rho]
    plt.semilogy(d['order'], d.posterior_sd, marker='o', markersize=3, label=rf'AR(1) prior $\rho={rho}$')
plt.xlabel('Image order n')
plt.ylabel('Posterior standard deviation')
plt.title('A temporal prior can reduce error, but does not create data information')
plt.grid(alpha=0.25, which='both')
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(FIG / 'paper2_prior_posterior_sd.pdf', bbox_inches='tight')
plt.savefig(FIG / 'paper2_prior_posterior_sd.png', dpi=240, bbox_inches='tight')
plt.close()

# Summary JSON for reproducibility.
summary = {
    'paper1': {
        'seed': 42,
        'history_samples': H,
        'observer_samples': W,
        'delay_samples_per_order': D,
        'spatial_source_modes': K,
        'measurements_per_order_time': M,
        'max_order': NMAX,
        'attenuation_gamma': GAMMA,
        'prior_dimension': int(B.shape[1]),
    },
    'paper2': {
        'threshold_snr': THRESHOLD,
        'monte_carlo_gamma': MC_GAMMA,
        'monte_carlo_snr0': MC_SNR0,
        'monte_carlo_trials_per_order': MC_TRIALS,
        'illustrative_baseline_ratio': B_RATIO,
        'illustrative_geometry_order_ceiling': N_GEOMETRY,
        'illustrative_window_order_ceiling': N_WINDOW,
    }
}
(RES / 'synthetic_experiment_manifest.json').write_text(json.dumps(summary, indent=2))

print('Generated figures and result tables in', ROOT)
