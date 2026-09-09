"""Fixed local source-field inverse: data-only / robust PINN, q3 / q8.
Not an amortized neural operator, not full NeRF, not direct-vs-order comparison.
The neural models never receive the event-template basis used by the separately
reported amplitude inverse. Numerical accuracy is checked AFTER training too.
"""
from common import *
import torch
from torch import nn
import pandas as pd

torch.set_default_dtype(torch.float64);torch.set_num_threads(1)

def ten(x):return torch.as_tensor(x,dtype=torch.float64)

class Field(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(8,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,1))
        with torch.no_grad():
            self.net[-1].weight.mul_(.2);self.net[-1].bias.zero_()
    def forward(self,c):
        r,p,t=c.unbind(-1)
        f=[(r-11)/5,(t-10)/15]
        for m in [1,2,3]:f.extend([torch.sin(m*p),torch.cos(m*p)])
        return 1+self.net(torch.stack(f,-1)).squeeze(-1)

def tensor_design(d):
    return {'coords':ten(d['coords']),'kernel':ten(d['kernel'])}

def project(model,d):return (model(d['coords'])*d['kernel'][None,:,:]).sum(-1).reshape(128)

def pde(model,coll):
    xy=coll.detach().clone().requires_grad_(True)
    out=model(xy)
    grad=torch.autograd.grad(out.sum(),xy,create_graph=True)[0]
    return (grad[:,2]+1/(xy[:,0]**1.5+.5)*grad[:,1])/.03

def derivative_data(model,d,noisy,std):
    out=project(model,d);loss=torch.mean(((out-noisy)/std)**2)
    grads=torch.autograd.grad(loss,list(model.parameters()))
    return float(loss.detach()),torch.cat([x.reshape(-1) for x in grads]).detach().numpy()

