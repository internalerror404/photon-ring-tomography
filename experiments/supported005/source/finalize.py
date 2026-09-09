"""Final derived reporting: repair a reporting-only relative-error argument;
refine the B72 source-loss readback without changing any field or estimator.
The raw BOX_METRIC.json and its failed 6-vs8 loss gate remain untouched.
"""
from box_metric import *
import copy

def finish():
    t0=time.perf_counter();raw=json.loads((ROOT/'results/RESULTS.json').read_text())
    num=json.loads((ROOT/'results/NUMERICAL_CLOSEOUT.json').read_text())
    box=copy.deepcopy(json.loads((ROOT/'results/BOX_METRIC.json').read_text()))
    old=np.load(PARENT/'results/NEURAL_ARRAYS.npz');ma=np.load(ROOT/'results/ARRAYS.npz');ba=np.load(ROOT/'results/BOX_METRIC_ARRAYS.npz')
    resp=np.load(PARENT/'results/PHYSICAL_FITTED_RESPONSE_READBACK.npz');sig=old['std'];coords=old['eval_coords']
    # The original helper relative(a,b) means ||a-b||/||b||. Two chart-only
    # report columns accidentally passed a=error instead of a=prediction-1.
    # Correct these columns by exact readback. Box loss and data results unchanged.
    for row in box['decompositions']:
        key=f"{row['scenario']}_{row['method']}_q8_s{row['seed']}"
        row['chart_source_error']=prior.relative(old['prediction_'+key]-1,old['truth_'+row['scenario']]-1)
    cached={}
    for row in box['corrections']:
        name=row['basis'];shape=next(s for s in CFG['source_dictionary']['nested_classes'] if np.prod(s)==int(name[1:]))
        if name not in cached:
            X=ba[name+'_X'];V=ba[name+'_V'];s=ba[name+'_s'];B=ma[name+'_A16']@X/sig[:,None]
            u,ss,vt=svd(B,full_matrices=True);cached[name]=(X,vt.T,ss,u,dictionary(coords,shape))
        X,V,s,u,Q=cached[name];key=f"{row['scenario']}_{row['method']}_q8_s{row['seed']}";k=row['modes']
        obs=old[f"noisy_{row['scenario']}_s{row['seed']}"];res=(obs-resp[key+'_physical_q16'])/sig
        dc=V[:,:k]@((u[:,:k].T@res)/s[:k]);pred=old['prediction_'+key];new=pred+Q@X@dc
        truth=old['truth_'+row['scenario']]
        row['raw_chart_error']=prior.relative(pred-1,truth-1)
        row['corrected_chart_error']=prior.relative(new-1,truth-1)
    # The single B72 source-loss check failed at 6/8 nodes, not the exact Gram
    # or detector. Use one fixed higher pair12/16 on the SAME saved fields.
    refinements=[]
    c12,w12=rule3([4,6,3],12);c16,w16=rule3([4,6,3],16)
    for scenario in ('background','events'):
        coeff=prior.truth_coefficients(scenario=='events');t12=prior.fields(c12,coeff);t16=prior.fields(c16,coeff)
        for method in ('data_only','robust_pinn'):
          for seed in (11,22,33):
            key=f'{scenario}_{method}_q8_s{seed}';net=Field();net.load_state_dict(torch.load(PARENT/'models'/f'{key}.pt',weights_only=True))
            with torch.no_grad():p12=net(ten(c12)).numpy();p16=net(ten(c16)).numpy()
            e12=wrms(p12-t12,w12);e16=wrms(p16-t16,w16)
            refinements.append({'id':key,'RMS12':e12,'RMS16':e16,'abs_change':abs(e12-e16)})
    correction_note={'relative_error_bug':'Only BOX_METRIC chart-error report columns supplied error as first input to relative() rather than prediction contrast. All corrected by readback here; original raw source retained. Does NOT affect full-box errors, mode matrices, inverse correction, primary experiment, spectra or witness.',
        'B72_source_loss_resolution':'Postplanned12/16 per-piece reference pair of fixed fields; not retraining or changing source norm/acceptance threshold.',
        'B72_readback':refinements,'B72_max_abs_change_12_16':max(x['abs_change'] for x in refinements),
        'B72_same_gate_passes_12_16':max(x['abs_change'] for x in refinements)<1e-4}
    dump('results/REPORTING_CORRECTION.json',correction_note)
    dump('results/BOX_METRIC_READBACK.json',box)
    pd.DataFrame(box['decompositions']).to_csv(ROOT/'results/BOX_DECOMPOSITIONS.csv',index=False)
    pd.DataFrame(box['corrections']).to_csv(ROOT/'results/BOX_CORRECTIONS.csv',index=False)
    d=pd.DataFrame(box['decompositions']);c=pd.DataFrame(box['corrections']);rawc=pd.DataFrame(raw['corrections'])
    primary=d[(d.basis=='B135')&(d.threshold==5)];primcor=c[(c.basis=='B135')&(c.threshold==5)]
    summary={'experiment':'Mahakal II support/prior separation005','status':'MODE_OVERWRITE_NOT_PROMOTED; CONDITIONAL_IDENTIFIABILITY_AND_SOURCE_NORM_LIMITS_ESTABLISHED_AT_NUMERICAL_SCOPE',
      'registration_commit':'2a5cc4df7f9134ea89094baf28d080d512d56dea',
      'primary_chart_norm_bases':[{k:v for k,v in b.items() if k not in ['spectrum','metric_singular_values']} for b in raw['bases']],
      'main_registered_checks':raw['checks'],'same_span_precision_closeout':num['checks'],
      'box_metric_is_postplanned':True,'box_norm_bases':[{k:v for k,v in b.items() if k!='spectrum'} for b in box['spectra']],
      'box_primary_error_decomposition':primary.groupby(['scenario','method'])[['box_source_error','chart_source_error','high_response_squared_error_fraction','weak_squared_error_fraction','outside_squared_error_fraction']].mean().reset_index().to_dict(orient='records'),
      'box_primary_correction_medians':primcor.groupby(['scenario','method'])[['raw_box_error','corrected_box_error','raw_chart_error','corrected_chart_error','raw_whitened_residual','corrected_whitened_residual']].median().reset_index().to_dict(orient='records'),
      'box_primary_number_worse':int((primcor.corrected_box_error>primcor.raw_box_error).sum()),'box_primary_comparisons':len(primcor),
      'all_box_corrections_worse':bool((c.corrected_box_error>c.raw_box_error).all()),'all_corrections_count':len(c),
      'nuisance_target_stress':raw['nuisance_stress'],'original7_amplitude_singular_values':raw['original7_target_singular_values'],
      'positive_box_witness':box['witness'],
      'source_loss_refinement':{'max_12_16':correction_note['B72_max_abs_change_12_16'],'same_gate_pass':correction_note['B72_same_gate_passes_12_16']},
      'new_neural_training':0,'saved_models_read':12,'main_mode_corrections':len(raw['corrections']), 'box_mode_corrections':len(c),
      'new_rays':0,'new_physical_integrals':0,'new_roots':0,'PaperI_remaining':854,
      'seconds':{'primary':raw['seconds'],'precision_closeout':num['seconds'],'box_diagnostic':box['seconds'],'report_readback':time.perf_counter()-t0},
      'limitations':['one previously chosen order2 chart; no direct-image comparison or observational feasibility',
        'source dictionaries/norm/amplitude thresholds control mode counts; not nonlinear-neural identifiability certificates',
        'source error outside chosen dictionary can affect observations; nonzero projection bias must remain explicit',
        'extended signed-nuisance model has no bound or positivity prior; its loss of amplitude identifiability is conditional',
        'new full-box norm changes the target relative to original chart-sample metric; reported separately',
        'no source-training data or threshold selected from oracle coefficient readback',
        'null witness is a fixed positive polynomial field; near-equivalent observations checked numerically, not globally rigorously enclosed']}
    dump('SUMMARY.json',summary)
    print('FINAL counts',summary['box_primary_number_worse'],summary['box_primary_comparisons'],'B72 q',correction_note['B72_max_abs_change_12_16'],flush=True)
if __name__=='__main__':finish()
