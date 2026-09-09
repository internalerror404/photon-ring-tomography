"""Summaries and readback records only. No fitting or physical ray evaluations."""
from common import *
import pandas as pd

def run():
    if not (ROOT/'results/VERIFICATION.json').exists():
        from verify import run as verify
        verify()
    linear=json.loads((ROOT/'results/LINEAR_RESULTS.json').read_text())
    neural=json.loads((ROOT/'results/NEURAL_RESULTS.json').read_text())
    ver=json.loads((ROOT/'results/VERIFICATION.json').read_text())
    frame=pd.DataFrame(neural['results'])
    ss=frame.groupby(['scenario','method','training_quadrature'])['contrast_error_chart_pullback'].agg(['median','min','max']).reset_index()
    ss.to_csv(ROOT/'results/NEURAL_SUMMARY.csv',index=False)
    comparison=[]
    for sc in ['background','events']:
        for q in [3,8]:
            d=frame[(frame.scenario==sc)&(frame.training_quadrature==q)]
            a=d[d.method=='data_only'].sort_values('seed')['contrast_error_chart_pullback'].to_numpy()
            b=d[d.method=='robust_pinn'].sort_values('seed')['contrast_error_chart_pullback'].to_numpy()
            comparison.append({'scenario':sc,'training_quadrature':q,'paired_relative_reductions':((a-b)/a).tolist(),
                 'median_paired_reduction':float(np.median((a-b)/a)),'improved_seeds':int(np.sum(b<a)),'pairs':3})
    quadgroups=[]
    for q in [3,8]:
        idx=[x for x in ver['rows'] if f'_q{q}_s' in x['id']]
        quadgroups.append({'training_q':q,'fits':len(idx),'max_actual_reference_whitened_discrepancy':max(x['training_vs_physical_ref_whitened'] for x in idx),
            'max_actual_reference_relative_discrepancy':max(x['training_vs_physical_ref_relative'] for x in idx),
            'all_pass':all(x['actual_fitted_field_check_pass'] for x in idx)})
    allchecks={**{'linear/'+k:v for k,v in linear['checks'].items()},**{'readback/'+k:v for k,v in ver['checks'].items()}}
    out={'experiment':'Mahakal II local Kerr inverse004','registration_commit':'9098fa5f5d5ee874738b8220367a8adb5f90f400','source_freeze_commit':'ed32d24d3e42ef09caaa0e4be6bd03754d389a2b',
       'status':'LOCAL_KNOWN_TEMPLATE_INVERSE_SUPPORTED; FREE_NEURAL_FIELD_NOT_FULL_HISTORY_RECOVERY',
       'linear':linear['models'],'known_event_amplitude_model':{'nuisance':7,'targets':2,'source_histories':32,'noise_draws_per_history':64,'estimates':16384,'shapes_known':True},
       'neural_summary':ss.to_dict(orient='records'),'paired_PINN_comparison':comparison,'quad_training_groups':quadgroups,
       'neural_fits':24,'seconds':{'linear':linear['seconds'],'neural_training':sum(x['seconds'] for x in neural['results']), 'neural_including_readbacks':neural['elapsed'],'supplement':ver['seconds']},
       'finite_MC_coverage_interval':ver['joint95_coverage_binomial_interval'],'known_template_event_power':ver['known_template_event_power'],
       'maximum_reference_q10_q16_fitted_field_relative':max(x['physical_reference_q10_q16_relative'] for x in ver['rows']),
       'maximum_spline33_tuple_plus_jacobian_fitted_whitened_defect':max(x['q24_surrogate_vs_physical_q16_whitened'] for x in ver['rows']),
       'jacobian_spline_max_relative_weight_error':linear['jacobian_relative_error_max'],
       'checks':allchecks,'all_checks_passed':bool(all(allchecks.values())),'negative_prediction_fraction_max':float(frame.negative_prediction_fraction.max()),
       'new_rays':0,'new_path_quadratures':0,'new_hull_critical_roots':0,'PaperI_remaining':854,'production_suite_run':False,
       'scope':['one previously selected order2 patch and fixed Kerr/emitter model','No direct-order image comparison or full-sky reconstruction',
                'Template-amplitude uncertainty assumes known shapes and seven nuisance functions; not a map of pixel confidence',
                'Neural field metric restricted to chart pullback and tested observer window',
                'Three noise/initialization seeds on two source scenarios; not a broad source-family benchmark',
                'Fine-training comparison equal optimizer steps, not equal computation time',
                'Neural physical-readback supplement was added after partial outcomes; no model/threshold changed',
                'Reference numerical accuracy inherited from independent chart003 checks and current field quadrature refinements; no global interval proof'],
       'environment':{'numpy':np.__version__,'torch':'2.10.0+cpu','precision':'float64','threads':1}}
    dump('SUMMARY.json',out)
    manifests=[]
    for p in sorted(ROOT.rglob('*.npz')):
        f=np.load(p,allow_pickle=False)
        manifests.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
          'keys':{k:{'shape':list(f[k].shape),'dtype':str(f[k].dtype),'finite':bool(np.isfinite(f[k]).all()) if f[k].dtype.kind in 'fciub' else None} for k in f.files}})
    dump('ARRAY_MANIFEST.json',manifests)
    print(ss.to_string(index=False));print('Checks',len(allchecks),out['all_checks_passed'])
if __name__=='__main__':run()
