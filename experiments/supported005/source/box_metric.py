"""Postplanned alternative-metric diagnostic with exact spline source Gram.
This is NOT a replacement for the registered chart-sample RMS experiment.
The source norm now covers an explicitly declared r/phi/time BOX using r dr dphi dt,
normalized to unit total measure. No proper-volume or full-source physical claim.
Finite spline Gram products are integrated exactly by piecewise Gaussian rules.
"""
from experiment import *
from numpy.polynomial.legendre import leggauss
from scipy.linalg import cholesky, solve_triangular


def axis_rule(knot_vector,q,radial=False):
    edges=np.unique(knot_vector);x,w=leggauss(q)
    out=np.concatenate([(a+b)/2+(b-a)/2*x for a,b in zip(edges[:-1],edges[1:])])
    ww=np.concatenate([(b-a)/2*w for a,b in zip(edges[:-1],edges[1:])])
    if radial:ww=ww*out
    return out,ww/ww.sum()

def rule3(shape,n):
    nr,nt,nphi=shape;lim=CFG['source_dictionary']['domain'];kr=knots(*lim['r'],nr);kt=knots(*lim['tbar'],nt)
    r,wr=axis_rule(kr,n,True);t,wt=axis_rule(kt,n,False);p,wp=axis_rule(lim['phi'],n,False)
    rr,pp,tt=np.meshgrid(r,p,t,indexing='ij');c=np.stack([rr.ravel(),pp.ravel(),tt.ravel()],-1)
    w=(wr[:,None,None]*wp[None,:,None]*wt[None,None,:]).ravel()
    return c,w

def normer(shape):
    lim=CFG['source_dictionary']['domain'];nr,nt,nphi=shape
    r,wr=axis_rule(knots(*lim['r'],nr),4,True);t,wt=axis_rule(knots(*lim['tbar'],nt),4)
    br=BSpline.design_matrix(r,knots(*lim['r'],nr),3).toarray();bt=BSpline.design_matrix(t,knots(*lim['tbar'],nt),3).toarray()
    Gr=br.T@(wr[:,None]*br);Gt=bt.T@(wt[:,None]*bt);Gp=np.diag(1/(2*np.arange(nphi)+1))
    H=np.kron(np.kron(Gr,Gt),Gp)
    R=cholesky(H,lower=False);X=solve_triangular(R,np.eye(len(R)),lower=False)
    return H,X

def wrms(a,w):return float(np.sqrt(w@(a*a)))

