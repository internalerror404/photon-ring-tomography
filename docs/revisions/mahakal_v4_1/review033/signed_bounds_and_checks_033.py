#!/usr/bin/env python3
"""Review 033: interval arithmetic and source-derived cost checks only.

No real Kerr rays, path integrations, hull roots, source spectra or repository
suite execution. The bound routine propagates SUPPLIED leaf intervals; it does
not infer physical envelopes from midpoint samples or certify their provenance.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import platform
import numpy as np


def interval_sum(rows, weights, chi_lo, chi_hi, field_lo, field_hi,
                 n_detector: int, known=None):
    """Sum interval products w*chi*f using nonnegative overlap weights.

    Arrays chi_* have one entry per overlap; field_* are (overlap, field).
    Repeated overlaps may refer to one leaf; the returned componentwise box is
    conservative and need not encode those correlations. For physical bounds,
    all supplied intervals must bound their functions over their active leaf,
    not just at a sample. Detector covariance/whitening is not changed here.
    """
    r = np.asarray(rows)
    w = np.asarray(weights, dtype=float)
    cl = np.asarray(chi_lo, dtype=float)
    ch = np.asarray(chi_hi, dtype=float)
    fl = np.asarray(field_lo, dtype=float)
    fh = np.asarray(field_hi, dtype=float)
    if not isinstance(n_detector, int) or n_detector < 1:
        raise ValueError('n_detector must be a positive integer')
    if r.ndim != 1 or not np.issubdtype(r.dtype, np.integer):
        raise ValueError('rows must be a one-dimensional integer array')
    if fl.ndim == 1:
        fl = fl[:, None]
    if fh.ndim == 1:
        fh = fh[:, None]
    m = r.size
    if (w.shape != (m,) or cl.shape != (m,) or ch.shape != (m,)
            or fl.ndim != 2 or fl.shape != fh.shape or fl.shape[0] != m):
        raise ValueError('incompatible overlap and interval shapes')
    if np.any(r < 0) or np.any(r >= n_detector):
        raise ValueError('detector index out of range')
    if not all(np.isfinite(v).all() for v in (w, cl, ch, fl, fh)):
        raise ValueError('missing finite envelope: do not replace with zero')
    if (np.any(w < 0) or np.any(cl < 0) or np.any(ch > 1)
            or np.any(cl > ch) or np.any(fl > fh)):
        raise ValueError('invalid weight, validity or field interval')
    products = np.stack([cl[:, None]*fl, cl[:, None]*fh,
                         ch[:, None]*fl, ch[:, None]*fh])
    lower_terms = w[:, None] * products.min(axis=0)
    upper_terms = w[:, None] * products.max(axis=0)
    shape = (n_detector, fl.shape[1])
    base = np.zeros(shape) if known is None else np.asarray(known, dtype=float)
    if base.shape != shape or not np.isfinite(base).all():
        raise ValueError('invalid known response')
    lower, upper = base.copy(), base.copy()
    np.add.at(lower, r, lower_terms)
    np.add.at(upper, r, upper_terms)
    return lower, upper


def run_checks():
    results = []
    def check(name, condition):
        results.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    lo, hi = interval_sum([0], [.25], [0], [1], [-2], [-2], 1)
    old_lo, old_hi = 0., .5  # current known + |field| construction
    check('negative_field_old_box_excludes_valid_emitting_value',
          not old_lo <= -.5 <= old_hi)
    check('negative_field_correct_box_is_minus_half_to_zero',
          lo.item() == -.5 and hi.item() == 0)
    lo_p, hi_p = interval_sum([0], [.25], [0], [1], [2], [2], 1)
    check('nonnegative_occupancy_case_is_preserved',
          lo_p.item() == 0 and hi_p.item() == .5)
    lo_m, hi_m = interval_sum([0], [.25], [0], [1], [-2], [2], 1)
    check('magnitude_only_envelope_needs_symmetric_uncertainty',
          lo_m.item() == -.5 and hi_m.item() == .5)
    rows = np.array([0, 0, 1])
    weights = np.array([.2, .3, .4])
    values = np.array([[-2., 3.], [5., -1.], [-4., -2.]])
    lo_e, hi_e = interval_sum(rows, weights, [0]*3, [1]*3,
                             values, values, 2)
    for bits in itertools.product([0., 1.], repeat=3):
        actual = np.zeros((2, 2))
        np.add.at(actual, rows, weights[:, None]*np.array(bits)[:, None]*values)
        check('exhaustive_validity_corner_'+''.join(str(int(b)) for b in bits),
              np.all(actual >= lo_e-1e-15) and np.all(actual <= hi_e+1e-15))
    rng = np.random.default_rng(33)
    fl = rng.uniform(-4, 1, (3, 2)); fh = fl + rng.uniform(0, 5, (3, 2))
    cl = np.array([0., .2, .4]); ch = np.array([.6, .9, 1.])
    lr, ur = interval_sum(rows, weights, cl, ch, fl, fh, 2)
    valid = True
    for _ in range(200):
        f = fl + rng.random((3,2))*(fh-fl)
        chi = cl + rng.random(3)*(ch-cl)
        actual = np.zeros((2,2))
        np.add.at(actual, rows, weights[:,None]*chi[:,None]*f)
        valid &= np.all(actual >= lr-1e-14) and np.all(actual <= ur+1e-14)
    check('random_signed_interval_samples_enclosed', valid)
    for name, kwargs in [
        ('missing_field_envelope_rejected', {'field_hi': [np.nan]}),
        ('negative_overlap_rejected', {'weights': [-.1]}),
        ('reversed_field_interval_rejected', {'field_lo': [3], 'field_hi': [2]}),
        ('invalid_validity_interval_rejected', {'chi_hi': [1.1]})]:
        args = dict(rows=[0], weights=[.25], chi_lo=[0], chi_hi=[1],
                    field_lo=[-2], field_hi=[2], n_detector=1)
        args.update(kwargs)
        caught = False
        try:
            interval_sum(**args)
        except ValueError:
            caught = True
        check(name, caught)
    counts = [331, 661, 1584, 3183, 5177, 11300]
    total_parents = sum(counts)
    matrix_cost = total_parents*(4+16)
    check('source_derived_uniform_matrix_cost_reproduced',
          total_parents == 22236 and matrix_cost == 444720)
    native, primary_path, reference = 13566, 10806, 4806
    charged = native + reference
    remainder = 20000-charged
    check('convention_B_selected_balance', charged == 18372 and remainder == 1628)
    check('primary_path_is_recorded_component_not_second_native_charge',
          primary_path == 10806 and charged != native+primary_path+reference)
    check('bounded_diagnostic_fits_without_new_batch',
          66+192 == 258 and 3*258 == 774 and 774 <= 1024 <= remainder)
    check('diagnostic_cap_leaves_balance', remainder-1024 == 604)
    # Geometric 1-D counterexample: a known single-crossing indicator does not
    # require uniform refinement everywhere. This is not a physical cost forecast.
    crossing = .371234
    left, right, calls = 0., 1., 0
    while right-left > 1e-5:
        mid = .5*(left+right); calls += 1
        if mid < crossing:
            left = mid
        else:
            right = mid
    uniform_bins_for_same_width = int(np.ceil(1/1e-5))
    check('synthetic_single_boundary_localization_has_nonuniform_cost',
          left <= crossing <= right and right-left <= 1e-5
          and calls < uniform_bins_for_same_width)
    return dict(
        scope=__doc__.strip(),
        reviewed_commit='303dfb640a6f5895641a82ae0aaa71bd1e0ae642',
        checks=results, n_checks=len(results), all_passed=True,
        negative_field_example=dict(overlap=.25, field=-2,
                                    old_interval=[old_lo,old_hi],
                                    correct_interval=[float(lo.item()),float(hi.item())]),
        cost_check=dict(transition_parents=counts, total=total_parents,
                        uniform_new_point_cost=matrix_cost,
                        ratio_to_native_spendable=matrix_cost/2434,
                        ratio_to_lifetime_cap=matrix_cost/250000,
                        is_lower_bound_for_every_integration_scheme=False),
        ledger_check=dict(native=native, primary_path_component=primary_path,
                          independent_reference=reference,
                          convention_B_spend=charged, remaining=remainder,
                          diagnostic_cap=1024, remaining_at_full_diagnostic_cap=604),
        synthetic_boundary=dict(assumptions='one monotone crossing of known topology',
                                bracket=[left,right], midpoint_queries=calls,
                                uniform_intervals_for_same_spacing=uniform_bins_for_same_width,
                                not_a_Kerr_cost_forecast=True),
        environment=dict(python=platform.python_version(), numpy=np.__version__),
        actual_campaign_queries=0, repository_suite_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    if a.output.exists():
        p.error('Refusing to overwrite output')
    result=run_checks()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False); f.write('\n')
    print(f"{result['n_checks']} checks passed; zero campaign queries")

if __name__=='__main__':
    main()
