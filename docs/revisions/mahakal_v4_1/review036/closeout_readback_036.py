#!/usr/bin/env python3
"""Review 036: arithmetic readback of explicit connector-returned summaries.

No campaign NPZ, ray map, geodesic, physical quadrature, target spectrum, or
repository test suite is executed. The numerical inputs below are transcribed
from the named JSON sources at the reviewed commit, not a locally rehashed
copy of those source files. Run with --output naming a new file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

COMMIT = '04572c8fa8a90b89e95a64b440ec5d90962cfd7b'
PREFIX = 'artifacts/revisions/mahakal_v4_1/Q035_20260908T004247Z_c1bf640/'
INPUTS = [
    dict(order=0, baseline=0.009593926019841242, candidate=0.009717724310099523,
         baseline_median=0.00373177141946304, candidate_median=0.003854746871573399,
         max_A_over_E=1.1015099071264431, max_T_over_A=20.015057536251767,
         max_T_over_E=20.628656941744644,
         point_identity=6.078471059822732e-15, detector_identity=1.1191048088221578e-13),
    dict(order=1, baseline=0.04274351473611188, candidate=0.08479504940405201,
         baseline_median=0.02845257124912427, candidate_median=0.04430425103859163,
         max_A_over_E=4.569057718344865, max_T_over_A=9.023017418644352,
         max_T_over_E=41.04532593548384,
         point_identity=6.679552744248696e-15, detector_identity=3.907985046680551e-14),
    dict(order=2, baseline=0.5116029567264959, candidate=0.6536382198807053,
         baseline_median=0.2629626499643508, candidate_median=0.169999185864314,
         max_A_over_E=4.708960202106982, max_T_over_A=6.725847197904428,
         max_T_over_E=31.353133225918388,
         point_identity=6.404599073306372e-15, detector_identity=4.954370247389761e-15),
]


def run() -> dict:
    budget, identity_atol = 5e-4, 1e-12
    rows = []
    for r in INPUTS:
        if not all(math.isfinite(v) for v in r.values()):
            raise ValueError('nonfinite transcribed input')
        if r['baseline'] <= 0 or r['candidate'] <= 0:
            raise ValueError('positive reference-relative error required for ratios')
        rows.append(dict(**r,
            candidate_over_baseline=r['candidate']/r['baseline'],
            change_in_max_percent=100*(r['candidate']/r['baseline']-1),
            baseline_multiple_of_budget=r['baseline']/budget,
            candidate_multiple_of_budget=r['candidate']/budget,
            product_of_separate_ratio_maxima=r['max_A_over_E']*r['max_T_over_A'],
            median_change_percent=100*(r['candidate_median']/r['baseline_median']-1)))
    tests = {
        'candidate_worse_by_registered_max_at_every_order': all(r['candidate']>r['baseline'] for r in rows),
        'both_maxima_outside_budget_at_every_order': all(min(r['candidate'],r['baseline'])>budget for r in rows),
        'order2_median_improves_but_maximum_worsens': rows[2]['candidate_median']<rows[2]['baseline_median'] and rows[2]['candidate']>rows[2]['baseline'],
        'point_identity_below_original_tolerance': max(r['point_identity'] for r in rows)<identity_atol,
        'detector_identity_below_original_tolerance': max(r['detector_identity'] for r in rows)<identity_atol,
        'ratio_maxima_product_not_reported_max_product': any(not math.isclose(r['product_of_separate_ratio_maxima'],r['max_T_over_E'],rel_tol=1e-6) for r in rows),
        'max_product_upper_bound_is_consistent': all(r['max_T_over_E']<=r['product_of_separate_ratio_maxima']*(1+1e-12) for r in rows),
        'reported_second_batch_balance': 20000-19146==854,
    }
    if not all(tests.values()):
        raise AssertionError(tests)
    return dict(
        schema='mahakal-review036-arithmetic/1', reviewed_commit=COMMIT,
        scope=__doc__.strip(),
        summary_sources=[dict(path=PREFIX+'PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json',
                              connector_reported_blob='d31e4c3f03ffad5f96ad72b0cddab441947119e4'),
                         dict(path=PREFIX+'HARMONIC_TEMPLATE_IDENTITY_035.json',
                              connector_reported_blob='3ef43b9b84536bf426d9b619dc632ac361f2b003')],
        input_method='Explicit transcription of connector-returned summary values; source files not locally rehashed.',
        per_order=rows,
        identity_global_max=dict(pointwise=max(r['point_identity'] for r in rows),
                                 after_detector=max(r['detector_identity'] for r in rows),
                                 acceptance_atol=identity_atol),
        tests=tests, n_arithmetic_checks=len(tests), all_passed=True,
        limitation='No per-channel distribution or campaign array values were independently recomputed.',
        physical_queries=0, repository_suite_executed=False,
        environment=dict(python=platform.python_version()))


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    args=ap.parse_args()
    if args.output.exists():
        ap.error('Refusing to overwrite existing output')
    result=run()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write('\n')
    print(f"{result['n_arithmetic_checks']} arithmetic checks passed; zero campaign queries")

if __name__=='__main__':
    main()