def execute():
    t0=time.perf_counter();a=np.load(ROOT/'results/ARRAYS.npz');old=np.load(PARENT/'results/NEURAL_ARRAYS.npz');lin=np.load(PARENT/'results/LINEAR_ARRAYS.npz')
    phy=np.load(PARENT/'results/PHYSICAL_FITTED_RESPONSE_READBACK.npz');rnd=prior.CachedRenderer();sig=old['std'];N=len(old['eval_coords'])
    spectra=[];decomps=[];corrections=[];profiles=[];arrays={};newgram={}
    d10=rnd.design(10,reference=True);d24=rnd.design(24,n=33)
    for shape in CFG['source_dictionary']['nested_classes']:
        name='B'+str(np.prod(shape));H,X=normer(shape);A=a[name+'_A16'];B=A@X/sig[:,None]
        u,s,vt=svd(B,full_matrices=True);V=vt.T;spad=np.r_[s,np.zeros(len(H)-len(s))]
        Qorig=dictionary(old['eval_coords'],shape);Pold=Qorig@X@V
        coords,w=rule3(shape,8);Q=dictionary(coords,shape);Q0=Q@X;Qm=Q0@V
        coords6,w6=rule3(shape,6)
        H8=Q.T@(w[:,None]*Q);orth=float(np.max(abs(Q0.T@(w[:,None]*Q0)-np.eye(len(H)))))
        newgram[name]=(H,X,u,s,V,Qorig,coords,w,Qm)
        st={'basis':name,'source_dimension':len(H),'numerical_response_rank':int(np.sum(s>s[0]*1e-10)),
            'source_normalizer_condition':float(np.linalg.cond(X)),'gram_analytic_vs_quad8':float(np.max(abs(H-H8))),
            'source_orthonormality':orth,'modes_SNR1':int(np.sum(.1*s>=1)),'modes_SNR5':int(np.sum(.1*s>=5)),
            'q10_q16_source_normalized_operator_difference':float(svd((a[name+'_A10']-A)@X/sig[:,None],compute_uv=False)[0]),
            'q24_q16_source_normalized_operator_difference':float(svd((a[name+'_A24']-A)@X/sig[:,None],compute_uv=False)[0]),
            'spectrum':spad,'source_norm':'normalized r dr dphi dt on declared box, not chart-pullback norm'}
        for scenario in ('background','events'):
            coeff=prior.truth_coefficients(scenario=='events');truth=prior.fields(coords,coeff);truth6=prior.fields(coords6,coeff)
            tr=truth-1;truecoeff=Qm.T@(w*tr);noise=1/s
            st[scenario+'_actual_coeffs_above_noise1']=int(np.sum(abs(truecoeff[:len(s)])*s>=1))
            st[scenario+'_actual_coeffs_above_noise5']=int(np.sum(abs(truecoeff[:len(s)])*s>=5))
            projection=Qm@truecoeff;st[scenario+'_box_representation_error']=wrms(tr-projection,w)/wrms(tr,w)
            base=np.tile(rnd.design(16,reference=True)['kernel'].sum(1),8)
            remainder=(old['clean_'+scenario]-base-A@X@V@truecoeff)/sig
            st[scenario+'_projection_remainder_detector_norm']=float(np.linalg.norm(remainder))
            for method in ('data_only','robust_pinn'):
              for seed in (11,22,33):
                key=f'{scenario}_{method}_q8_s{seed}';mod=Field();mod.load_state_dict(torch.load(PARENT/'models'/f'{key}.pt',weights_only=True))
                with torch.no_grad():
                    pred=mod(ten(coords)).numpy();pred6=mod(ten(coords6)).numpy()
                    resp10=project(mod,tensor_design(d10)).numpy();resp24=project(mod,tensor_design(d24)).numpy()
                error=pred-truth;ce=Qm.T@(w*error);outside=error-Qm@ce
                total=w@(error**2);outenergy=w@(outside**2)
                for th in (1,5):
                    k=int(np.sum(.1*s>=th));low=float(ce[:k]@ce[:k]);weak=float(ce[k:]@ce[k:])
                    dec={'basis':name,'scenario':scenario,'method':method,'seed':seed,'threshold':th,'count':k,
                         'box_source_error':np.sqrt(total)/wrms(tr,w),'chart_source_error':prior.relative(old['prediction_'+key]-old['truth_'+scenario],old['truth_'+scenario]-1),
                         'high_response_squared_error_fraction':low/total,'weak_squared_error_fraction':weak/total,
                         'outside_squared_error_fraction':float(outenergy/total),'Pythagorean_residual':float(abs(total-low-weak-outenergy)/total),
                         'box_error_quad6_quad8_change':abs(wrms(pred6-truth6,w6)-np.sqrt(total))}
                    decomps.append(dec)
                    obs=old[f'noisy_{scenario}_s{seed}'];res=(obs-phy[key+'_physical_q16'])/sig
                    dc=V[:,:k]@((u[:,:k].T@res)/s[:k]);pnew=pred+Q0@dc
                    pchart=old['prediction_'+key]+Qorig@X@dc
                    responses={16:phy[key+'_physical_q16']+A@X@dc,10:resp10+a[name+'_A10']@X@dc,24:resp24+a[name+'_A24']@X@dc}
                    newres=(obs-responses[16])/sig
                    corrections.append({'basis':name,'scenario':scenario,'method':method,'seed':seed,'threshold':th,'modes':k,
                      'raw_box_error':dec['box_source_error'],'corrected_box_error':wrms(pnew-truth,w)/wrms(tr,w),
                      'raw_chart_error':dec['chart_source_error'],'corrected_chart_error':prior.relative(pchart-old['truth_'+scenario],old['truth_'+scenario]-1),
                      'raw_whitened_residual':float(np.linalg.norm(res)),'corrected_whitened_residual':float(np.linalg.norm(newres)),
                      'projected_residual_after':float(np.linalg.norm(u[:,:k].T@newres)),
                      'q10_q16_corrected_whitened':float(np.linalg.norm((responses[10]-responses[16])/sig)),
                      'q24_q16_corrected_whitened':float(np.linalg.norm((responses[24]-responses[16])/sig)),
                      'source_noise_box_RMS':float(np.sqrt(np.sum(1/s[:k]**2))),'minimum_checked_corrected_field':float(pnew.min())})
                    if name=='B135' and th==5:
                        arrays['chart_corrected_'+key]=pchart
        spectra.append(st);arrays[name+'_s']=spad;arrays[name+'_X']=X;arrays[name+'_V']=V
        print('BOX',name,'rank',st['numerical_response_rank'],'modes',st['modes_SNR1'],st['modes_SNR5'],'Qerr',orth,flush=True)
    # Explicit positive-box ambiguity using an analytic coefficient envelope.
    name='B315';H,X,u,s,V,Qorig,c,w,Qm=newgram[name];rank=int(np.sum(s>s[0]*1e-10));VN=V[:,rank:]
    trial=np.sin(np.pi*(c[:,0]-6.5)/10.5)*np.sin(2*np.pi*(c[:,2]+7)/33)
    cc=Qm@np.zeros(len(H)) # shape fixture only; no additional model
    qs=dictionary(c,[7,15,3])@X
    projection=qs.T@(w*trial);v=VN@(VN.T@projection)
    v/=np.linalg.norm(v);co=X@v
    # B-splines nonnegative partition of unity; |Legendre0..2| <=1 on [-1,1].
    bound=float(np.max(np.sum(abs(co.reshape(7,15,3)),axis=2)))
    amp=min(.1,.5/(bound*(1+1e-12)))
    d={q:2*amp*a[name+'_A'+str(q)]@co for q in (10,16,24)}
    chart=Qorig@co
    witness={'scope':'fixed polynomial field in declared box; uniform positivity follows from basis envelope, with a numerical safety margin',
         'source_norm':'normalized box r dr dphi dt','null_rank_tolerance':1e-10,'numerical_null_dimension':V.shape[0]-rank,
         'analytic_coefficient_sup_envelope':bound,'one_sided_box_RMS':amp,'two_history_box_RMS_separation':2*amp,
         'guaranteed_minimum_j_from_basis_bound':1-amp*bound,
         'chart_pullback_RMS_separation':2*amp*rms(chart),
         'reference16_whitened_difference':float(np.linalg.norm(d[16]/sig)),
         'reference10_whitened_difference':float(np.linalg.norm(d[10]/sig)),
         'classical33_q24_whitened_difference':float(np.linalg.norm(d[24]/sig))}
    arrays['witness_box_coeff']=co;arrays['witness_box_amplitude']=np.array(amp)
    arrays['witness_box_chart_plus']=1+amp*chart;arrays['witness_box_chart_minus']=1-amp*chart
    checks={'all_gram_checks_pass':all(s['gram_analytic_vs_quad8']<1e-10 and s['source_orthonormality']<1e-8 for s in spectra),
       'error_partitions_pass':max(d['Pythagorean_residual'] for d in decomps)<1e-8,
       'source_loss_quadrature_agrees':max(d['box_error_quad6_quad8_change'] for d in decomps)<1e-4,
       'all_corrections_response_whitened_test_pass':max(max(d['q10_q16_corrected_whitened'],d['q24_q16_corrected_whitened']) for d in corrections)<=.1,
       'positive_box_witness':witness['guaranteed_minimum_j_from_basis_bound']>=.5,
       'witness_measured_differences_below_noise_fraction':max(witness[k] for k in ('reference16_whitened_difference','reference10_whitened_difference','classical33_q24_whitened_difference'))<.1}
    dump('results/BOX_METRIC.json',{'scope':__doc__,'spectra':spectra,'decompositions':decomps,'corrections':corrections,'witness':witness,
          'checks':checks,'seconds':time.perf_counter()-t0,'new_rays':0,'new_network_fits':0,
          'postplanned':'new source-norm diagnostic after sampled-metric failure; not a retroactive replacement or claim about same relative error metric'})
    np.savez_compressed(ROOT/'results/BOX_METRIC_ARRAYS.npz',**arrays)
    print('BOX CHECKS',checks,'WITNESS',witness,flush=True)
if __name__=='__main__':execute()
