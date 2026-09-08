"""Independent postfit diagnostics. Does not retrain or retune any candidate."""
from support import *
from inverse002 import parameters,source,design,response
import hashlib,platform,scipy

def main():
    inv=json.loads((OUT/'inverse_test.json').read_text());fw=json.loads((OUT/'forward_results.json').read_text());ps=np.load(OUT/'inverse_predictions.npz')
    tests={};details=[]
    tests['all_twin_direct_vectors_exactly_equal']=all(x['direct_max_abs']==0 for x in inv['twin_checks'])
    # Independent quadrature readback on each learned field (fixed data, no fits).
    for b in [0,1]:
      for ss in [101,202,303]:
       for method in ['data','quadratic','innovation']:
        for kind in ['direct','matched','single','double']:
            tag=f'test_b{b}_s{ss}_{method}_{kind}';m=Field();m.load_state_dict(torch.load(OUT/f'{tag}.pt',weights_only=True))
            orders=[0] if kind=='direct' else [0,1,2]
            r8=predict(m,design(orders,8));r48=predict(m,design(orders,48))
            details.append(dict(tag=tag,relative_q8_q48=relative(r8,r48),max_abs_q8_q48=float(np.max(abs(r8-r48)))))
    tests['source_renderer_refinement_below_1e_minus4']=max(x['relative_q8_q48'] for x in details)<1e-4
    qtruth=[]
    for pseed in [1701,2701]:
      for kind in ['matched','single','double']:
        a=response(design([0,1,2],48),parameters(pseed),kind);b=response(design([0,1,2],96),parameters(pseed),kind)
        qtruth.append(dict(parameter_seed=pseed,kind=kind,max_abs=float(np.max(abs(a-b))),relative=relative(a,b)))
    tests['source_truth48vs96_below_1e_minus8']=max(x['relative'] for x in qtruth)<1e-8
    # Exact L1-innovation minimization identity, not a sampled GR theorem.
    z=np.r_[np.linspace(-5,5,1001),[-1.,0.,1.]];innovation=np.sign(z)*np.maximum(abs(z)-1,0);hub=np.where(abs(z)<=1,z*z,2*abs(z)-1)
    tests['eliminated_innovation_equals_Huber']=bool(np.max(abs((z-innovation)**2+2*abs(innovation)-hub))<1e-12)
    # Linear leading term in log coordinate is reproduced exactly by cubic splines.
    v=np.load(OUT/'forward_arrays.npz');tests['residual_cubic_equivalence']=bool(np.max(abs(v['holdout_cubic_log_None']-v['holdout_residual_cubic_None']))<1e-11)
    kernel=json.loads((OUT/'physical_reference_check.json').read_text());tests['independent_GR_time_gate']=kernel['gate_pass']
    tests['physical_response24vs48_below_1e_minus7']=max(fw['quadrature_24_vs48_perchannel'])<1e-7
    tests['all_neural_checkpoint_counts']=len(list(OUT.glob('*.pt')))==99
    # Metadata frozen before test, no in-place alteration.
    h=hashlib.sha256((OUT/'selected_lambdas.json').read_bytes()).hexdigest();tests['test_selection_hash_matches']=h==inv['selection_hash']
    old=ps['old_mask'];low=[]
    for b in [0,1]:
        t0=ps[f'truth_b{b}_matched'];t1=ps[f'truth_b{b}_double'];low.append(dict(background=b,half_distance_old_L2=float(np.linalg.norm((t1-t0)[old])/2),physical_interpretation='identical direct data means no single output is simultaneously closer than half this absolute distance to both truths'))
    save('verification002.json',dict(checks=tests,all_checks_pass=all(tests.values()),learned_field_quadrature=details,source_truth_quadrature=qtruth,twins=low,neural_models=99,production_suite_run=False,environment={'python':platform.python_version(),'torch':torch.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'dtype':'float64','CPU':True},scope='finite-pilot checks, no whole Kerr acquisition validation'))
    print(tests)
if __name__=='__main__':main()
