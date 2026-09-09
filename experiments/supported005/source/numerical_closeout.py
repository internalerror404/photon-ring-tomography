"""Postplanned source-metric numerical readback, NOT new estimator selection.
Original failed check is preserved. Reorthogonalize the same retained source span
using two fixed QR steps and extended-precision products. Compare spectra and
source-error energies, without rerunning any neural fit or changing thresholds.
Picard truth-to-noise comparison is an oracle diagnostic only, not an estimator.
"""
from experiment import *

def ldot(a,b):return np.asarray(np.asarray(a,np.longdouble)@np.asarray(b,np.longdouble),float)

def run_closeout():
    start=time.perf_counter();raw=json.loads((ROOT/'results/RESULTS.json').read_text())
    ar=np.load(ROOT/'results/ARRAYS.npz');old=np.load(PARENT/'results/NEURAL_ARRAYS.npz')
    coord=old['eval_coords'];N=len(coord);std=old['std'];rows=[];spectra=[];corr=[];datas={}
    for shape in CFG['source_dictionary']['nested_classes']:
        name='B'+str(np.prod(shape));Q=dictionary(coord,shape);X=np.asarray(ar[name+'_source_normalizer'],np.longdouble)
        # Explicit finite arithmetic correction; no basis enlargement, shrinkage,
        # source-metric change or tolerance increase.
        for _ in range(2):
            qv=np.asarray(np.asarray(Q,np.longdouble)@X,float)
            qq,rr=np.linalg.qr(qv/np.sqrt(N),mode='reduced')
            X=X@np.asarray(np.linalg.solve(rr,np.eye(len(rr))),np.longdouble)
        qo=np.asarray(np.asarray(Q,np.longdouble)@X,float)
        orth=float(np.max(abs(qo.T@qo/N-np.eye(qo.shape[1]))))
        B={q:np.asarray(np.asarray(ar[name+'_A'+str(q)],np.longdouble)@X,float)/std[:,None] for q in (10,16,24)}
        u,s,vt=svd(B[16],full_matrices=True);v=vt.T;spad=np.r_[s,np.zeros(qo.shape[1]-len(s))]
        old_s=ar[name+'_s'];relmax=float(np.max(abs(spad-old_s)/max(old_s[0],1e-15)))
        spectral={'basis':name,'retained_source_dimension':qo.shape[1],'reorthonormality':orth,
           'count_rho1':int(np.sum(.1*s>=1)),'count_rho5':int(np.sum(.1*s>=5)),
           'maximum_singular_change_scaled_by_largest':relmax,
           'extended_precision_eps':float(np.finfo(np.longdouble).eps),
           'q10_q16_source_normalized_operator_norm':float(svd(B[10]-B[16],compute_uv=False)[0])}
        for sc in ('background','events'):
            truth=old['truth_'+sc];ct=qo.T@(truth-1)/N;mc=v.T@ct
            signal=np.abs(mc[:len(s)])*s
            spectral[sc+'_true_coeffs_exceeding_own_noise_1']=int(np.sum(signal>=1))
            spectral[sc+'_true_coeffs_exceeding_own_noise_5']=int(np.sum(signal>=5))
            # More informative than counting nominal .10-RMS test directions.
            datas[name+'_'+sc+'_true_mode_coefficients']=mc
            datas[name+'_'+sc+'_coefficient_standard_errors']=1/s
            for me in ('data_only','robust_pinn'):
              for seed in (11,22,33):
                key=f'{sc}_{me}_q8_s{seed}';pred=old['prediction_'+key]
                for th in (1,5):
                    di,_,_=decomposition(pred-truth,qo,v,spad,th)
                    rows.append({'basis':name,'scenario':sc,'method':me,'seed':seed,'threshold':th,**di})
        spectra.append(spectral);datas[name+'_s']=spad;datas[name+'_source_normalizer']=X;datas[name+'_V']=v
        print('REORTH',name,orth,relmax,flush=True)
    out={'scope':__doc__,'spectra':spectra,'decompositions':rows,
      'checks':{'same_span_source_metric_reorthonormalized':all(r['reorthonormality']<=1e-8 for r in spectra),
                'operational_counts_unchanged':all(r['count_rho1']==next(b for b in raw['bases'] if b['name']==r['basis'])['operational_counts']['1'] and r['count_rho5']==next(b for b in raw['bases'] if b['name']==r['basis'])['operational_counts']['5'] for r in spectra),
                'original_failed_records_retained':True},
      'source_value_noise_test':'Truth coefficients examined only to explain noise amplification; NEVER used to select estimator modes.',
      'seconds':time.perf_counter()-start,'new_rays':0,'new_fits':0}
    dump('results/NUMERICAL_CLOSEOUT.json',out);np.savez_compressed(ROOT/'results/NUMERICAL_CLOSEOUT_ARRAYS.npz',**datas)
if __name__=='__main__':run_closeout()
