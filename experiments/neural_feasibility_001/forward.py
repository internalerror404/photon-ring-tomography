"""Manufactured near-critical-like log-delay surrogate.
The logarithmic leading term is an intentionally supplied asymptotic structure,
not a fitted Kerr formula. A classical structure-aware comparator is included.
"""
from common import *
from numpy.polynomial.legendre import leggauss
from scipy.interpolate import CubicSpline
XMIN=float(np.exp(-8))

def exact(x):return -np.log(x)+.08*(x-1)
class Delay(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind;self.net=mlp(1,1)
    def forward(self,x):
        q=torch.log(x)/4+1 if self.kind=='factored_pinn' else 2*x-1
        r=(1-x)*self.net(q[:,None]).squeeze(-1)
        return -torch.log(x)+r if self.kind=='factored_pinn' else r

def detector(fn,q=64):
    e=np.exp(np.linspace(-8,0,13));u,w=leggauss(q)
    # Integrate in log coordinate but include exact dx Jacobian.
    le=np.log(e);z=(le[:-1,None]+le[1:,None])/2+(le[1:,None]-le[:-1,None])*u/2
    x=np.exp(z); ww=(le[1:,None]-le[:-1,None])*w/2*x
    val=np.sum(ww*np.cos(3*fn(x)),axis=1)
    return val/np.sqrt(np.diff(e))

def run():
    cfg=CFG['forward'];xs=np.linspace(XMIN,1,24);ys=exact(xs)
    xgrid=np.exp(np.linspace(-8,0,2049)); truth=exact(xgrid)
    yt=detector(exact,96); check=relative(detector(exact,48),yt)
    spline=CubicSpline(np.log(xs),ys)
    # Fixed analytical-leading-term plus constant residual: one-parameter control.
    feat=1-xs;coef=float(feat@(ys+np.log(xs))/(feat@feat))
    baselines={
      'log_coordinate_cubic_spline':lambda x:spline(np.log(x)),
      'known_log_plus_linear_residual':lambda x:-np.log(x)+coef*(1-x),
    }
    rows=[];arrays={'x':xgrid,'truth':truth}
    for name,fn in baselines.items():
        rows.append(dict(model=name,seed=None,delay_log_grid_relative_error=relative(fn(xgrid),truth),
            whitened_detector_relative_error=relative(detector(fn),yt),seconds=0.,parameter_count=1 if name.endswith('residual') else None))
        arrays[name]=fn(xgrid)
    for seed in CFG['seeds']:
      for kind in ('data','raw_pinn','factored_pinn'):
        seed_all(seed);model=Delay(kind);tx=tensor(xs);ty=tensor(ys)
        coll=tensor(np.exp(np.linspace(-8,0,256)))
        def closure():
            data=((model(tx)-ty)/8).square().mean()
            if kind=='data':return data
            xc=coll.detach().clone().requires_grad_(True);value=model(xc)
            deriv=torch.autograd.grad(value.sum(),xc,create_graph=True)[0]
            phys=(xc*deriv+1-.08*xc).square().mean()
            return data+phys
        info=fit(model,closure,cfg['adam_steps'],cfg['lbfgs_max_iter'])
        def fn(x):
            with torch.no_grad():return model(tensor(np.asarray(x).ravel())).numpy().reshape(np.shape(x))
        pred=fn(xgrid)
        xc=tensor(xgrid[::4]).requires_grad_(True);v=model(xc)
        der=torch.autograd.grad(v.sum(),xc)[0]
        row=dict(model=kind,seed=seed,delay_log_grid_relative_error=relative(pred,truth),
            whitened_detector_relative_error=relative(detector(fn),yt),
            heldout_pde_rms=float((xc*der+1-.08*xc).square().mean().sqrt()),
            parameter_count=sum(p.numel() for p in model.parameters()),**info)
        rows.append(row);arrays[f'{kind}_{seed}']=pred
        torch.save(model.state_dict(),ROOT/f'forward_{kind}_{seed}.pt')
        dump('forward_results.json',dict(results=rows,reference_quadrature_relative_48_96=check,
              truth_equation=cfg['equation'],residual_coefficient_control=coef,
              scope='Manufactured scalar transfer surrogate only; no actual Kerr transfer validation.'))
        print(kind,seed,row['delay_log_grid_relative_error'],row['whitened_detector_relative_error'],flush=True)
    np.savez_compressed(ROOT/'forward_arrays.npz',**arrays)
if __name__=='__main__':run()
