"""New mode/readback experiment using immutable inverse004 inputs.
No Kerr equation is solved and no network is trained. The source norm and
basis are explicitly finite, and numerical near-null is not continuum-null.
"""
from __future__ import annotations
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
from pathlib import Path
import sys,time,json,hashlib,platform
import numpy as np
import pandas as pd
import scipy
from scipy.interpolate import BSpline
from scipy.special import eval_legendre
from scipy.linalg import svd
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'inputs/parent004'
sys.path.insert(0,str(PARENT/'source'))
import common as prior
from neural_inverse import Field,ten,tensor_design,project
import torch
torch.set_num_threads(1)
CFG=json.loads((ROOT/'protocol.json').read_text())


def dump(path,obj):
    def conv(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    (ROOT/path).write_text(json.dumps(obj,indent=2,allow_nan=False,default=conv)+'\n')

def knots(lo,hi,n):
    return np.r_[np.full(4,lo),np.linspace(lo,hi,n-2)[1:-1],np.full(4,hi)]

def dictionary(coords,shape):
    c=np.asarray(coords);p=c.reshape(-1,3);nr,nt,np_=shape
    lim=CFG['source_dictionary']['domain']
    if not np.isfinite(p).all():raise ValueError('Nonfinite source coordinate')
    for i,k in enumerate(('r','phi','tbar')):
        if np.any(p[:,i]<lim[k][0]-1e-10) or np.any(p[:,i]>lim[k][1]+1e-10):raise ValueError('Source outside declared basis support: '+k)
    r=BSpline.design_matrix(p[:,0],knots(*lim['r'],nr),3,extrapolate=False).toarray()
    t=BSpline.design_matrix(p[:,2],knots(*lim['tbar'],nt),3,extrapolate=False).toarray()
    z=2*(p[:,1]-lim['phi'][0])/(lim['phi'][1]-lim['phi'][0])-1
    az=np.stack([eval_legendre(k,z) for k in range(np_)],axis=1)
    return np.einsum('ni,nj,nk->nijk',r,t,az).reshape(*c.shape[:-1],nr*nt*np_)

def integrated_matrix(d,shape):
    vals=dictionary(d['coords'],shape)
    return np.einsum('tpqk,pq->tpk',vals,d['kernel']).reshape(128,-1)

def normalize(Q):
    u,s,vt=svd(Q/np.sqrt(len(Q)),full_matrices=False,check_finite=True)
    keep=s>s[0]*1e-9;X=vt[keep].T/s[keep]
    return Q@X,X,s,keep

def rms(x):return float(np.linalg.norm(x)/np.sqrt(len(x)))

def decomposition(error,Qorth,V,s,threshold):
    c=(Qorth.T@error)/len(error);m=V.T@c
    k=int(np.sum(.1*s>=threshold));supported=float(m[:k]@m[:k]);remaining=float(m[k:]@m[k:])
    outside=error-Qorth@c;outside2=float(outside@outside/len(error));total=float(error@error/len(error))
    return {'count':k,'total_RMS':np.sqrt(total),'supported_RMS':np.sqrt(supported),'weak_RMS':np.sqrt(remaining),
            'outside_RMS':np.sqrt(outside2),'supported_squared_fraction':supported/max(total,1e-300),
            'weak_squared_fraction':remaining/max(total,1e-300),'outside_squared_fraction':outside2/max(total,1e-300),
            'energy_partition_relative_residual':abs(total-supported-remaining-outside2)/max(total,1e-300)},c,m

def run():
    if (ROOT/'results/RESULTS.json').exists():raise RuntimeError('Refuse output overwrite')
    t0=time.perf_counter();prior.authenticate();newin=json.loads((ROOT/'INPUT_MANIFEST.json').read_text())
    for d in newin['files']:
        if hashlib.sha256((ROOT/d['path']).read_bytes()).hexdigest()!=d['sha256']:raise RuntimeError('Input changed: '+d['path'])
    frozen=json.loads((ROOT/'SOURCE_FREEZE.json').read_text())
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=frozen['source_sha256']:raise RuntimeError('Unregistered executable')
    rnd=prior.CachedRenderer();basearrays=np.load(PARENT/'results/NEURAL_ARRAYS.npz')
    modelresp=np.load(PARENT/'results/PHYSICAL_FITTED_RESPONSE_READBACK.npz')
    lin=np.load(PARENT/'results/LINEAR_ARRAYS.npz')
    coords=basearrays['eval_coords'];N=len(coords);sig=basearrays['std'];ds={q:rnd.design(q,reference=True) for q in (10,16)}
    ds[24]=rnd.design(24,n=33)
    base={q:np.tile(d['kernel'].sum(1),8) for q,d in ds.items()}
    dims=[];splines={};arrays={};decomprows=[];corrows=[];profiling=[];witnesses=[];checks={}
    net16={};net10={};net24={}
    for scenario in ('background','events'):
      for method in ('data_only','robust_pinn'):
       for seed in (11,22,33):
        key=f'{scenario}_{method}_q8_s{seed}'
        mod=Field();mod.load_state_dict(torch.load(PARENT/'models'/f'{key}.pt',weights_only=True))
        net16[key]=modelresp[key+'_physical_q16']
        with torch.no_grad():
            net10[key]=project(mod,tensor_design(ds[10])).numpy();net24[key]=project(mod,tensor_design(ds[24])).numpy()
    for shape in CFG['source_dictionary']['nested_classes']:
        if time.perf_counter()-t0>900:raise RuntimeError('Compute envelope reached')
        name='B'+str(np.prod(shape));Q=dictionary(coords,shape);Qorth,X,metric_s,keep=normalize(Q)
        d=X.shape[1];Ad={q:integrated_matrix(des,shape) for q,des in ds.items()}
        Bd={q:(Ad[q]@X)/sig[:,None] for q in ds}
        U,s,Vt=svd(Bd[16],full_matrices=True);V=Vt.T
        spad=np.r_[s,np.zeros(d-len(s))];rr=int(np.sum(s>s[0]*1e-10));modeQ=Qorth@V
        opdiff=svd(Bd[16]-Bd[10],compute_uv=False)[0]
        opdiff24=svd(Bd[16]-Bd[24],compute_uv=False)[0]
        orth=float(np.max(abs(Qorth.T@Qorth/N-np.eye(d))))
        summary={'name':name,'factors':shape,'nominal_dimension':int(np.prod(shape)), 'source_metric_retained_rank':d,
          'metric_singular_values':metric_s,'metric_condition_retained':float(metric_s[0]/metric_s[keep][-1]),
          'source_orthonormality_max_abs':orth,'numerical_measurement_rank':rr,'spectrum':spad,
          'source_amplitude_RMS':.1,'operational_counts':{str(th):int(np.sum(.1*s>=th)) for th in (1,5)},
          'q10_q16_operator_norm_whitened_source_normalized':float(opdiff),'q24_q16_operator_difference':float(opdiff24),
          'same_rule_source_linear':True}
        dims.append(summary);splines[name]=(Q,Qorth,X,V,U,spad,Ad,Bd)
        arrays[name+'_source_normalizer']=X;arrays[name+'_V']=V;arrays[name+'_U']=U;arrays[name+'_s']=spad
        arrays[name+'_A16']=Ad[16];arrays[name+'_A10']=Ad[10];arrays[name+'_A24']=Ad[24]
        arrays[name+'_source_metric_singular_values']=metric_s
        checks[name+'/orthonormality']=orth<=1e-8
        for scenario in ('background','events'):
            truth=basearrays['truth_'+scenario];c=(Qorth.T@(truth-1))/N
            truth_out=truth-1-Qorth@c
            outresp=(basearrays['clean_'+scenario]-base[16]-Ad[16]@X@c)/sig
            summary[scenario+'_representation_error']=rms(truth_out)/rms(truth-1)
            summary[scenario+'_projection_remainder_detector_norm']=float(np.linalg.norm(outresp))
            for method in ('data_only','robust_pinn'):
              for seed in (11,22,33):
                key=f'{scenario}_{method}_q8_s{seed}';pred=basearrays['prediction_'+key];obs=basearrays[f'noisy_{scenario}_s{seed}']
                residual=(obs-net16[key])/sig
                for threshold in (1,5):
                    decomp,cpre,mpre=decomposition(pred-truth,Qorth,V,spad,threshold)
                    decomprows.append(dict(basis=name,scenario=scenario,method=method,seed=seed,threshold=threshold,**decomp))
                    k=decomp['count'];proj=U[:,:k].T@residual
                    delta=V[:,:k]@(proj/s[:k]);correction=Qorth@delta
                    post=pred+correction
                    responses={q: {16:net16,10:net10,24:net24}[q][key]+Ad[q]@X@delta for q in ds}
                    ypost=responses[16];rpost=(obs-ypost)/sig
                    # Independent spectral estimate without a neural completion.
                    cts=V[:,:k]@((U[:,:k].T@((obs-base[16])/sig))/s[:k])
                    pure=1+Qorth@cts
                    truncpre=1+modeQ[:,:k]@((modeQ[:,:k].T@(pred-1))/N)
                    row={'basis':name,'scenario':scenario,'method':method,'seed':seed,'threshold':threshold,'modes':k,
                         'raw_source_relative':rms(pred-truth)/rms(truth-1),'corrected_source_relative':rms(post-truth)/rms(truth-1),
                         'pure_spectral_source_relative':rms(pure-truth)/rms(truth-1),'neural_supported_only_source_relative':rms(truncpre-truth)/rms(truth-1),
                         'source_correction_RMS':rms(correction),'source_noise_RMS_if_model_exact':float(np.sqrt(np.sum(1/s[:k]**2))),
                         'raw_whitened_residual':float(np.linalg.norm(residual)),'corrected_whitened_residual':float(np.linalg.norm(rpost)),
                         'residual_projection_after':float(np.linalg.norm(U[:,:k].T@rpost)),
                         'expected_residual_decrease_squared':float(proj@proj),
                         'observed_decrease_squared':float(residual@residual-rpost@rpost),
                         'q10_q16_corrected_whitened':float(np.linalg.norm((responses[10]-responses[16])/sig)),
                         'q24_q16_corrected_whitened':float(np.linalg.norm((responses[24]-responses[16])/sig)),
                         'q10_q16_corrected_relative':prior.relative(responses[10],responses[16]),
                         'q24_q16_corrected_relative':prior.relative(responses[24],responses[16]),
                         'minimum_evaluated_emissivity':float(post.min())}
                    corrows.append(row)
                    if name=='B135':
                        arrays[f'correction_{key}_rho{threshold}']=post;arrays[f'pure_spectral_{scenario}_s{seed}_rho{threshold}']=pure
                        arrays[f'corrected_response_{key}_rho{threshold}']=ypost
                # No source fit or correction selection based on the unknown truth.
        # Event-template nuisance stress: full original seven nuisance functions
        # plus all new source-dictionary columns; source-normalize jointly.
        NQ=np.column_stack([prior.basis(coords)[...,:7],Q])
        nQ,nX,ns,nkeep=normalize(NQ)
        NA=np.column_stack([lin['A_reference'][:,:7],Ad[16]])
        NB=(NA@nX)/sig[:,None];nu,nss,nvt=svd(NB,full_matrices=False)
        target=lin['A_reference'][:,7:]/sig[:,None]
        for tol in (1e-8,1e-10,1e-12):
            rank=int(np.sum(nss>nss[0]*tol));E=target-nu[:,:rank]@(nu[:,:rank].T@target)
            st=svd(E,compute_uv=False)
            profiling.append({'nuisance':name+'+original7','basis':name,'nominal_nuisance_columns':NQ.shape[1],
              'metric_rank':nX.shape[1],'response_rank_tolerance':tol,'response_nuisance_rank':rank,
              'target_singular_values':st,'target_spectrum_scope':'unit-peak amplitudes; source-normalized nuisance only',
              'raw_projected_target_norm':float(np.linalg.norm(E))})
        print(name,'rank',rr,'ops',summary['operational_counts'],'orth',orth,'qdiff',opdiff,flush=True)
    # Recover original known-target result with only the original7 unknowns.
    B0=lin['A_reference']/sig[:,None];u0,s0,_=svd(B0[:,:7],full_matrices=False)
    E0=B0[:,7:]-u0@(u0.T@B0[:,7:]);st0=svd(E0,compute_uv=False)
    # Explicit witness from the largest source space; project fixed smooth trial
    # onto numerical null. This is an existence diagnostic, not a learned source.
    name='B315';Q,Qorth,X,V,U,spad,Ad,Bd=splines[name];rank=int(np.sum(spad>spad[0]*1e-10))
    vn=V[:,rank:];tr=np.sin((coords[:,0]-6.5)*np.pi/10.5)*np.sin((coords[:,2]+7)*2*np.pi/33)
    cc=Qorth.T@tr/N;cn=vn@(vn.T@cc)
    if np.linalg.norm(cn)<1e-10:cn=vn[:,0]
    cn=cn/np.linalg.norm(cn);field=Qorth@cn
    coeff=X@cn
    samplemax=float(np.max(abs(field)));mins=[]
    for q,dsg in ds.items():samplemax=max(samplemax,float(np.max(abs(dictionary(dsg['coords'],[7,15,3])@coeff))))
    amp=min(.10,.5/samplemax)
    diffs={q:2*amp*Ad[q]@coeff for q in ds}
    witness={'source_basis':'B315','metric':'same chart-pullback RMS','numerical_null_dimension':int(vn.shape[1]),
      'one_sided_source_RMS':amp,'two_histories_RMS_separation':2*amp,'sample_max_abs_normalized_mode':samplemax,
      'minimum_emissivity_on_declared_checked_points':1-amp*samplemax,
      'exact_reference16_whitened_difference':float(np.linalg.norm(diffs[16]/sig)),
      'physical_reference10_whitened_difference':float(np.linalg.norm(diffs[10]/sig)),
      'frozen_reference24_whitened_difference':float(np.linalg.norm(diffs[24]/sig)),
      'scope':'Numerically near-null for declared finite measurements; positivity only on checked sets, no uniform continuum proof.'}
    arrays['witness_mode']=field;arrays['witness_coeff']=coeff;arrays['witness_plus']=1+amp*field;arrays['witness_minus']=1-amp*field
    # Record local data-compatible multiplicity among actual neural completions.
    pairrows=[]
    for sc in ('background','events'):
      for method in ('data_only','robust_pinn'):
        for a,b in ((11,22),(11,33),(22,33)):
            f=basearrays[f'prediction_{sc}_{method}_q8_s{a}']-basearrays[f'prediction_{sc}_{method}_q8_s{b}']
            _,qo,_,v,_,ss,_,_=splines['B135']
            dc,_,_=decomposition(f,qo,v,ss,5)
            pairrows.append({'scenario':sc,'method':method,'seeds':[a,b],**dc})
    checks['all_decompositions_partition_error']=max(x['energy_partition_relative_residual'] for x in decomprows)<1e-8
    checks['projection_residual_removal']=max(x['residual_projection_after'] for x in corrows)<1e-7
    checks['linear_data_loss_reduction_identity']=max(abs(x['observed_decrease_squared']-x['expected_residual_decrease_squared']) for x in corrows)<1e-7
    checks['reference_earlier_target_spectrum_reproduced']=np.max(abs(st0-[49.94718386791838,41.65077101634471]))<1e-6
    checks['witness_tested_positivity']=witness['minimum_emissivity_on_declared_checked_points']>=.5-1e-10
    checks['witness_reference_near_null']=witness['exact_reference16_whitened_difference']<1e-5
    # Failed numerical response tests are findings, not retrospectively waived.
    checks['all_corrected_fields_numerical_whitened_criterion']=all(max(x['q10_q16_corrected_whitened'],x['q24_q16_corrected_whitened'])<=.1 for x in corrows)
    checks['all_corrected_fields_numerical_relative_criterion']=all(max(x['q10_q16_corrected_relative'],x['q24_q16_corrected_relative'])<=5e-4 for x in corrows)
    arrays['eval_coords']=coords;arrays['truth_background']=basearrays['truth_background'];arrays['truth_events']=basearrays['truth_events']
    out={'scope':CFG['scope'],'bases':dims,'decompositions':decomprows,'corrections':corrows,'nuisance_stress':profiling,
         'original7_target_singular_values':st0,'ambiguity_witness':witness,'neural_seed_differences':pairrows,'checks':checks,
         'all_checks_pass':all(checks.values()),'seconds':time.perf_counter()-t0,
         'new_physical_calls':0,'new_neural_fits':0,'actual_network_checkpoint_readbacks':12,
         'source_freedom_changed':True,'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__,'threads':1}}
    dump('results/RESULTS.json',out)
    np.savez_compressed(ROOT/'results/ARRAYS.npz',**arrays)
    pd.DataFrame(decomprows).to_csv(ROOT/'results/DECOMPOSITIONS.csv',index=False)
    pd.DataFrame(corrows).to_csv(ROOT/'results/CORRECTIONS.csv',index=False)
    pd.DataFrame(profiling).to_csv(ROOT/'results/NUISANCE_STRESS.csv',index=False)
    print('CHECKS',checks,'SECONDS',out['seconds'],'WITNESS',witness,flush=True)

if __name__=='__main__':run()
