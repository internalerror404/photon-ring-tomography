"""Final report data, table and byte verification. No physical computation."""
from pathlib import Path
import json,hashlib,platform
from collections import Counter
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/RESULTS.json').read_text());c=json.loads((ROOT/'results/CLOSEOUT.json').read_text());training=json.loads((ROOT/'results/training.json').read_text())
rows=[]
for name,v in c['models'].items():
    group,seed=name.split('_');rows.append({'method':group,'seed':int(seed) if group!='classical' else None,
      'physical_calibration_nodes':int(seed)**2 if group=='classical' else 81,
      'max_channel_relative_error':v['max_channel_error'],'median_channel_relative_error':v['median_channel_error'],
      'failed_columns_of64':v['channels_failing'],'supplement_split_q4_vs_q8':v['split_q4_q8_max_relative'],
      'source':'fixed coefficients; supplementary knot-split detector integration'})
df=pd.DataFrame(rows);df.to_csv(ROOT/'results/PER_MODEL_RESULTS.csv',index=False)
counts=Counter(json.loads(x)['method'] for x in (ROOT/'attempts/physical_calls.jsonl').read_text().splitlines())
paired=[]
for seed in (11,22,33):
    a=c['models'][f'data_{seed}']['max_channel_error'];b=c['models'][f'physics_{seed}']['max_channel_error'];paired.append((a-b)/a)
summary={'experiment':'Mahakal II Kerr transfer-chart pilot003','registration_commit':'9d9972a60469b57c80a66454b699cba366513cdc',
 'status':'LOCAL_CLASSICAL_CHART_COMPARISON_PASS_NEURAL_CANDIDATES_NOT_PROMOTED',
 'units':'M=1; detector errors dimensionless; every column own reference norm',
 'methods':rows,'per_seed_physics_reduction_vs_data':paired,'median_paired_reduction':float(np.median(paired)),
 'checks':r['checks'],'all_12_checks_pass':r['all_checks_pass'],'frozen_coefficient_readback_error':c['coefficient_readback_max_abs'],
 'models_unchanged':c['fixed_model_files_unchanged'],'physical_attempt_counts':dict(counts),
 'training_integral_evaluations_completed_fits':sum(x['training_residual_integral_evaluations'] for x in training),
 'additional_freeze_and_native_physics_integrals':3*1089+3*128+3*144,
 'incomplete_training_attempt':'partial seed33 physics fit terminated by tool timeout; work not fully counted; conservative upper bound one extra full fit; no endpoint/calibration replay',
 'total_completed_training_seconds':sum(x['seconds'] for x in training),'evaluation_seconds':r['evaluation_seconds'],'supplement_seconds':c['seconds'],
 'reference_validation':json.loads((ROOT/'results/independent_validation.json').read_text())['max_absolute_tuple_error'],
 'reference_detector_q10_q16':r['reference_pairs']['10'],'independent_matched_q3_detector_error':r['ODE_matched_rule_detector_error'],
 'new_physical_PaperII_evaluations_not_charged_to_PaperI854':True,
 'PaperI_modified':False,'PaperI_remaining':854,
 'full_Kerr_acquisition_qualified':False,'rigorous_global_interval_certificate':False,'source_inverse_experiment':False,
 'limitations':r['limitations'],'protocol_differences':['Geometry-only scouting and pre-registration solver repair disclosed.',
 'Partial training timeout resumed only incomplete seed without changed hyperparameters.',
 'Knot-split detector quadrature supplement applied after primary results; both retained; no new candidate.',
 'Native-vs-frozen conversion checked on common q3 detector nodes, not global sup norm.',
 'Independent solver uses same metric/constants and redshift prescription but different numerical path/angle evolution.',
 'Endpoint integral-equation PINN rather than differential source-dynamics PINN.']}
(ROOT/'SUMMARY.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
# Read all array files, force materialization and verify finite expected arrays.
arrayrecords=[]
for p in sorted(ROOT.rglob('*.npz')):
    a=np.load(p,allow_pickle=False)
    keys={k:{'shape':list(a[k].shape),'dtype':str(a[k].dtype),'finite':bool(np.isfinite(a[k]).all()) if np.issubdtype(a[k].dtype,np.number) else None} for k in a.files}
    arrayrecords.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'arrays':keys})
(ROOT/'ARRAY_MANIFEST.json').write_text(json.dumps(arrayrecords,indent=2)+'\n')
print(df.to_string(index=False));print('COUNTS',counts,'PAIRED',paired)
