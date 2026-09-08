"""Readback diagnostics planned in protocol. Known-shape fit is an explicit oracle.
No new photon integrations. This is not the free-form neural reconstruction.
"""
from inverse003 import *
from scipy.linalg import svd

def template_diagnostic():
    c=np.load(D/'camera_q64.npz');coords=c['coords'];r,phi,t=coords[...,0],coords[...,1],coords[...,2]
    s=phi-r**(-1.5)*t;rr=(r-6)/6
    profiles=[1-.25*rr,.75+.25*rr,np.ones_like(rr)]
    fs=[]
    for k in range(1,4):
        fs += [profiles[k-1]*np.cos(k*s),profiles[k-1]*np.sin(k*s)]
    fs += [src(r,phi,t,'event1')-src(r,phi,t,'matched'),src(r,phi,t,'event2')-src(r,phi,t,'event1')]
    F=np.stack(fs,-1); A=np.einsum('nq,nqd->nd',c['weights'],F)
    obs,sigma=noise_parameters();ybase=obs['baseline'];out=[]
    true_background=np.array([.18*np.cos(.3),-.18*np.sin(.3),.13*np.sin(-.4),.13*np.cos(-.4),.07*np.cos(.8),-.07*np.sin(.8)])
    model_check=[]
    for srcname,amps in [('matched',[0,0]),('event1',[1,0]),('event2',[1,1])]:
        pred=ybase+A@np.r_[true_background,amps];model_check.append(float(np.max(abs(pred-obs['y_'+srcname]))))
    for S in [100,1000]:
        sd=sigma*1000/S
        for acq in ['direct','direct_plus_first','all']:
            sel=c['orders']<({'direct':1,'direct_plus_first':2,'all':3}[acq]); B=A[sel]/sd[sel,None]
            N=B[:,:6];T=B[:,6:];un,sn,vn=svd(N,full_matrices=False);nr=int(np.sum(sn>sn.max()*1e-11))
            Tcond=T-un[:,:nr]@(un[:,:nr].T@T);Fcond=Tcond.T@Tcond
            svals=np.linalg.svd(Tcond,compute_uv=False);rank=int(np.sum(svals>max(1e-10,svals.max()*1e-10)))
            cov=np.linalg.pinv(Fcond,rcond=1e-12)
            # A zero diagonal in a pseudoinverse is NOT a zero standard error of an unobserved mode.
            identifiable=np.linalg.norm(Tcond,axis=0)>1e-9
            std=[float(np.sqrt(cov[i,i])) if identifiable[i] else None for i in range(2)]
            fits=[]
            for seed in [11,22,33]:
                z=np.random.default_rng(seed).normal(size=len(sd))
                y=(obs['y_event2'][sel]-ybase[sel])/sd[sel]+z[sel]
                coeff=np.linalg.lstsq(B,y,rcond=1e-11)[0]
                fits.append(dict(seed=seed,event_coefficients=coeff[-2:].tolist(),whitened_chi2=float(np.mean((B@coeff-y)**2))))
            out.append(dict(SNR=S,acquisition=acq,nuisance_rank=nr,conditional_target_rank=rank,
                conditional_singular_values=svals.tolist(),template_amplitude_standard_errors=std,fits=fits))
    result=dict(scope='Shapes and orbital law known; two event amplitudes unknown plus six background nuisance coefficients. Dimensionless amplitudes multiply fixed peak-0.5 templates. Not image/movie recovery.',rows=out,exact_source_dictionary_max_abs_error=max(model_check))
    (D/'template_information.json').write_text(json.dumps(result,indent=2));np.savez_compressed(D/'template_operator.npz',A=A)
    print(json.dumps(result,indent=2))


def summarize_inverse():
    inv=pd.read_csv(D/'inverse_per_seed.csv');cla=pd.read_csv(D/'classical_per_seed.csv')
    results=pd.concat([inv,cla],ignore_index=True);xy=evaluation_grid();old=xy[:,2]<=-12
    # Interval coverage is an observer-window envelope, NOT coverage of every time by five exposures.
    rad=np.load(D/'radial_q64.npz');envelope=np.zeros(len(xy),bool)
    for n in [1,2]:
        tr=rad[f'n{n}_trace'];rv=tr[...,0].ravel();delay=tr[...,1].ravel()-100
        sort=np.argsort(rv);d=np.interp(xy[:,0],rv[sort],delay[sort]);envelope |= ((xy[:,2]>=-d)&(xy[:,2]<=8-d))
    extra=[]
    for seed in [11,22,33]:
        for method in ['comoving_data','comoving_robust_PINN','staged_residual_PINN','fourier_spline_ridge']:
            for acq in ['direct','all']:
                base=np.load(D/f'prediction_{seed}_{method}_{acq}_matched.npy')
                for variant in ['matched','event1','event2']:
                    pred=base if acq=='direct' else np.load(D/f'prediction_{seed}_{method}_{acq}_{variant}.npy')
                    truth=src(xy[:,0],xy[:,1],xy[:,2],variant);event=truth-src(xy[:,0],xy[:,1],xy[:,2],'matched')
                    rec=pred-base;w=xy[:,0]
                    if variant=='matched':eventerr=None;spurious=None
                    else:
                        eventerr=float(np.sqrt(np.sum(w[old]*(rec[old]-event[old])**2)/np.sum(w[old]*event[old]**2)))
                        emask=abs(event)>1e-10
                        spurious=float(np.sqrt(np.sum(w[~emask]*rec[~emask]**2)/np.sum(w*event**2)))
                    extra.append(dict(seed=seed,method=method,acquisition=acq,source=variant,event_difference_error=eventerr,
                        false_change_outside_event=spurious,old_observer_window_envelope_error=source_error(pred,truth,xy,old&envelope),
                        old_outside_window_envelope_error=source_error(pred,truth,xy,old&(~envelope))))
    ex=pd.DataFrame(extra);res=results.merge(ex,on=['seed','method','acquisition','source']);res.to_csv(D/'all_inverse_metrics.csv',index=False)
    group=res.groupby(['acquisition','source','method'])[['old_contrast_error','event_difference_error','old_observer_window_envelope_error','noisy_chi2','clean_chi2']].agg(['median','min','max'])
    group.to_csv(D/'inverse_summary.csv')
    print(group.to_string())

if __name__=='__main__':
    import sys
    summarize_inverse() if '--inverse' in sys.argv else template_diagnostic()
