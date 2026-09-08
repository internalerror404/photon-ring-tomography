"""Remaining registered cached algebra and secondary diagnostics. No new fit/ray."""
from support import *
def run():
    f=np.load(OUT/'forward_arrays.npz');w=f['weights'];a=f['areas'];d=f['reference_delay'];rng=np.random.default_rng(3023)
    x=rng.normal(size=(*d.shape,3));y=rng.normal(size=x.shape)
    def op(z):return np.sum(w[...,None]*z,axis=1)/np.sqrt(a[:,None])
    linear=float(np.max(abs(op(.7*x-.2*y)-(.7*op(x)-.2*op(y)))))
    # A common coordinate-time offset must shift both observer time and delay.
    t=13.;c=23.;phase=max(float(np.max(abs(np.exp(2j*np.pi*(t-d)/p)-np.exp(2j*np.pi*((t+c)-(d+c))/p))))for p in [20.,40.])
    checks={'fixed_response_superposition':linear<1e-12,'common_time_origin_invariance':phase<1e-12}
    p=np.load(OUT/'inverse_predictions.npz');xy=p['coordinates'];old=p['old_mask'];rows=[]
    for b in [0,1]:
      for ss in [101,202,303]:
       for method in ['data','quadratic','innovation']:
        for kind in ['direct','matched','single','double']:
          tag=f'test_b{b}_s{ss}_{method}_{kind}';m=Field();m.load_state_dict(torch.load(OUT/f'{tag}.pt',weights_only=True));dd=design([0] if kind=='direct' else [0,1,2]);sig=.01*np.sqrt(dd[2]);chi=float(np.mean(((predict(m,dd)-p[tag+'_observations'])/sig)**2))
          for ek in (['matched','single','double'] if kind=='direct' else [kind]):
            row=dict(background=b,seed=ss,method=method,fit=kind,evaluated_source=ek,noisy_training_data_chi2=chi)
            if ek!='matched':
              ev=p[f'truth_b{b}_{ek}']-p[f'truth_b{b}_matched'];got=p[tag]-p[f'truth_b{b}_matched'];idx=old&(abs(ev)>.01)
              row['event_norm_ratio_using_true_background']=float(np.linalg.norm(got[idx])/np.linalg.norm(ev[idx]));row['event_projection_using_true_background']=float(got[idx]@ev[idx]/(ev[idx]@ev[idx]))
            rows.append(row)
    save('extra_checks.json',dict(checks=checks,all_pass=all(checks.values()),superposition_max_abs=linear,common_time_origin_max_abs=phase,secondary_diagnostics=rows,event_metric_scope='Uses true background for evaluation only, not an inferred source separation.',new_physical_evaluations=0,new_fits=0))
    print(checks,linear,phase)
if __name__=='__main__':run()