def run():
    if (ROOT/'results/NEURAL_RESULTS.json').exists():raise RuntimeError('Refuse overwrite; use fresh directory')
    renderer=CachedRenderer();dref=renderer.design(16,reference=True)
    design={q:tensor_design(renderer.design(q,n=33)) for q in [3,8,16,24]}
    evalvals=renderer.cache['test_reference']
    te=np.linspace(0,20,37)
    evcoords=np.stack([np.broadcast_to(evalvals[:,0,None],(128,37)),np.broadcast_to(evalvals[:,1,None],(128,37)),te[None,:]-evalvals[:,2,None]+145],-1).reshape(-1,3)
    std=ten(noise_std(renderer.areas,.001))
    records=[];arrays={'eval_coords':evcoords,'eval_observer_times':te,'std':std.numpy(),'reference_test_tuples':evalvals}
    global_start=time.perf_counter();budget=1200
    for seed in [11,22,33]:
      z=np.random.default_rng(410000+seed).normal(size=128)
      for events in [False,True]:
        coeff=truth_coefficients(events);truth=fields(evcoords,coeff)
        clean=response(dref,fields(dref['coords'],coeff));noisy=ten(clean+std.numpy()*z)
        scenario='events' if events else 'background'
        arrays[f'truth_{scenario}']=truth;arrays[f'clean_{scenario}']=clean;arrays[f'noisy_{scenario}_s{seed}']=noisy.numpy()
        rng=np.random.default_rng(420000+seed)
        coll=ten(rng.uniform([6.5,-7.56,-7],[17,-7.07,26],size=(256,3)))
        for method in ['data_only','robust_pinn']:
          for q in [3,8]:
            if time.perf_counter()-global_start>budget:
                dump('results/BLOCKED.json',{'reason':'walltime cap before new fit','completed':len(records)});return
            name=f'{scenario}_{method}_q{q}_s{seed}'
            torch.manual_seed(seed);model=Field()
            inp=design[q];count=0;trace=[];start=time.perf_counter()
            def objective():
                nonlocal count
                count+=1
                data=(((project(model,inp)-noisy)/std)**2).mean()
                if method=='data_only':return data
                zz=pde(model,coll);h=torch.where(abs(zz)<=1,zz**2,2*abs(zz)-1)
                return data+.03*h.mean()
            opt=torch.optim.Adam(model.parameters(),lr=.002)
            with (ROOT/'logs/FIT_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'fit':name,'state':'start','wallclock':time.time()})+'\n')
            for step in range(1000):
                opt.zero_grad(set_to_none=True);loss=objective()
                if not torch.isfinite(loss):raise FloatingPointError(name)
                loss.backward();opt.step()
                if step%200==0:trace.append([step,float(loss.detach())])
            opt=torch.optim.LBFGS(model.parameters(),lr=.8,max_iter=100,history_size=30,line_search_fn='strong_wolfe',tolerance_grad=1e-10,tolerance_change=1e-13)
            def closure():
                opt.zero_grad(set_to_none=True);v=objective();v.backward();return v
            opt.step(closure)
            loss=float(objective().detach());elapsed=time.perf_counter()-start
            torch.save(model.state_dict(),ROOT/'models'/f'{name}.pt')
            with torch.no_grad():
                pred=model(ten(evcoords)).numpy();responses={n:project(model,design[n]).numpy() for n in [3,8,16,24]}
            gradfitval,gfit=derivative_data(model,design[q],noisy,std)
            gradrefval,gref=derivative_data(model,design[16],noisy,std)
            relquad={str(n):relative(responses[n],responses[24]) for n in [3,8,16]}
            whitequad={str(n):float(np.linalg.norm((responses[n]-responses[24])/std.numpy())) for n in [3,8,16]}
            state_rms=pde(model,coll).detach().numpy()*.03
            record={'id':name,'seed':seed,'scenario':scenario,'method':method,'training_quadrature':q,
               'contrast_error_chart_pullback':relative(pred-1,truth-1),'total_source_error':relative(pred,truth),
               'minimum_prediction':float(pred.min()),'negative_prediction_fraction':float(np.mean(pred<0)),
               'noisy_chi2_training':float(np.mean(((responses[q]-noisy.numpy())/std.numpy())**2)),
               'noisy_chi2_q24':float(np.mean(((responses[24]-noisy.numpy())/std.numpy())**2)),
               'clean_chi2_q24':float(np.mean(((responses[24]-clean)/std.numpy())**2)),
               'training_objective':loss,'pde_RMS':float(np.sqrt(np.mean(state_rms**2))),
               'quadrature_relative_to24':relquad,'quadrature_whitened_to24':whitequad,
               'training_quadrature_qualified_on_fitted_field':bool(relquad[str(q)]<=5e-4 and whitequad[str(q)]<=.1),
               'q16_q24_qualified_on_fitted_field':bool(relquad['16']<=5e-4 and whitequad['16']<=.1),
               'data_gradient_relative_training_vs16':float(np.linalg.norm(gfit-gref)/max(np.linalg.norm(gref),1e-15)),
               'data_gradient_norm_train':float(np.linalg.norm(gfit)),'data_gradient_norm_q16':float(np.linalg.norm(gref)),
               'seconds':elapsed,'objective_evaluations':count,'adam_trace':trace}
            records.append(record);arrays['prediction_'+name]=pred
            for n,v in responses.items():arrays[f'response_{name}_q{n}']=v
            dump('results/NEURAL_PROGRESS.json',{'results':records,'elapsed':time.perf_counter()-global_start})
            np.savez_compressed(ROOT/'results/NEURAL_ARRAYS.npz',**arrays)
            with (ROOT/'logs/FIT_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'fit':name,'state':'complete','seconds':elapsed,'objective_calls':count})+'\n')
            print(name,'contrast',round(record['contrast_error_chart_pullback'],5),'quad',whitequad[str(q)],'seconds',round(elapsed,2),flush=True)
    dump('results/NEURAL_RESULTS.json',{'results':records,'fits':len(records),'elapsed':time.perf_counter()-global_start,
          'notes':['each fit same optimizer steps; fine rule higher arithmetic cost','metric restricted to available chart source-point/time distribution','three seeds are noise/initialization repeats of two fixed source scenarios, not six independent event families']})
    pd.DataFrame([{k:v for k,v in x.items() if k not in ['adam_trace','quadrature_relative_to24','quadrature_whitened_to24']} for x in records]).to_csv(ROOT/'results/NEURAL_PER_FIT.csv',index=False)
    print('COMPLETED',len(records),'fits',time.perf_counter()-global_start,flush=True)

if __name__=='__main__':run()
