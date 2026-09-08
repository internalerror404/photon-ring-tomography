"""Neural emissivity inversion through a manufactured distributed-delay renderer.
This is a one-angle/time tomography proxy, NOT Kerr ray tracing or volumetric NeRF.
Pixel observations are integrals, with correctly transformed area-noise variance.
"""
from common import *
from numpy.polynomial.legendre import leggauss
PI=np.pi; V=CFG['inverse']['source_velocity']

def source(phi,t,transient=False):
    s=phi-V*t
    j=1+.22*np.cos(s)+.15*np.sin(2*s+.35)+.09*np.cos(3*s-.4)
    if transient:
        z=(t+.67)/.24
        bump=np.maximum(1-z*z,0)**3
        j=j+.55*bump*(1+.6*np.cos(2*s+.2))/1.6
    return j

def observation_design(orders,q=8,npix=16,times=None):
    if times is None: times=np.linspace(0,.24,5)
    u,w=leggauss(q); edges=np.linspace(0,2*PI,npix+1); dx=np.diff(edges)
    mids=(edges[:-1]+edges[1:])/2
    xx=mids[:,None]+dx[:,None]/2*u[None,:]
    basew=dx[:,None]/2*w[None,:]
    coords=[]; weights=[]; areas=[]; orderids=[]
    for n in orders:
        phi=xx+[0,.7,1.3][n]+.10*n*np.sin(xx)
        delay=[.10,.50,.90][n]+.06*np.cos(xx)+.025*n*np.sin(2*xx)
        amp=[1.,.55,.28][n]*(1+.08*np.cos(xx))
        for to in times:
            coords.append(np.stack([phi,to-delay],axis=-1))
            weights.append(basew*amp); areas.extend(dx.tolist());orderids.extend([n]*npix)
    return np.concatenate(coords),np.concatenate(weights),np.asarray(areas),np.asarray(orderids)

def evaluate_true(design,transient=False):
    c,w,_,_=design
    return np.sum(w*source(c[...,0],c[...,1],transient),axis=1)

class SourceField(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind; self.net=mlp(8 if kind=='characteristic' else 9,1)
    def forward(self,coord):
        phi,t=coord[...,0],coord[...,1]
        s=phi-V*t if self.kind=='characteristic' else phi
        inputs=[]
        for k in range(1,5): inputs += [torch.cos(k*s),torch.sin(k*s)]
        if self.kind!='characteristic':inputs.append(t)
        return 1+self.net(torch.stack(inputs,dim=-1)).squeeze(-1)

def run():
    config=CFG['inverse']; results=[]; arrays={}; references={}
    for orders in ([0],[0,1,2]):
        for transient in (False,True):
            d48=observation_design(orders,48);d96=observation_design(orders,96)
            y48=evaluate_true(d48,transient);y96=evaluate_true(d96,transient)
            references[str((orders,transient))]=dict(max_abs_48_96=float(np.max(abs(y48-y96))),relative_48_96=relative(y48,y96))
    all48=observation_design([0,1,2],48)
    y_base=evaluate_true(all48,False);y_event=evaluate_true(all48,True)
    sigmas=config['noise_density']*np.sqrt(all48[2])
    direct=all48[3]==0
    nullcheck=dict(direct_twin_max_abs=float(np.max(abs(y_base[direct]-y_event[direct]))),
                   all_order_twin_whitened_separation=float(np.linalg.norm((y_base-y_event)/sigmas)))
    pp,tt=np.meshgrid(np.linspace(0,2*PI,128,endpoint=False),np.linspace(-.98,.25,81),indexing='ij')
    evalxy=np.stack([pp.ravel(),tt.ravel()],-1);old=(evalxy[:,1]>=-.95)&(evalxy[:,1]<=-.38)
    truth_base=source(evalxy[:,0],evalxy[:,1],False);truth_event=source(evalxy[:,0],evalxy[:,1],True)
    arrays.update(eval_coordinates=evalxy,old_mask=old,truth_base=truth_base,truth_event=truth_event)
    # The direct fit is reused for both truths: inputs and physics losses are identical.
    scenarios=[('direct',False,[0]),('all_matched',False,[0,1,2]),('all_transient',True,[0,1,2])]
    for seed in CFG['seeds']:
        rng=np.random.default_rng(seed);noise_all=rng.normal(size=len(y_base))
        for kind in ('data','pinn','characteristic'):
            for tag,event,orders in scenarios:
                seed_all(seed)
                model=SourceField(kind)
                d=observation_design(orders,config['training_pixel_quadrature'])
                ref=evaluate_true(observation_design(orders,48),event)
                inds=direct if tag=='direct' else np.ones(len(y_base),bool)
                sig=config['noise_density']*np.sqrt(d[2]); noisy=ref+sig*noise_all[inds]
                coords=tensor(d[0]);weights=tensor(d[1]);yt=tensor(noisy);st=tensor(sig)
                crng=np.random.default_rng(1000+seed)
                coll=tensor(np.stack([crng.uniform(0,2*PI,256),crng.uniform(-.98,.25,256)],axis=1))
                def closure():
                    pred=(model(coords)*weights).sum(dim=1)
                    ld=(((pred-yt)/st)**2).mean()
                    if kind=='pinn':
                        co=coll.detach().clone().requires_grad_(True)
                        f=model(co);grad=torch.autograd.grad(f.sum(),co,create_graph=True)[0]
                        residual=(grad[:,1]+V*grad[:,0])/config['pde_scale']
                        return ld+residual.square().mean()
                    return ld
                info=fit(model,closure,config['adam_steps'],config['lbfgs_max_iter'])
                with torch.no_grad():
                    estimate=model(tensor(evalxy)).numpy()
                    predobs=(model(coords)*weights).sum(dim=1).numpy()
                    held=observation_design(orders,24,npix=24,times=[.03,.09,.15,.21])
                    heldpred=(model(tensor(held[0]))*tensor(held[1])).sum(dim=1).numpy()
                co=tensor(evalxy[::8]).requires_grad_(True)
                f=model(co);grad=torch.autograd.grad(f.sum(),co)[0]
                pderms=float(torch.mean((grad[:,1]+V*grad[:,0])**2).sqrt())
                for evaluate_event in ((False,True) if tag=='direct' else (event,)):
                    truth=truth_event if evaluate_event else truth_base
                    row=dict(seed=seed,model=kind,acquisition='direct' if tag=='direct' else 'all_orders',
                             source='transient' if evaluate_event else 'matched',
                             old_contrast_relative_error=relative(estimate[old]-1,truth[old]-1),
                             full_contrast_relative_error=relative(estimate-1,truth-1),
                             clean_training_chi2=float(np.mean(((predobs-ref)/sig)**2)),
                             heldout_observation_relative_error=relative(heldpred,evaluate_true(held,evaluate_event)),
                             pde_rms=pderms,negative_fraction=float(np.mean(estimate<0)),**info)
                    results.append(row)
                arrays[f'prediction_s{seed}_{kind}_{tag}']=estimate
                torch.save(model.state_dict(),ROOT/f'inverse_s{seed}_{kind}_{tag}.pt')
                dump('inverse_results.json',dict(protocol=config,results=results,reference_checks=references,nullspace_twin=nullcheck))
                print(seed,kind,tag,'old',results[-1]['old_contrast_relative_error'],'seconds',round(info['seconds'],2),flush=True)
    np.savez_compressed(ROOT/'inverse_arrays.npz',**arrays)
    return results
if __name__=='__main__':run()
