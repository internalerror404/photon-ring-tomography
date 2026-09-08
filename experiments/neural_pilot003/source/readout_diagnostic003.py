"""POST-TEST diagnostic of frozen learned features, not a new primary competitor.
Exact least-squares readout on same noisy training data at SVD rcond=1e-10.
No hidden-feature training, no selection with source truth; no PINN-objective optimum claim.
"""
from inverse003 import *

def run():
    if (D/'readout_diagnostic.csv').exists():raise RuntimeError('No overwrite')
    cam=dict(np.load(D/'camera_q4.npz'));xy=evaluation_grid();old=xy[:,2]<=-12;obs,sig=noise_parameters();rows=[]
    for seed in [11,22,33]:
        noise=np.random.default_rng(seed).normal(size=len(sig))
        for method in ['comoving_data','comoving_robust_PINN','staged_residual_PINN']:
            for variant in ['event1','event2']:
                key=f'{seed}_{method}_all_{variant}'
                if method=='staged_residual_PINN':m=SumField(Field(16,True),Field(24));readout=m.res
                else:m=Field(32);readout=m
                m.load_state_dict(torch.load(CK/f'{key}.pt',weights_only=True))
                c=ten(cam['coords']);w=cam['weights'];last=readout.net[-1]
                with torch.no_grad():
                    h=readout.net[:-1](features(c)).numpy();hp=[]
                    for chunk in np.array_split(xy,4):hp.append(readout.net[:-1](features(ten(chunk))).numpy())
                    H=np.concatenate(hp)
                    base=(m.base(c).numpy() if method=='staged_residual_PINN' else np.zeros_like(w))
                    gridbase=(m.base(ten(xy)).numpy() if method=='staged_residual_PINN' else np.zeros(len(xy)))
                h=np.concatenate([h,np.ones((*h.shape[:-1],1))],-1);H=np.c_[H,np.ones(len(H))]
                A=np.einsum('nq,nqd->nd',w,h)/sig[:,None];offset=(w*(1+base)).sum(1)
                yy=obs['y_'+variant]+sig*noise;z=(yy-offset)/sig
                coef,res,rank,s=np.linalg.lstsq(A,z,rcond=1e-10)
                pred=1+gridbase+H@coef;fit=offset+sig*(A@coef);tr=src(xy[:,0],xy[:,1],xy[:,2],variant)
                original=np.load(D/f'fit_observations_{key}.npz')['predicted']
                rows.append(dict(seed=seed,method=method,source=variant,rank=rank,nfeatures=A.shape[1],
                    original_noisy_chi2=float(np.mean(((original-yy)/sig)**2)),refit_noisy_chi2=float(np.mean(((fit-yy)/sig)**2)),
                    refit_old_contrast_error=source_error(pred,tr,xy,old),coefficient_norm=float(np.linalg.norm(coef))))
    pd.DataFrame(rows).to_csv(D/'readout_diagnostic.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':run()
