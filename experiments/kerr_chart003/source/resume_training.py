"""Record-only orchestration recovery: initial process interrupted by tool timeout.
Five completed fits retained. Reinitialize and run only unfinished physics seed33.
No source/calibration values changed; no hyperparameter or test outcome used.
"""
from experiment import *
cal=np.load(ROOT/'results/calibration81.npz');pre=dict(np.load(ROOT/'results/collocation_setup.npz'))
tx=torch.tensor(cal['xy']);ty=torch.tensor(cal['values'][:,:3]);ts=torch.tensor(pre['coordinates']);cp=torch_pre(pre)
logs=json.loads((ROOT/'results/training_progress.json').read_text())
if len(logs)!=5:raise RuntimeError('Expected exactly five completed pre-timeout fits')
seed=33;kind='physics';torch.manual_seed(seed);model=Net(kind);t0=time.perf_counter();calls=0

def closure():
    global calls
    rs=model(ts);integ=radial_torch(rs,cp)[:,0];resid=(integ-(cp['angular'][:,0]-cp['jo'][:,0]))/.001
    calls+=len(ts)
    return ((model(tx)-ty[:,0])/10).square().mean()+resid.square().mean()
opt=torch.optim.Adam(model.parameters(),lr=.003);trace=[]
for step in range(2500):
    opt.zero_grad(set_to_none=True);v=closure();v.backward();opt.step()
    if step%250==0:trace.append([step,float(v.detach())])
opt=torch.optim.LBFGS(model.parameters(),lr=.8,max_iter=200,history_size=40,tolerance_grad=1e-11,tolerance_change=1e-14,line_search_fn='strong_wolfe')
def lb():
    opt.zero_grad(set_to_none=True);v=closure();v.backward();return v
opt.step(lb);v=float(closure().detach());torch.save(model.state_dict(),ROOT/'models'/f'{kind}_{seed}.pt')
logs.append({'seed':seed,'kind':kind,'loss':v,'seconds':time.perf_counter()-t0,'training_residual_integral_evaluations':calls,'trace':trace})
dump('results/training.json',logs)
x,y,knots=grid(33);kp=precompute(knots,'freeze_precompute');np.savez_compressed(ROOT/'results/freeze_setup.npz',**kp);tpk=torch_pre(kp)
frozen=[]
for row in logs:
 model=Net(row['kind']);model.load_state_dict(torch.load(ROOT/'models'/f"{row['kind']}_{row['seed']}.pt",weights_only=True))
 with torch.no_grad():
  vals=model(torch.tensor(knots))
  if row['kind']=='physics':vals=complete_from_r(vals,tpk)
  vals=vals.numpy()
 p=ROOT/'models'/f"frozen_{row['kind']}_{row['seed']}.npz"
 np.savez_compressed(p,knots=knots,values=vals,axes_x=x,axes_y=y)
 Spline((x,y),vals).save(ROOT/'models'/f"coeff_{row['kind']}_{row['seed']}.npz")
 frozen.append({'kind':row['kind'],'seed':row['seed'],'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
dump('results/FROZEN_MODELS.json',frozen)
dump('attempts/TRAINING_INTERRUPTION.json',{'cause':'container command timeout; initial source intact','completed_fits_retained':5,'restarted_fit':'physics seed33 only','unfinished_optimizer_work_count':'not recovered; conservatively at most one full prescribed fit (2500 Adam + LBFGS line searches)','calibration_or_precompute_repeated':False,'test_outcomes_seen':False,'hyperparameters_changed':False})
print('Six models frozen',[(x['kind'],x['seed'],x['loss']) for x in logs])
