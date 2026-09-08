"""Post-fit independent arithmetic, renderer-resolution and payload checks."""
from common import *
from inverse import SourceField,observation_design
import scipy,sys

def run():
    rows=[]
    for seed in CFG['seeds']:
      for kind in ('data','pinn','characteristic'):
        for tag,orders in [('direct',[0]),('all_matched',[0,1,2]),('all_transient',[0,1,2])]:
            m=SourceField(kind);m.load_state_dict(torch.load(ROOT/f'inverse_s{seed}_{kind}_{tag}.pt',weights_only=True))
            responses=[]
            with torch.no_grad():
              for q in [8,24,48]:
                d=observation_design(orders,q);responses.append((m(tensor(d[0]))*tensor(d[1])).sum(1).numpy())
            rows.append(dict(seed=seed,model=kind,fit=tag,relative_q8_q48=relative(responses[0],responses[2]),
                      relative_q24_q48=relative(responses[1],responses[2]),max_abs_q8_q48=float(np.max(abs(responses[0]-responses[2])))))
    inv=json.loads((ROOT/'inverse_results.json').read_text());forward=json.loads((ROOT/'forward_results.json').read_text());op=json.loads((ROOT/'operator_results.json').read_text())
    # Determine actual fit count; the direct fit has two separate truth evaluations.
    fitcount=sum(1 for p in ROOT.glob('*.pt'))
    checks={'inverse_models_saved':len(list(ROOT.glob('inverse_*.pt')))==27,
            'forward_models_saved':len(list(ROOT.glob('forward_*.pt')))==9,
            'operator_models_saved':len(list(ROOT.glob('operator_*.pt')))==6,
            'all_fit_results_finite':all(np.isfinite(r['old_contrast_relative_error']) for r in inv['results']),
            'analytic_truth_quad48_96_max_abs_below_2e-10':max(v['max_abs_48_96'] for v in inv['reference_checks'].values())<2e-10,
            'direct_twin_data_exactly_equal':inv['nullspace_twin']['direct_twin_max_abs']==0.,
            'independent_operator_input_grid_count':np.load(ROOT/'operator_arrays.npz')['truth'].shape==(96,37,127)}
    if not all(checks.values()):raise AssertionError(checks)
    dump('verification.json',dict(checks=checks,trained_neural_models=fitcount,fit_renderer_resolution=rows,
          worst_relative_q8_q48=max(x['relative_q8_q48'] for x in rows),
          worst_relative_q24_q48=max(x['relative_q24_q48'] for x in rows),
          environment={'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'scipy':scipy.__version__,
           'cuda_used':False,'float':'float64','torch_threads':torch.get_num_threads()},
          full_production_suite_executed=False,production_rays=0,
          runtime_seconds_sum_of_training_fits=sum(r['seconds'] for r in inv['results'] if not(r['acquisition']=='direct' and r['source']=='transient'))+sum(r['seconds'] for r in forward['results'])+sum(r['seconds'] for r in op['results'])))
    print(fitcount,'models checked; maximum learned-renderer q8 vs q48',max(x['relative_q8_q48'] for x in rows))
if __name__=='__main__':run()
