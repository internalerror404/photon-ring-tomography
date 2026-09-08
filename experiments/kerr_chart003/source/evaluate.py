"""Held-fixed post-training evaluation. All outputs, including failed gates, retained.
No hyperparameter changes or promotion based on training residual alone.
"""
from experiment import *
from collections import Counter
import scipy

def fields(vals,times=np.linspace(0,20,8)):
    r,phi,T,g=vals.T;a=g**3;out=[];labels=[]
    for t in times:
        ph=t-T
        v=[a,a*np.cos(2*np.pi*ph/20),a*np.sin(2*np.pi*ph/20),a*np.cos(2*np.pi*ph/40),a*np.sin(2*np.pi*ph/40),a*(r-10)/10,a*np.cos(phi),a*np.sin(phi)]
        out.extend(v);labels.extend([f'{name}:t{t:.15g}' for name in ('g3','cos20','sin20','cos40','sin40','radial','cosphi','sinphi')])
    return np.stack(out,-1),labels

def design(q):
    u,w=leggauss(q);e0=np.linspace(LOW[0],HIGH[0],5);e1=np.linspace(LOW[1],HIGH[1],5)
    points=[];weights=[];pix=[]
    for i in range(4):
      for j in range(4):
        xs=.5*(e0[i]+e0[i+1])+.5*(e0[i+1]-e0[i])*u
        ys=.5*(e1[j]+e1[j+1])+.5*(e1[j+1]-e1[j])*u
        xx,yy=np.meshgrid(xs,ys,indexing='ij')
        base=.25*(e0[i+1]-e0[i])*(e1[j+1]-e1[j])*np.outer(w,w)
        ps=np.column_stack([xx.ravel(),yy.ravel()]);jj=np.array([kerr.invariants(*p)['jac'] for p in ps])
        points.append(ps);weights.append(base.ravel()*jj);pix.extend([4*i+j]*len(ps))
    return np.concatenate(points),np.concatenate(weights),np.array(pix)

def integrate(vals,weights,pix,areas):
    f,labels=fields(vals);y=np.zeros((16,f.shape[1]));np.add.at(y,pix,weights[:,None]*f)
    return y/(.01*np.sqrt(areas))[:,None]

def rels(a,b):
    den=np.linalg.norm(b,axis=0);num=np.linalg.norm(a-b,axis=0)
    return num/den

def load_frozen():
    out={}
    for d in json.loads((ROOT/'results/FROZEN_MODELS.json').read_text()):
        p=ROOT/'models'/d['file']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=d['sha256']:raise RuntimeError('Frozen file hash failed')
        v=np.load(p);name=f"{d['kind']}_{d['seed']}"
        out[name]=Spline((v['axes_x'],v['axes_y']),v['values'])
    return out

