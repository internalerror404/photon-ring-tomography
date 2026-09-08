#!/usr/bin/env python3
"""Review 037: algebra/summary arithmetic and claim-record schema fixtures.
No campaign operator, spectrum, ray, source-mode integral, or repository suite.
Optional --matrix validates structure only; --repo additionally reads pinned
source bytes using git show. Neither mode proves semantic support for prose.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, subprocess, sys
from pathlib import Path
import numpy as np

PINS = ('operator','source_basis','source_Gram','sampled_rays','quadrature',
        'covariance','noise_normalisation','target_nuisance_partition',
        'estimator','evaluation_metric')

def validate_claims(matrix: dict, repo: Path | None = None) -> dict:
    errors = []
    for claim in matrix.get('claims', []):
        cid = claim.get('claim_id', 'MISSING_ID')
        refs = claim.get('evidence', [])
        if not refs:
            errors.append([cid, 'NO_STRUCTURED_EVIDENCE_REFERENCE'])
        for source in refs:
            ref, path, digest = (source.get(k) for k in ('commit','path','sha256'))
            valid = (isinstance(ref,str) and re.fullmatch(r'[0-9a-f]{40}',ref)
                     and isinstance(path,str) and not path.startswith('/')
                     and '..' not in Path(path).parts
                     and isinstance(digest,str) and re.fullmatch(r'[0-9a-f]{64}',digest)
                     and bool(source.get('selector')))
            if not valid:
                errors.append([cid, 'INCOMPLETE_REFERENCE_OR_SELECTOR']); continue
            if repo is not None:
                result = subprocess.run(['git','-C',str(repo),'show',f'{ref}:{path}'],
                                        capture_output=True, timeout=30)
                if result.returncode:
                    errors.append([cid, 'PINNED_SOURCE_UNREADABLE'])
                elif hashlib.sha256(result.stdout).hexdigest() != digest:
                    errors.append([cid, 'PINNED_SOURCE_HASH_MISMATCH'])
        pins = claim.get('pins', {})
        for key in PINS:
            entry = pins.get(key)
            if not isinstance(entry,dict) or not entry.get('status'):
                errors.append([cid, 'MISSING_PIN:'+key]); continue
            if entry['status'] == 'NOT_APPLICABLE':
                if not entry.get('reason'):
                    errors.append([cid, 'UNJUSTIFIED_NA:'+key])
            elif entry['status'] == 'RESOLVED':
                if 'value' not in entry or not entry.get('evidence_ref'):
                    errors.append([cid, 'UNSUPPORTED_PIN:'+key])
            elif entry['status'] == 'UNRESOLVED':
                if claim.get('candidate_abstract_or_headline_allowed'):
                    errors.append([cid, 'UNRESOLVED_PIN_PROMOTED:'+key])
            else:
                errors.append([cid, 'UNKNOWN_PIN_STATUS:'+key])
    if not matrix.get('claims'):
        errors.append(['MATRIX','EMPTY_CLAIMS'])
    return {'status':'SCHEMA_BLOCKED' if errors else 'SCHEMA_READY_FOR_SEMANTIC_REVIEW',
            'errors':errors, 'claim_count':len(matrix.get('claims',[])),
            'semantic_support_verified':False, 'physical_queries':0}

def run_checks() -> dict:
    checks = {}
    # Logical counterexamples, not a new astrophysical campaign.
    identity = np.eye(2)
    checks['enrichment_need_not_destroy_injectivity'] = (
        np.linalg.matrix_rank(identity[:,:1]) == 1 and np.linalg.matrix_rank(identity) == 2)
    checks['compact_support_alone_does_not_imply_direct_null'] = max(1-abs(0.25)/0.5,0)>0
    checks['disjoint_compact_temporal_support_gives_zero_samples'] = bool(
        np.all(np.maximum(1-np.abs((np.array([0.,1.])-(-3.))/.5),0)==0))
    old = np.array([.024396455213855257,.02351217590390685])
    mid = np.array([.4381078027023865,.43921537629618046])
    young = np.array([.5374957420837584,.5372724477999128])
    checks['saved_localization_partition_sums_to_one'] = bool(np.allclose(old+mid+young,1,atol=1e-14))
    checks['oldest_interval_is_not_zero_in_saved_modes'] = bool(np.all(old>.02))
    checks['known_and_conditional_trace_ratio_is_not_epoch_energy'] = abs(7.198318097661488/11.05366014165148-.651215796886805)<1e-12
    checks['sampled_oldest_age_is_not_anchor_span'] = 144-32==112 and 144-28==116
    checks['high_SNR_results_use_different_multipliers'] = 1000/100==10 and 30000/100==300
    # Schema-only fixture: all fields have explicit applicability, not generic prose.
    claim = {'claim_id':'FIXTURE','candidate_abstract_or_headline_allowed':False,
             'evidence':[{'commit':'a'*40,'path':'source.json','sha256':'b'*64,'selector':'/value'}],
             'pins':{k:{'status':'NOT_APPLICABLE','reason':'synthetic schema fixture'} for k in PINS}}
    checks['structured_fixture_accepted'] = not validate_claims({'claims':[claim]})['errors']
    copied = {'claim_id':'C01','source_commit_path_and_hash':'artifacts/manuscript/PAPER_I.md',
              'source_operator_metric_and_noise_assumptions':'single-sky noise; declared norm'}
    checks['path_only_and_global_pin_list_rejected'] = bool(validate_claims({'claims':[copied],'pins_recorded_per_claim':list(PINS)})['errors'])
    broken = copy.deepcopy(claim); broken['evidence'][0].pop('selector')
    checks['missing_row_selector_rejected'] = bool(validate_claims({'claims':[broken]})['errors'])
    broken = copy.deepcopy(claim); broken['pins']['covariance']={'status':'UNRESOLVED'}; broken['candidate_abstract_or_headline_allowed']=True
    checks['unresolved_covariance_cannot_be_promoted'] = bool(validate_claims({'claims':[broken]})['errors'])
    checks = {key: bool(value) for key, value in checks.items()}
    if not all(checks.values()): raise AssertionError(checks)
    return {'scope':__doc__, 'checks':checks,'n_checks':len(checks),'all_passed':True,
            'source_values':'Explicit transcription from LOCALIZATION_READBACK.json and reference_geometry_information.csv at 8c309ff; no source-mode recomputation.',
            'reviewed_commit':'8c309ff6736e8933df37b9f8e61bcdb495980aec',
            'environment':{'python':sys.version.split()[0],'numpy':np.__version__},
            'campaign_queries':0,'repository_suite_executed':False,
            'original_036_matrix_run_through_script':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--matrix',type=Path); p.add_argument('--repo',type=Path)
    p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    if a.output.exists(): p.error('Choose a fresh output path')
    out=validate_claims(json.loads(a.matrix.read_text()),a.repo) if a.matrix else run_checks()
    out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(out,indent=2,allow_nan=False)+'\n'
    with a.output.open('x') as f: f.write(serialized)
    print(out.get('status',f"{out.get('n_checks')} local checks passed"))
if __name__=='__main__': main()
