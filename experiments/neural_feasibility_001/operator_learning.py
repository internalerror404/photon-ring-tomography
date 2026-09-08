"""Reduced spectral operator experiment borrowing PINO's multiresolution loss.
Input functions are projected onto four Fourier modes. A shared continuous
neural temporal multiplier acts on every function in that span. This is not
FNO reproduction and does NOT remove representation assumptions.
"""
from common import *
V=.8;M=4
class Operator(nn.Module):
    def __init__(self):super().__init__();self.net=mlp(1,2*M)
    def forward(self,t):
        raw=t[:,None]*self.net(2*t[:,None]-1)
        re=1+raw[:,:M]; im=raw[:,M:]
        return torch.cat([re,im],dim=-1)

def expand(z,coeff,phi):
    c=coeff[:,:M]-1j*coeff[:,M:]
    zz=z[:,:M]+1j*z[:,M:]
    return np.real(np.einsum('hm,tm,pm->htp',c,zz,np.exp(1j*np.outer(phi,np.arange(1,M+1)))))

def run():
    cfg=CFG['operator_learning'];omega=tensor(np.arange(1,M+1)*V)
    tdata=tensor(np.linspace(0,1,5));exactdata=torch.cat([torch.cos(tdata[:,None]*omega),-torch.sin(tdata[:,None]*omega)],dim=-1)
    coll=tensor(np.linspace(0,1,128));tt=np.linspace(0,1,37);phi=np.linspace(0,2*np.pi,127,endpoint=False)
    c=np.random.default_rng(7741).normal(size=(96,8))/np.tile(np.arange(1,5),(96,2))
    exactz=np.concatenate([np.cos(tt[:,None]*omega.numpy()),-np.sin(tt[:,None]*omega.numpy())],axis=-1)
    truth=expand(exactz,c,phi);rows=[];arrays={'coefficients':c,'times':tt,'phi':phi,'truth':truth}
    for seed in CFG['seeds']:
      for kind in ('data','pino'):
        seed_all(seed);model=Operator()
        def closure():
            data=(model(tdata)-exactdata).square().mean()
            if kind=='data':return data
            t=coll.detach().clone().requires_grad_(True);z=model(t)
            dz=torch.stack([torch.autograd.grad(z[:,j].sum(),t,create_graph=True,retain_graph=True)[0] for j in range(8)],dim=-1)
            resre=dz[:,:M]-omega*z[:,M:];resim=dz[:,M:]+omega*z[:,:M]
            return data+.1*(resre.square().mean()+resim.square().mean())
        info=fit(model,closure,cfg['adam_steps'],cfg['lbfgs_max_iter'])
        with torch.no_grad():z=model(tensor(tt)).numpy()
        pred=expand(z,c,phi); errs=np.linalg.norm((pred-truth).reshape(96,-1),axis=1)/np.linalg.norm(truth.reshape(96,-1),axis=1)
        row=dict(model=kind,seed=seed,median_heldout_field_relative_error=float(np.median(errs)),
                  max_heldout_field_relative_error=float(np.max(errs)),
                  sixth_mode_relative_error=1.0,
                  input_span='Four Fourier modes; canonical-basis training with 5 time labels; 96 new coefficient fields evaluated',**info)
        rows.append(row);arrays[f'prediction_{kind}_{seed}']=pred
        torch.save(model.state_dict(),ROOT/f'operator_{kind}_{seed}.pt')
        dump('operator_results.json',dict(results=rows,non_neural_exact_fourier_propagator_error=0.,
            out_of_basis='Pure sixth mode is orthogonal to the 4-mode encoder: predicted zero, relative error one',
            scope='Reduced operator-learning demonstration; not benchmark of published PINO architecture'))
        print(kind,seed,row['median_heldout_field_relative_error'],flush=True)
    np.savez_compressed(ROOT/'operator_arrays.npz',**arrays)
if __name__=='__main__':run()