def run():
    t0=time.perf_counter();checks={};summaries={};raw={};frozen=load_frozen()
    # New IDs never used for training or geometry selection.
    rng=np.random.default_rng(53003);xy=LOW+(HIGH-LOW)*rng.random((128,2))
    v64,meta,records=reference(xy,64,'heldout_B64');v96,_,_=reference(xy,96,'heldout_B96')
    ode=[];vode=[]
    for p in xy[:48]:
        d=kerr.ode_transfer(*map(float,p),phase='heldout_A');ode.append(d);vode.append(d.get('tuple',np.full(4,np.nan)))
    vode=np.array(vode);diff=vode-v96[:48];difff=np.abs(diff);difff[:,1]=abs(np.angle(np.exp(1j*diff[:,1])))
    tol=np.array([2e-6,2e-7,2e-6,2e-7]);checks['independent_primitive_tolerances']=bool(np.all(difff.max(axis=0)<tol))
    checks['independent_classifications']=all(d['status']=='EMITTING' and d['leg']==1 for d in ode)
    checks['B64_B96_converged']=bool(np.max(abs(v64-v96))<2e-8)
    raw['test_xy']=xy;raw['test_reference']=v96;raw['test_ODE']=vode
    dump('results/independent_validation.json',{'max_absolute_tuple_error':difff.max(axis=0),'tuple_order':['r','phase','T','g'],
         'thresholds':tol,'B64_B96_max_abs':np.max(abs(v64-v96),axis=0),'max_radial_invariant':max(d['radial_first_integral_error'] for d in ode),
         'max_polar_invariant':max(d['angular_first_integral_error'] for d in ode),'records':ode,'checks':checks})
    # Classical nested-grid values. Existing 81 knots genuinely reused, every other endpoint charged.
    x33,y33,g33=grid(33);cal=np.load(ROOT/'results/calibration81.npz');lookup={tuple(p):v for p,v in zip(cal['xy'],cal['values'])}
    v33=[]
    for p in g33:
        key=tuple(p)
        if key in lookup:v33.append(lookup[key])
        else:
            vals,_,_=reference(np.array([p]),64,'classical_nested');v33.append(vals[0])
    v33=np.array(v33);np.savez_compressed(ROOT/'results/classical_grid1089.npz',xy=g33,values=v33)
    for n,stride in ((9,4),(17,2),(33,1)):
        v=v33.reshape(33,33,4)[::stride,::stride,:3];s=Spline((x33[::stride],y33[::stride]),v)
        frozen[f'classical_{n}']=s;s.save(ROOT/'models'/f'coeff_classical{n}.npz')
    for name,spl in frozen.items():
        pred=augment(spl(xy),xy);raw[f'test_{name}']=pred
        summaries[name]={'primitive_max_abs_error':np.max(abs(pred-v96),axis=0).tolist(),
                         'primitive_median_abs_error':np.median(abs(pred-v96),axis=0).tolist()}
    # Fixed detector quadrature ladder; not adaptive selection based on candidate error.
    ref_vectors={};designs={};reference_tuples={};areas16=None
    for q in (16,10,6):
        pts,weights,pix=design(q);areas=np.bincount(pix,weights,minlength=16)
        if q==16:areas16=areas
        v,_,_=reference(pts,64,f'detector_B_q{q}')
        yr=integrate(v,weights,pix,areas16);ref_vectors[q]=yr;designs[q]=(pts,weights,pix);reference_tuples[q]=v
        raw[f'pixels_q{q}']=pix;raw[f'weights_q{q}']=weights;raw[f'detector_xy_q{q}']=pts
        raw[f'reference_tuples_q{q}']=v;raw[f'reference_vectors_q{q}']=yr
    reference_pair={str(q):float(np.max(rels(v,ref_vectors[16]))) for q,v in ref_vectors.items() if q!=16}
    checks['reference_detector_q10_q16']=reference_pair['10']<5e-7
    checks['reference_detector_q6_q16']=reference_pair['6']<5e-6
    raw['pixel_areas']=areas16
    for name,spl in frozen.items():
        byq={};vectors={}
        for q in (6,10,16):
            pts,weights,pix=designs[q];pred=augment(spl(pts),pts);yy=integrate(pred,weights,pix,areas16)
            byq[q]=rels(yy,ref_vectors[16]);vectors[q]=yy;raw[f'{name}_vectors_q{q}']=yy
        err=byq[16];summaries[name].update({'max_channel_error':float(err.max()),'median_channel_error':float(np.median(err)),
          'per_channel_error':err.tolist(),'channels_above_5e4':int(np.sum(err>5e-4)),
          'detector_q10_q16':float(np.max(rels(vectors[10],vectors[16]))),'detector_q6_q16':float(np.max(rels(vectors[6],vectors[16])))})
        print(name,summaries[name]['max_channel_error'],summaries[name]['median_channel_error'],summaries[name]['channels_above_5e4'],flush=True)
    # Direct independent ODE-vs-B response with IDENTICAL q3 nodes/weights.
    pts,w,pix=design(3);vb,_,_=reference(pts,64,'detector_matched_Bq3');va=[]
    for p in pts:va.append(kerr.ode_transfer(*map(float,p),phase='detector_matched_Aq3')['tuple'])
    va=np.array(va);yb=integrate(vb,w,pix,areas16);ya=integrate(va,w,pix,areas16)
    matchedODE=float(np.max(rels(ya,yb)));checks['independent_detector_same_rule']=matchedODE<2e-7
    raw.update(ODE_detector_xy=pts,ODE_detector_values=va,ODE_detector_Bvalues=vb,ODE_detector_weights=w,ODE_detector_pixels=pix)
    # Native neural-vs-frozen compare on heldout points; physics setup from already saved B reference, no new setup queries.
    prem={'coordinates':xy,'meta':meta,'other':np.array([kerr.radial_setup(d['meta'])[0] for d in records]),
          'angular':np.array([d['angular'] for d in records]),'jo':np.array([d['radial_observer'] for d in records])}
    pp=torch_pre(prem);residuals={}
    for kind in ('data','physics'):
      for seed in (11,22,33):
        name=f'{kind}_{seed}';net=Net(kind);net.load_state_dict(torch.load(ROOT/'models'/f'{name}.pt',weights_only=True))
        with torch.no_grad():
            v=net(torch.tensor(xy))
            if kind=='physics':
                js=radial_torch(v,pp)[:,0];res=js-(pp['angular'][:,0]-pp['jo'][:,0]);v=complete_from_r(v,pp)
                # Conditional monotone inverse estimate, not a validated interval calculation.
                rmax=[]
                for d in records:
                    l=d['meta']['lam'];e=d['meta']['eta'];RR=(20**2+kerr.A*kerr.A-kerr.A*l)**2-(20**2-40+kerr.A*kerr.A)*(e+(l-kerr.A)**2);rmax.append(np.sqrt(RR))
                bound=np.array(rmax)*(abs(res.numpy())+1e-10)
                actual=abs(v[:,0].numpy()-v96[:,0])
                residuals[name]={'max_abs_radial_integral_residual':float(abs(res).max()),'actual_max_radius_error':float(actual.max()),
                                  'max_conditional_radius_envelope':float(bound.max()),'violations_on_128_points':int(np.sum(actual>bound)),
                                  'scope':'Mathematical monotone inverse bound conditional on exact integral residual; +1e-10 is an empirical integration safety allowance, NOT a rigorous enclosure.'}
            v=v.numpy()
        summaries[name]['frozen_vs_native_tuple_max_abs']=np.max(abs(frozen[name](xy)-v),axis=0).tolist()
        raw[f'native_{name}_test']=v
    # Algebraic source-linearity and chart Jacobian checks.
    vals=v96;F,_=fields(vals);W=meta[:,3];x=F[:,1];y=F[:,2];checks['source_linearity']=np.max(abs(W*(2*x-3*y)-(2*W*x-3*W*y)))<1e-13
    jacerr=[]
    for p,mm in zip(xy[:16],meta[:16]):
        h=1e-5;bplus=kerr.invariants(p[0],p[1]+h)['beta'];bminus=kerr.invariants(p[0],p[1]-h)['beta'];jfd=-(bplus-bminus)/(2*h*np.sin(kerr.INC));jacerr.append(abs(jfd/mm[3]-1))
    checks['chart_jacobian_finite_difference']=max(jacerr)<2e-7
    # Exact invariance: translate observer clock and all delays by same shift.
    vshift=vals.copy();vshift[:,2]+=13.;fs,_=fields(vshift,np.linspace(0,20,8)+13.)
    checks['common_clock_shift_invariance']=np.max(abs(F-fs))<1e-13
    rs=vals[:,0];om=1/(rs**1.5+kerr.A);ut=(1+kerr.A/rs**1.5)/np.sqrt(1-3/rs+2*kerr.A/rs**1.5)
    norm=ut**2*((-1+2/rs)+2*(-2*kerr.A/rs)*om+(rs**2+kerr.A**2+2*kerr.A**2/rs)*om**2)
    checks['source_timelike_unit_norm']=np.max(abs(norm+1))<1e-12
    rejected=False
    try:frozen['classical_9'](np.array([[1.,-2.]]))
    except ValueError:rejected=True
    checks['outside_chart_refused']=rejected
    counts=Counter(json.loads(x)['method'] for x in (ROOT/'attempts/physical_calls.jsonl').read_text().splitlines())
    checks['physical_caps']=counts['separated_quadrature']<=10000 and counts['compactified_ode']<=220 and counts['equation_precompute']<=1600
    dump('results/RESULTS.json',{'models':summaries,'reference_pairs':reference_pair,'ODE_matched_rule_detector_error':matchedODE,
          'checks':checks,'all_checks_pass':all(checks.values()),'root_jacobian_max_rel_finite_difference':max(jacerr),
          'physical_evaluation_counts':dict(counts),'residual_bounds':residuals,'evaluation_seconds':time.perf_counter()-t0,
          'tuple_scope':{'test_radius_range':list(np.min(v96[:,0:1],axis=0))+list(np.max(v96[:,0:1],axis=0)),
          'test_delay_range':[float(v96[:,2].min()),float(v96[:,2].max())]},
          'limitations':['One geometrically selected patch; no claim of whole lensing-band coverage.','Impact-plane detector differs from original D026.','No global interval residual bound or continuum certificate.','One fixed geometry/order/source velocity; shared equations/redshift across numerical algorithms.'],
          'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__}})
    raw['channel_labels']=np.array(fields(v96)[1]);np.savez_compressed(ROOT/'results/ALL_EVALUATION_ARRAYS.npz',**raw)
    print('CHECKS',checks,'COUNTS',counts,'SECONDS',time.perf_counter()-t0,flush=True)

if __name__=='__main__':run()
