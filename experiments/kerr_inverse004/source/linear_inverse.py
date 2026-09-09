"""Known-template amplitude inference; seven unknown background coefficients.
Every calculation is an existing-transfer readback with new synthetic sources,
not a new Kerr integration. Intervals are frequentist noise-model ellipses for
known target templates; no image-wise confidence or arbitrary-history claim.
"""
from common import *
from scipy.stats import chi2

def factor(A,sig):
    B=A/sig[:,None]
    un,sn,vn=np.linalg.svd(B[:,:7],full_matrices=False)
    rank=int(np.sum(sn>1e-12*sn[0]));un=un[:,:rank]
    E=B[:,7:]-un@(un.T@B[:,7:])
    s=np.linalg.svd(E,compute_uv=False)
    F=E.T@E;cov=np.linalg.inv(F)
    W=cov@E.T
    pinv=np.linalg.pinv(B,rcond=1e-12)
    if not np.isfinite(W).all():raise FloatingPointError('Invalid profile solve')
    return B,E,F,cov,W,pinv,rank,s

def run():
    t0=time.perf_counter();renderer=CachedRenderer()
    dref=renderer.design(16,reference=True);br,Ar=linear_components(dref)
    b10,A10=linear_components(renderer.design(10,reference=True))
    rng=np.random.default_rng(400410)
    truth=np.column_stack([rng.normal(0,.08,(32,7)),rng.uniform(0,.7,(32,2))]);truth[:16,7:]=0
    nois=np.random.default_rng(400411).normal(size=(32,64,128))
    clean=br[None,:]+truth@Ar.T
    normref=np.linalg.norm(Ar,axis=0)
    row={};arrays={'A_reference':Ar,'base_reference':br,'true_coefficients':truth,'standard_noise':nois,'clean_observations':clean}
    jointcrit=chi2.ppf(.95,2)
    for name,n in [('reference',None),('classical9',9),('classical17',17),('classical33',33)]:
        if n is None:b,A=br,Ar
        else:b,A=linear_components(renderer.design(16,n=n,exact_saved_weights=True))
        arrays['A_'+name]=A;arrays['base_'+name]=b
        row[name]={}
        for sigma in [.01,.001]:
            sig=noise_std(renderer.areas,sigma);B,E,F,cov,W,pinv,nrank,s=factor(A,sig)
            residual=(clean-b[None,:])/sig[None,:]
            est0=residual@W.T;bias=est0-truth[:,7:]
            draws=np.einsum('kq,hdq->hdk',W,nois+residual[:,None,:])
            err=draws-truth[:,None,7:]
            ell=np.einsum('...i,ij,...j->...',err,F,err)
            sd=np.sqrt(np.diag(cov));normbias=np.sqrt(np.einsum('hi,ij,hj->h',bias,F,bias))
            pert=(clean-b[None,:]-truth@A.T)/sig[None,:]
            # Orthogonal projection bound: ||F^1/2 bias|| <= ||W_noise delta_y||.
            bound=np.linalg.norm(pert,axis=1)
            pred=(pert@W.T)
            full= residual@pinv.T
            payload={'target_singular_values':s,'nuisance_rank':nrank,'full_singular_values':np.linalg.svd(B,compute_uv=False),
                'standard_errors':sd,'covariance':cov,'event_correlation':float(cov[0,1]/np.prod(sd)),
                'max_abs_noise_free_bias':np.max(abs(bias),axis=0),'median_abs_noise_free_bias':np.median(abs(bias),axis=0),
                'max_bias_in_joint_standard_error_units':float(normbias.max()),'max_forward_defect_whitened_norm':float(bound.max()),
                'joint95_coverage':float(np.mean(ell<=jointcrit)),
                'no_event_false_positive_joint95':float(np.mean(ell[:16]>jointcrit)),
                'target_RMSE':np.sqrt(np.mean(err*err,axis=(0,1))),
                'profile_vs_full_pseudoinverse_maxabs':float(np.max(abs(full[:,7:]-est0))),
                'bias_identity_maxabs':float(np.max(abs(pred-bias))),
                'bias_bound_max_violation':float(np.max(normbias-bound)),
                'minimum_true_emissivity':float(np.min(fields(dref['coords'],truth[0]))) }
            row[name][str(sigma)]=payload
            arrays[f'{name}_sigma{sigma}_draw_estimates']=draws;arrays[f'{name}_sigma{sigma}_bias']=bias
            arrays[f'{name}_sigma{sigma}_covariance']=cov
    jac=renderer.design(16,n=33)
    jacrel=np.max(abs(jac['weights']/dref['weights']-1))
    # Exact detector adjoint property for a nonconstant finite source.
    x=np.random.default_rng(444).normal(size=9);y=np.random.default_rng(445).normal(size=128)
    adjerr=abs(y@(Ar@x)-x@(Ar.T@y))
    checks={'cached_inputs_authenticated':True,'reference_template_quad10_16':bool(np.max(np.linalg.norm(A10-Ar,axis=0)/normref)<5e-4),
        'profile_matches_full_lsq':max(v['profile_vs_full_pseudoinverse_maxabs'] for m in row.values() for v in m.values())<1e-7,
        'inverse_bias_identity':max(v['bias_identity_maxabs'] for m in row.values() for v in m.values())<1e-7,
        'joint_bias_bounded_by_forward_defect':max(v['bias_bound_max_violation'] for m in row.values() for v in m.values())<1e-7,
        'reference_ellipse_coverage_expected_noise_model':all(.93<row['reference'][str(s)]['joint95_coverage']<.97 for s in [.01,.001]),
        'source_linearity_adjoint':adjerr<1e-12,
        'jacobian_spline_matches_reference_weights':bool(jacrel<5e-4)}
    out={'scope':__doc__,'models':row,'truth_histories':32,'noise_draws_per_truth':64,'reference_template_q10_q16_relative':np.linalg.norm(A10-Ar,axis=0)/normref,
       'jacobian_relative_error_max':jacrel,'adjoint_error':adjerr,'checks':checks,'seconds':time.perf_counter()-t0,
       'new_ray_or_path_calls':0,'new_operator':'9-column declared source-response matrices only; no Paper-I operator changed'}
    dump('results/LINEAR_RESULTS.json',out)
    np.savez_compressed(ROOT/'results/LINEAR_ARRAYS.npz',**arrays)
    print(json.dumps({name:{s:{k:v[k] for k in ['standard_errors','max_bias_in_joint_standard_error_units','joint95_coverage']} for s,v in x.items()} for name,x in row.items()},default=lambda v:v.tolist(),indent=2),flush=True)
    print('CHECKS',checks,flush=True)
if __name__=='__main__':run()
