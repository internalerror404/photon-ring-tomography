"""Post-outcome quadrature/readback closeout, no new model or truth endpoint.
Initial outcomes preserved. Fixed source splines re-read from saved coefficients.
"""
from evaluate import *
from scipy.interpolate import _fitpack2

def load_coeff(path):
    d=np.load(path); spl=[]
    for j in range(3):
        spl.append(_fitpack2.BivariateSpline._from_tck((d[f'tx{j}'],d[f'ty{j}'],d[f'coeff{j}'],3,3)))
    def f(xy):return np.column_stack([s.ev(xy[:,0],xy[:,1]) for s in spl])
    return f

def pixel_piece_design(q):
    u,w=leggauss(q);xx,yy,unused=grid(33);points=[];weights=[];pix=[]
    # Vector chart Jacobian, with cached scalar critical radius only.
    for i in range(32):
      for j in range(32):
        xs=.5*(xx[i+1]+xx[i])+.5*(xx[i+1]-xx[i])*u
        zs=.5*(yy[j+1]+yy[j])+.5*(yy[j+1]-yy[j])*u
        X,Z=np.meshgrid(xs,zs,indexing='ij');rc=np.array([kerr.rc_of_lambda(float(x)) for x in xs])[:,None]
        rt=rc+np.exp(Z);P=rt*rt+kerr.A*kerr.A-kerr.A*X;D=rt*rt-2*rt+kerr.A*kerr.A
        eta=P*P/D-(X-kerr.A)**2;ep=4*rt*P/D-P*P*(2*rt-2)/D**2
        beta=np.sqrt(eta+kerr.A*kerr.A*kerr.MU0*kerr.MU0-X*X*(kerr.MU0/np.sin(kerr.INC))**2)
        jac=ep*np.exp(Z)/(2*np.sin(kerr.INC)*beta)
        ww=.25*(xx[i+1]-xx[i])*(yy[j+1]-yy[j])*np.outer(w,w)*jac
        points.append(np.column_stack([X.ravel(),Z.ravel()]));weights.append(ww.ravel());pix.extend([4*(i//8)+j//8]*(q*q))
    return np.concatenate(points),np.concatenate(weights),np.array(pix)

def run():
    t0=time.perf_counter();r=json.loads((ROOT/'results/RESULTS.json').read_text());a=np.load(ROOT/'results/ALL_EVALUATION_ARRAYS.npz');ref=a['reference_vectors_q16'];areas=a['pixel_areas'];frozen=load_frozen()
    for n in (9,17,33):
        z=np.load(ROOT/'results/classical_grid1089.npz');gridvalues=z['values'].reshape(33,33,4)[::32//(n-1),::32//(n-1),:3]
        xx,yy,_=grid(n);frozen[f'classical_{n}']=Spline((xx,yy),gridvalues)
    coeff={};rd={};raw={};readerr=[]
    for name in frozen:
        p=ROOT/'models'/(f'coeff_{name}.npz' if not name.startswith('classical') else f"coeff_classical{name.split('_')[-1]}.npz")
        coeff[name]=load_coeff(p);er=np.max(abs(coeff[name](a['test_xy'])-frozen[name](a['test_xy'])));readerr.append(er)
    quad={q:pixel_piece_design(q) for q in (4,8)}
    for name,fn in coeff.items():
        y={}
        for q,(xy,w,pix) in quad.items():
            y[q]=integrate(augment(fn(xy),xy),w,pix,areas);raw[f'{name}_split_q{q}']=y[q]
        e=rels(y[8],ref);rd[name]={'max_channel_error':float(e.max()),'median_channel_error':float(np.median(e)),'per_channel_error':e.tolist(),
                'channels_failing':int(np.sum(e>5e-4)),'split_q4_q8_max_relative':float(np.max(rels(y[4],y[8]))),
                'primary_q16_difference':float(np.max(rels(y[8],a[f'{name}_vectors_q16'])))}
    # These setups are additional and metered; source tuples are NOT new truth solves.
    xy,w,pix=design(3);pre=precompute(xy,'freeze_native_closeout');tp=torch_pre(pre)
    conversion={}
    for kind in ('data','physics'):
      for seed in (11,22,33):
        name=f'{kind}_{seed}';net=Net(kind);net.load_state_dict(torch.load(ROOT/'models'/f'{name}.pt',weights_only=True))
        with torch.no_grad():
            v=net(torch.tensor(xy));v=complete_from_r(v,tp) if kind=='physics' else v
            v=v.numpy()
        native=integrate(augment(v,xy),w,pix,areas);spl=integrate(augment(coeff[name](xy),xy),w,pix,areas)
        conversion[name]={'max_relative_same_q3_detector_change':float(np.max(rels(spl,native)))}
        raw[f'{name}_native_q3']=native;raw[f'{name}_frozen_q3']=spl
    dump('results/CLOSEOUT.json',{'models':rd,'frozen_vs_native':conversion,'coefficient_readback_max_abs':max(readerr),
       'fixed_model_files_unchanged':all(hashlib.sha256((ROOT/'models'/d['file']).read_bytes()).hexdigest()==d['sha256'] for d in json.loads((ROOT/'results/FROZEN_MODELS.json').read_text())),
       'seconds':time.perf_counter()-t0,'scope':__doc__})
    np.savez_compressed(ROOT/'results/SPLIT_INTEGRATION_VECTORS.npz',**raw)
    print(json.dumps({name:(v['max_channel_error'],v['split_q4_q8_max_relative']) for name,v in rd.items()},indent=2));print('CONVERSION',conversion)

if __name__=='__main__':run()
