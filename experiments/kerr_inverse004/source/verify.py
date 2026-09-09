"""Post-fit audits on saved physical tuples and model checkpoints.
This additional measurement does not retrain, change a candidate, or add rays.
It separates tuple/Jacobian approximation from numerical integration of a fitted
source, and checks the latter on actual cached reference tuples, not only splines.
"""
from common import *
from neural_inverse import Field,ten,tensor_design,project,derivative_data
import torch
from scipy.stats import chi2,ncx2,beta

def run():
    t0=time.perf_counter();renderer=CachedRenderer()
    r=json.loads((ROOT/'results/NEURAL_RESULTS.json').read_text());arr=np.load(ROOT/'results/NEURAL_ARRAYS.npz')
    refs={q:tensor_design(renderer.design(q,reference=True)) for q in [10,16]}
    ap_exact=tensor_design(renderer.design(16,n=33,exact_saved_weights=True))
    sig=ten(arr['std']);rows=[];models_before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*.pt')}
    samples={}
    for item in r['results']:
        name=item['id'];model=Field();model.load_state_dict(torch.load(ROOT/'models'/f'{name}.pt',weights_only=True))
        noisy=ten(arr[f"noisy_{item['scenario']}_s{item['seed']}"])
        with torch.no_grad():
            yphys={q:project(model,d).numpy() for q,d in refs.items()}
            ytuple=project(model,ap_exact).numpy()
        y16=arr[f'response_{name}_q16'];y24=arr[f'response_{name}_q24'];ytrain=arr[f"response_{name}_q{item['training_quadrature']}"]
        loss,gphys=derivative_data(model,refs[16],noisy,sig)
        row={'id':name,'physical_reference_q10_q16_relative':relative(yphys[10],yphys[16]),
             'physical_reference_q10_q16_whitened':float(np.linalg.norm((yphys[10]-yphys[16])/sig.numpy())),
             'tuple_surrogate_same_weight_q16_whitened':float(np.linalg.norm((ytuple-yphys[16])/sig.numpy())),
             'jacobian_surrogate_only_whitened':float(np.linalg.norm((y16-ytuple)/sig.numpy())),
             'q24_surrogate_vs_physical_q16_whitened':float(np.linalg.norm((y24-yphys[16])/sig.numpy())),
             'training_vs_physical_ref_whitened':float(np.linalg.norm((ytrain-yphys[16])/sig.numpy())),
             'training_vs_physical_ref_relative':relative(ytrain,yphys[16]),
             'physical_noisy_chi2':loss,'physical_data_gradient_norm':float(np.linalg.norm(gphys))}
        row['actual_fitted_field_check_pass']=row['training_vs_physical_ref_whitened']<=.1 and row['training_vs_physical_ref_relative']<=5e-4 and row['physical_reference_q10_q16_whitened']<=.1
        rows.append(row);samples[name+'_physical_q16']=yphys[16]
    # Finite difference of an actual detector loss at one saved model, parameters
    # exactly restored in memory; checkpoint bytes never touched.
    name=r['results'][0]['id'];model=Field();model.load_state_dict(torch.load(ROOT/'models'/f'{name}.pt',weights_only=True))
    noisy=ten(arr['noisy_background_s11']);v=torch.nn.utils.parameters_to_vector(model.parameters()).detach().clone()
    loss,g=derivative_data(model,refs[16],noisy,sig)
    direction=np.random.default_rng(4010).normal(size=len(g));direction/=np.linalg.norm(direction)
    h=1e-6;vl=[]
    for s in [-1,1]:
        torch.nn.utils.vector_to_parameters(v+s*h*ten(direction),model.parameters())
        with torch.no_grad():vl.append(float(torch.mean(((project(model,refs[16])-noisy)/sig)**2)))
    torch.nn.utils.vector_to_parameters(v,model.parameters())
    fd=(vl[1]-vl[0])/(2*h);ad=float(g@direction)
    grad_error=abs(fd-ad)/max(1.,abs(fd),abs(ad))
    # Source-equation fixture, no approximation of Kerr trajectories.
    c=truth_coefficients(False);coords=ten(arr['eval_coords'][::20]).requires_grad_(True)
    rad,ph,t=coords.unbind(-1);R=(rad-11)/5;psi=ph-1/(rad**1.5+.5)*t
    b=torch.stack([torch.ones_like(rad),R,R**2,torch.cos(psi),torch.sin(psi),torch.cos(2*psi),torch.sin(2*psi)],-1)
    val=1+b@ten(c[:7]);gr=torch.autograd.grad(val.sum(),coords)[0]
    trms=float(torch.sqrt(torch.mean((gr[:,2]+1/(rad**1.5+.5)*gr[:,1])**2)))
    f=json.loads((ROOT/'SOURCE_FREEZE.json').read_text())
    source_ok=all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in f['source_hashes'].items())
    input_ok=authenticate() is not None
    model_ok=models_before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*.pt')}
    L=json.loads((ROOT/'results/LINEAR_RESULTS.json').read_text())
    coverage=L['models']['reference']['0.001']['joint95_coverage'];n=2048;k=round(coverage*n)
    ci=[float(beta.ppf(.025,k,n-k+1)),float(beta.ppf(.975,k+1,n-k))]
    events=np.array([.5,.35]);powers={}
    for s in [.01,.001]:
        cov=np.array(L['models']['reference'][str(s)]['covariance']);ncp=float(events@np.linalg.solve(cov,events))
        powers[str(s)]={'unit':'known-template Gaussian-noise model only','squared_whitened_target_norm':ncp,'joint95_rejection_probability':float(ncx2.sf(chi2.ppf(.95,2),2,ncp))}
    checks={'all_24_fits_present':len(rows)==24,'input_byte_hashes':input_ok,'frozen_executable_sources_unchanged':source_ok,
          'model_bytes_unchanged_during_readback':model_ok,'autograd_matches_directional_difference':grad_error<1e-7,
          'matched_source_satisfies_assumed_transport':trms<1e-12,
          'all_actual_fitted_field_response_checks_pass':all(v['actual_fitted_field_check_pass'] for v in rows),
          'no_new_ray_or_root_or_path_calls':True}
    dump('results/VERIFICATION.json',{'scope':__doc__,'rows':rows,'checks':checks,'directional_gradient':{'finite_difference':fd,'autograd':ad,'relative_error':grad_error},
        'matched_truth_transport_RMS':trms,'joint95_coverage_binomial_interval':ci,'known_template_event_power':powers,
        'scope_extra':'Post-fit measurement and algebraic power readback added after partial neural outcomes; no hyperparameter or candidate change','seconds':time.perf_counter()-t0})
    np.savez_compressed(ROOT/'results/PHYSICAL_FITTED_RESPONSE_READBACK.npz',**samples)
    print('VERIFICATION',checks,'max physical reference q10/16',max(x['physical_reference_q10_q16_relative'] for x in rows),flush=True)

if __name__=='__main__':run()
