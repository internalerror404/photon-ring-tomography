#!/usr/bin/env python3
"""Source-time localization of saved L224 modes, not a new inverse experiment.

Uses exported source coefficients c, NOT Cholesky-normalized coordinates v.
For each interval I reports c.T H_I c / (c.T H c), retaining all cross terms.
The specialized L224 layout is validated. No ray maps, noise draws, estimators,
network access or physical-operator imports are used.

Example from repository root:
python docs/revisions/mahakal_v4_1/review025/localize_saved_modes_025.py \
  --modes artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/mode_export.json \
  --manifest artifacts/revisions/mahakal_v4_1/R2_REPLAY_TARGET_MANIFEST.json \
  --output artifacts/revisions/mahakal_v4_1/LOCALIZATION025_unique.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.linalg import eigvalsh
from scipy.special import roots_legendre


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_columns() -> np.ndarray:
    return np.array([(a * 7 + b) * 8 + k
                     for a in range(4) for b in range(1, 7) for k in range(3)])


def spatial_gram(model: dict, n: int, midpoint: bool = False) -> np.ndarray:
    """Analytic azimuthal integral and radial quadrature, with full cross terms.

    Four clamped cubic splines without interior knots are Bernstein cubics in
    log(radius), as in physical_basis.py. The six nonconstant Fourier columns
    are pairwise orthogonal with squared integral pi.
    """
    ri, ro = float(model['r_inner_M']), float(model['r_outer_M'])
    if not (0 < ri < ro):
        raise ValueError('Require a positive nonempty radial interval.')
    if midpoint:
        r = ri + (np.arange(n) + .5) * (ro-ri)/n
        weights = r * (ro-ri)/n
    else:
        x, w = roots_legendre(n)
        r = ri + (x+1)*(ro-ri)/2
        weights = w*(ro-ri)/2*r
    u = np.log(r/ri)/np.log(ro/ri)
    B = np.column_stack(((1-u)**3, 3*u*(1-u)**2, 3*u*u*(1-u), u**3))
    Hr = B.T @ (weights[:, None]*B)
    return np.kron(Hr, np.pi*np.eye(6))


def temporal_design(t: np.ndarray, model: dict) -> np.ndarray:
    lo, hi = float(model['t_min_M']), float(model['t_max_M'])
    width = (hi-lo)/8
    x = np.asarray(t, dtype=float)
    return (np.maximum(1-np.abs((x[:,None]-lo)/width-np.arange(3)), 0)
            * ((x >= lo) & (x <= hi))[:,None])


def interval_gram(lo: float, hi: float, model: dict) -> np.ndarray:
    """Exactly integrate temporal hat products, up to floating point.

    Each piece is quadratic. Three Gauss nodes per segment integrate it exactly;
    all hat breakpoints and requested interval endpoints are explicit.
    """
    if hi <= lo:
        raise ValueError('Require a nonempty interval.')
    t0, tmax = float(model['t_min_M']), float(model['t_max_M'])
    width = (tmax-t0)/8
    nodes = t0+width*np.arange(4)
    cuts = np.unique(np.r_[lo, nodes[(nodes > lo) & (nodes < hi)], hi])
    x, w = roots_legendre(3)
    G = np.zeros((3,3))
    for a,b in zip(cuts[:-1], cuts[1:]):
        T = temporal_design(a+(x+1)*(b-a)/2, model)
        G += T.T @ ((w*(b-a)/2)[:,None]*T)
    return .5*(G+G.T)


def analyze(modes: dict, manifest: dict) -> dict:
    model = manifest['source_class']
    if [model[k] for k in ('n_radial','n_azimuthal','n_temporal')] != [4,7,8]:
        raise ValueError('This diagnostic is restricted to the declared L224 layout.')
    arm = modes['RESOLVED_PHYSICAL']
    wanted = expected_columns()
    for key, obj in [('mode export', arm), ('target manifest', manifest)]:
        if not np.array_equal(np.asarray(obj['target_column_indices']), wanted):
            raise ValueError(f'{key}: unexpected target column ordering or set.')
    C = np.asarray(arm['source_coefficient_vectors'], dtype=float)[:2]
    if C.shape != (2,72) or not np.isfinite(C).all():
        raise ValueError('Require two finite 72-component source coefficient vectors.')
    t0, tmax = float(model['t_min_M']), float(model['t_max_M'])
    width = (tmax-t0)/8
    nodes = t0 + width*np.arange(4)
    intervals = [
        ('oldest_third', nodes[0], nodes[1]),
        ('middle_third', nodes[1], nodes[2]),
        ('youngest_third', nodes[2], nodes[3]),
        ('original_hat2_support', nodes[1], nodes[3]),
        ('youngest_fifth_of_target_union', nodes[3]-.2*(nodes[3]-nodes[0]), nodes[3]),
    ]
    Ht = interval_gram(nodes[0], nodes[3], model)
    fulls = [np.kron(spatial_gram(model,n),Ht) for n in (64,128,256)]
    H = fulls[-1]
    relative_steps = [float(np.linalg.norm(b-a)/np.linalg.norm(b))
                      for a,b in zip(fulls[:-1],fulls[1:])]
    if max(relative_steps) > 1e-10:
        raise ValueError(f'Independent source integration has not converged: {relative_steps}')
    N = C@H@C.T
    norms = np.diag(N)
    if not np.allclose(N, np.eye(2), rtol=0, atol=1e-5):
        raise ValueError(f'Exported mode normalization sanity check failed: {N}')
    Hs = spatial_gram(model,256)
    rows=[]
    for name, lo, hi in intervals:
        E = C @ np.kron(Hs, interval_gram(float(lo),float(hi),model)) @ C.T
        fraction = np.diag(E)/norms
        subspace = eigvalsh(.5*(E+E.T),.5*(N+N.T))
        if np.min(fraction) < -1e-10 or np.max(fraction)>1+1e-10:
            raise ValueError('Nonphysical interval energy fraction.')
        rows.append(dict(name=name,interval_M=[float(lo),float(hi)],
                         source_energy_fraction=fraction.tolist(),
                         subspace_fraction_min_max=[float(subspace[0]),float(subspace[-1])]))
    if not np.allclose(np.sum([r['source_energy_fraction'] for r in rows[:3]],axis=0),1,
                       rtol=0,atol=1e-12):
        raise ValueError('Disjoint intervals do not sum to full source energy.')
    # Reconstruct the same coordinate gauge as the source export for comparison.
    n=12800
    tm=t0+(np.arange(n)+.5)*(tmax-t0)/n
    T=temporal_design(tm,model)
    Htm=T.T@T*((tmax-t0)/n)
    Hmid=np.kron(spatial_gram(model,n,midpoint=True),Htm)
    R=np.linalg.cholesky(Hmid).T
    V=C@R.T
    coordinate_shares=(V.reshape(2,24,3)**2).sum(axis=1)/(V**2).sum(axis=1)[:,None]
    v_check=None
    if 'right_singular_vectors' in arm:
        expected_v=np.asarray(arm['right_singular_vectors'],float)[:2]
        if expected_v.shape != V.shape:
            raise ValueError('Right-vector shape mismatch.')
        v_check=float(np.max(np.abs(expected_v-V)))
        if v_check>1e-10:
            raise ValueError(f'Reconstructed coordinate vectors differ: {v_check}')
    return dict(
        schema='mahakal-saved-mode-source-localization/1',
        scope='Independent postprocessing of two saved coefficient vectors; no operator/SVD/test-suite replay.',
        reviewed_commit='1d99e99eec9c61eeece2d00b832b1e62e6047b2c',
        model_norm='r dr dphi dt, not proper-volume or source prior',
        target_union_M=[float(nodes[0]),float(nodes[3])],
        knot_times_M=nodes.tolist(),
        source_metric_independent_radial_refinements=[64,128,256],
        source_gram_relative_refinement_steps=relative_steps,
        source_mode_inner_product_matrix=N.tolist(),
        integration_note='Gauss radial plus exact piecewise-quadratic temporal integration; differs slightly from midpoint normalization used in archived modes.',
        intervals=rows,
        reconstructed_cholesky_coordinate_group_shares=coordinate_shares.tolist(),
        coordinate_vector_readback_max_abs=v_check,
        note='Coordinate shares are NOT energy in the original hats or time windows. The trace-by-coordinate diagnostic needs its own interpretation correction.',
    )


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modes',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        p.error('Output exists; choose a fresh path.')
    result=analyze(json.loads(args.modes.read_text()),json.loads(args.manifest.read_text()))
    result['inputs']={str(args.modes):digest(args.modes),str(args.manifest):digest(args.manifest)}
    result['environment']={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write('\n')
    for row in result['intervals']:
        print(row['name'],row['interval_M'],row['source_energy_fraction'])
    return 0


if __name__=='__main__':
    raise SystemExit(main())
