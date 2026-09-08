"""Supplementary classical controls, defined AFTER the neural screen.
These are development crosschecks, not a hidden preregistered comparison.
A known-characteristic Fourier least-squares fit and a tensor-product cubic
spline/Fourier ridge fit are evaluated with GCV using training data only.
No test-source-error hyperparameter selection is performed.
"""
from common import *
from inverse import source,observation_design,evaluate_true,V
from scipy.interpolate import BSpline

def angular(phi):
    out=[np.ones_like(phi)]
    for k in range(1,5):out.extend([np.cos(k*phi),np.sin(k*phi)])
    return np.stack(out,axis=-1)
# 12 cubic basis functions; fixed before this control's result is computed.
KNOTS=np.r_[[-1.15]*4,np.linspace(-1.15,.35,10)[1:-1],[.35]*4]
SPL=BSpline(KNOTS,np.eye(len(KNOTS)-4),3,extrapolate=False)

def basis(coords,kind):
    p,t=coords[...,0],coords[...,1]
    if kind=='exact_transport_fourier':return angular(p-V*t)
    a=angular(p); b=SPL(t)
    return (a[..., :,None]*b[...,None,:]).reshape(*t.shape,-1)

def run():
    data=json.loads((ROOT/'inverse_results.json').read_text()); ary=np.load(ROOT/'inverse_arrays.npz')
    xy=ary['eval_coordinates'];old=ary['old_mask'];rows=[]
    dall=observation_design([0,1,2],48);native_y=evaluate_true(dall,False);sel=dall[3]==0
    for seed in CFG['seeds']:
      noise=np.random.default_rng(seed).normal(size=len(native_y))
      for kind in ('exact_transport_fourier','flexible_spline_fourier_ridge'):
       for scenario,event,orders in [('direct',False,[0]),('all_matched',False,[0,1,2]),('all_transient',True,[0,1,2])]:
        d=observation_design(orders,8);ref=evaluate_true(observation_design(orders,48),event)
        sig=.01*np.sqrt(d[2]);noisy=ref+sig*noise[sel if scenario=='direct' else np.ones(len(noise),bool)]
        baseline=d[1].sum(axis=1)
        A=np.einsum('mq,mqd->md',d[1],basis(d[0],kind))/sig[:,None]
        yy=(noisy-baseline)/sig
        u,s,vt=np.linalg.svd(A,full_matrices=False);uy=u.T@yy
        alphas=np.logspace(-8,4,37)
        fits=[]
        for alpha in alphas:
            f=s*s/(s*s+alpha);yhat=u@(f*uy)
            gcv=float(np.sum((yy-yhat)**2)/(len(yy)-f.sum())**2)
            fits.append(gcv)
        alpha=float(alphas[int(np.argmin(fits))]);c=vt.T@(s/(s*s+alpha)*uy)
        pred=1+basis(xy,kind)@c
        for testevent in ((False,True) if scenario=='direct' else (event,)):
            truth=ary['truth_event' if testevent else 'truth_base']
            rows.append(dict(seed=seed,model=kind,acquisition='direct' if scenario=='direct' else 'all_orders',
                       source='transient' if testevent else 'matched',alpha=alpha,
                       old_contrast_relative_error=relative(pred[old]-1,truth[old]-1),
                       full_contrast_relative_error=relative(pred-1,truth-1),
                       training_design_shape=list(A.shape),effective_df=float(np.sum(s*s/(s*s+alpha)))))
    dump('classical_results.json',dict(results=rows,scope=__doc__,gcv_alphas=alphas.tolist()))
    print('Classical crosschecks',len(rows),flush=True)
if __name__=='__main__':run()
