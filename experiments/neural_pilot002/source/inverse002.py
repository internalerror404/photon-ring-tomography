"""Matched tuning and heldout transient tests; no test-truth hyperparameter tuning."""
from support import *
import argparse, hashlib
from scipy.interpolate import BSpline
LAMS=[.03,.1,.3,1.];SEEDS=[101,202,303]
def validation():
    if (OUT/'selected_lambdas.json').exists():raise RuntimeError('Selection already exists')
    rows=[]
    for method in ['data','quadratic','innovation']:
      for lam in ([0.] if method=='data' else LAMS):
       vals=[]
       for k,(ps,kind) in enumerate([(701,'matched'),(702,'single')]):
        p=parameters(ps);tag=f'val_{method}_{lam}_{k}'
        m,inf,obs=train_field(p,kind,method,lam,909,[0,1,2],tag)
        dv=design([0,1,2],24,20,[.035,.095,.155,.215]);yv=response(dv,p,kind);sig=.01*np.sqrt(dv[2]);yv+=sig*np.random.default_rng(99000+k).normal(size=len(yv))
        score=float(np.mean(((predict(m,dv)-yv)/sig)**2));vals.append(score)
        rows.append(dict(method=method,lambda_=lam,validation_case=kind,chi2=score,**inf))
        save('inverse_validation.json',dict(rows=rows,source_truth_used_for_tuning=False))
        print('VAL',method,lam,kind,score,round(inf['seconds'],1),flush=True)
    choices={'data':0.}
    for method in ['quadratic','innovation']:
        loss=[(np.mean([r['chi2'] for r in rows if r['method']==method and r['lambda_']==l]),l) for l in LAMS];choices[method]=min(loss)[1]
    save('selected_lambdas.json',dict(choices=choices,criterion='independent validation-observation mean chi2 across matched and single-transient; no test-truth use',test_outcomes_seen=False))
    print('SELECTED',choices,flush=True)

def angular(p):
    out=[np.ones_like(p)]
    for k in range(1,5):out.extend([np.cos(k*p),np.sin(k*p)])
    return np.stack(out,-1)
knots=np.r_[[-1.15]*4,np.linspace(-1.15,.35,10)[1:-1],[.35]*4];spl=BSpline(knots,np.eye(len(knots)-4),3,extrapolate=False)
def basis(x):
    a=angular(x[...,0]);b=spl(x[...,1]);return (a[..., :,None]*b[...,None,:]).reshape(*x.shape[:-1],-1)
def classical(p,kind,ss,orders,xy):
    d=design(orders);dd=design(orders,48);sig=.01*np.sqrt(d[2]);yv=response(dd,p,kind)
    nz=np.random.default_rng(ss+313*p['seed']).normal(size=240);yv+=sig*nz[np.arange(80) if len(orders)==1 else np.arange(240)]
    A=np.einsum('mq,mqd->md',d[1],basis(d[0]))/sig[:,None];y=(yv-d[1].sum(1))/sig
    U,s,Vt=np.linalg.svd(A,full_matrices=False);uy=U.T@y;als=np.logspace(-8,4,37)
    scores=[]
    for a in als:
        f=s*s/(s*s+a);scores.append(np.sum((y-U@(f*uy))**2)/(len(y)-f.sum())**2)
    al=float(als[np.argmin(scores)]);c=Vt.T@(s/(s*s+al)*uy);pred=1+basis(xy)@c
    return pred,al

def test():
    cho=json.loads((OUT/'selected_lambdas.json').read_text())['choices'];selection_hash=hashlib.sha256((OUT/'selected_lambdas.json').read_bytes()).hexdigest()
    gridp,gridt=np.meshgrid(np.linspace(0,2*np.pi,96,endpoint=False),np.linspace(-.98,.25,81),indexing='ij');xy=np.stack([gridp.ravel(),gridt.ravel()],-1);old=(xy[:,1]>=-.95)&(xy[:,1]<=-.38)
    rows=[];arr={'coordinates':xy,'old_mask':old};checks=[]
    for b,ps in enumerate([1701,2701]):
      p=parameters(ps)
      d=design([0,1,2],48)
      for kind in ['single','double']:
        diff=response(d,p,kind)-response(d,p,'matched');sig=.01*np.sqrt(d[2]);checks.append(dict(background=b,kind=kind,direct_max_abs=float(np.max(abs(diff[:80]))),all_whitened_separation=float(np.linalg.norm(diff/sig))))
      for kind in ['matched','single','double']:arr[f'truth_b{b}_{kind}']=source(xy,p,kind)
      for ss in SEEDS:
       for method in ['data','quadratic','innovation']:
        for kind,orders in [('direct',[0]),('matched',[0,1,2]),('single',[0,1,2]),('double',[0,1,2])]:
         trainingkind='matched' if kind=='direct' else kind;tag=f'test_b{b}_s{ss}_{method}_{kind}'
         m,inf,obs=train_field(p,trainingkind,method,cho[method],ss,orders,tag)
         with torch.no_grad():pred=m(tensor(xy)).numpy()
         arr[tag]=pred
         # Retain observations; no separate-pixel-point likelihood expansion.
         arr[tag+'_observations']=obs['y']
         for evalkind in (['matched','single','double'] if kind=='direct' else [kind]):
          truth=arr[f'truth_b{b}_{evalkind}'];tr_base=arr[f'truth_b{b}_matched'];event=truth-tr_base
          row=dict(background=b,seed=ss,method=method,source=evalkind,acquisition='direct' if kind=='direct' else 'all_orders',old_contrast_error=relative(pred[old]-1,truth[old]-1),full_contrast_error=relative(pred-1,truth-1),negative_fraction=float(np.mean(pred<0)),lambda_=cho[method],**{k:v for k,v in inf.items() if k!='trace'})
          if evalkind!='matched':row['event_error_in_truth_event_region']=relative((pred-tr_base)[old&(abs(event)>.01)],event[old&(abs(event)>.01)])
          dh=design(orders,24,20,[.017,.077,.137,.197]);row['heldout_clean_response_error']=relative(predict(m,dh),response(dh,p,evalkind))
          rows.append(row)
         save('inverse_test.json',dict(rows=rows,twin_checks=checks,selection_hash=selection_hash,stats='two independent background realizations with matched/single/double variants; seeds not independent sources'))
         np.savez_compressed(OUT/'inverse_predictions.npz',**arr)
         print('TEST',b,ss,method,kind,'old',rows[-1]['old_contrast_error'],round(inf['seconds'],1),flush=True)
       for kind,orders in [('direct',[0]),('matched',[0,1,2]),('single',[0,1,2]),('double',[0,1,2])]:
        trainingkind='matched' if kind=='direct' else kind;pred,al=classical(p,trainingkind,ss,orders,xy);arr[f'classical_b{b}_s{ss}_{kind}']=pred
        for ek in (['matched','single','double'] if kind=='direct' else [kind]):
         truth=arr[f'truth_b{b}_{ek}'];rows.append(dict(background=b,seed=ss,method='spline_ridge',source=ek,acquisition='direct' if kind=='direct' else 'all_orders',old_contrast_error=relative(pred[old]-1,truth[old]-1),full_contrast_error=relative(pred-1,truth-1),alpha=al))
        save('inverse_test.json',dict(rows=rows,twin_checks=checks,selection_hash=selection_hash))
        np.savez_compressed(OUT/'inverse_predictions.npz',**arr)
    print('TESTS COMPLETE',len(rows),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['validation','test']);a=p.parse_args()
    validation() if a.stage=='validation' else test()
