"""Build and independently check a physical source-crossing camera before inversion."""
from geodesics003 import *
from numpy.polynomial.legendre import leggauss
CONFIG=json.loads((ROOT/'protocol.json').read_text())
RESULT=ROOT/'results'

def src(r,phi,t,variant='matched'):
    rr=(r-6)/6; s=phi-r**(-1.5)*t
    bg=1+.18*(1-.25*rr)*np.cos(s+.3)+.13*(.75+.25*rr)*np.sin(2*s-.4)+.07*np.cos(3*s+.8)
    if variant!='matched':
        z=(t+26)/5;b=np.maximum(1-z*z,0)**3
        bg+=.5*b*(.5+.5*np.cos(np.pi*(rr-.5)))*(1+.7*np.cos(s-1.1))/1.7
    if variant=='event2':
        z=(t+43)/5;b=np.maximum(1-z*z,0)**3
        bg+=.5*b*(.6+.4*np.sin(np.pi*rr))*(1+.6*np.cos(2*(phi-.035*t)+.6))/1.6
    return bg


def make_camera(radial,edges,qphi=4,orders=(0,1,2),times=None):
    if times is None:times=np.array(CONFIG['detector']['observer_times_M'])
    u,w=leggauss(qphi);nphi=CONFIG['detector']['azimuth_pixels']
    pe=np.linspace(0,2*np.pi,nphi+1);px=(pe[:-1,None]+pe[1:,None])/2+np.diff(pe)[:,None]*u/2
    pw=np.diff(pe)[:,None]*w/2
    xyz=[];wg=[];area=[];oid=[];idx=[]
    for n in orders:
        b=radial[f'n{n}_b'];bw=radial[f'n{n}_bw'];rr,T,g=radial[f'n{n}_trace'][:,:,:3].transpose(2,0,1)
        for to in times:
            for ir in range(len(b)):
                r=np.broadcast_to(rr[ir,None,:,None],(nphi,len(b[ir]),qphi))
                ph=np.broadcast_to(px[:,None,:]+n*np.pi,r.shape)
                t=np.broadcast_to(to-(T[ir,None,:,None]-100),r.shape)
                ww=bw[ir,None,:,None]*weight_jacobian(b[ir,None,:,None])*pw[:,None,:]*g[ir,None,:,None]**3
                xyz.append(np.stack([r,ph,t],axis=-1).reshape(nphi,-1,3))
                wg.append(ww.reshape(nphi,-1))
                area.extend([camera_area(edges[n][ir],edges[n][ir+1],2*np.pi/nphi)]*nphi)
                oid.extend([n]*nphi);idx.extend([(n,float(to),ir,ip) for ip in range(nphi)])
    return dict(coords=np.concatenate(xyz),weights=np.concatenate(wg),areas=np.array(area),orders=np.array(oid),row_ids=np.array(idx))


def observe(cam,variant='matched'):
    c=cam['coords'];return np.sum(cam['weights']*src(c[...,0],c[...,1],c[...,2],variant),axis=1)


def radial_grid(edges,q,method='quad'):
    data={};u,w=leggauss(q)
    for n in range(3):
        e=edges[n];b=(e[:-1,None]+e[1:,None])/2+np.diff(e)[:,None]*u/2;bw=np.diff(e)[:,None]*w/2
        values=[(trace_quad(x,n) if method=='quad' else trace_ode(x,n)) for x in b.ravel()]
        data[f'n{n}_b']=b;data[f'n{n}_bw']=bw;data[f'n{n}_trace']=np.array(values).reshape(*b.shape,-1)
    return data


def run():
    if (RESULT/'forward_validation.json').exists():raise RuntimeError('No result overwrite')
    # Reuse authenticated engineering boundary arrays; direct endpoint radius is rechecked here.
    pre=json.loads((RESULT/'engineering_preflight.json').read_text())
    bands=np.array([pre[str(n)]['band'] for n in range(3)])
    edges=np.array([np.linspace(*ba,5) for ba in bands]);np.save(RESULT/'detector_edges.npy',edges)
    independent=[];rng=np.random.default_rng(803)
    for n in range(3):
        x=rng.uniform(*bands[n],32)
        for b in x:
            qa=trace_quad(b,n);ob=trace_ode(b,n)
            independent.append(dict(n=n,b=b,quad=qa.tolist(),ode=ob.tolist(),error=np.abs(qa[:3]-ob[:3]).tolist()))
    d=np.array([x['error'] for x in independent]);cons=max(x['ode'][4] for x in independent)
    gates=dict(radius=d[:,0].max()<2e-7,time=d[:,1].max()<2e-6,redshift=d[:,2].max()<1e-8,
        leg=all(x['quad'][3]==x['ode'][3] for x in independent),conservation=cons<2e-9,
        distinct_annuli=bool(bands[2,1]<bands[1,0]<bands[1,1]<bands[0,0]))
    gates={k:bool(v) for k,v in gates.items()}
    np.savez_compressed(RESULT/'point_reference_arrays.npz',quad=np.array([x['quad'] for x in independent]),ode=np.array([x['ode'] for x in independent]),b=np.array([x['b'] for x in independent]),order=np.array([x['n'] for x in independent]))
    (RESULT/'point_reference.json').write_text(json.dumps(dict(rows=independent,max_errors=d.max(0).tolist(),max_conservation=cons,gates=gates),indent=2))
    if not all(gates.values()):raise RuntimeError('Independent ray check failed')
    cameras={}
    for q in [4,8,16,32,64]:
        radial=radial_grid(edges,q)
        np.savez_compressed(RESULT/f'radial_q{q}.npz',**radial)
        cam=make_camera(radial,edges,qphi=q if q<=16 else 32)
        for n in range(3):
            if np.any((cam['coords'][cam['orders']==n,:,0]<6-1e-6)|(cam['coords'][cam['orders']==n,:,0]>12+1e-6)):
                raise RuntimeError('Unknown emitting domain encountered')
        np.savez_compressed(RESULT/f'camera_q{q}.npz',**cam)
        cameras[q]=cam
        print('built camera q',q,'rays',sum(1 for _ in LEDGER.open()),flush=True)
    primary=make_camera(np.load(RESULT/'radial_q8.npz'),edges,qphi=8)
    rd=radial_grid(edges,8,'ode');np.savez_compressed(RESULT/'independent_radial_q8.npz',**rd)
    reference=make_camera(rd,edges,qphi=8)
    checks={};out={}
    base_ref=cameras[64]['weights'].sum(1);a=cameras[64]['areas'];m=cameras[64]['orders']==0
    sref=np.sqrt(np.mean((base_ref[m]/np.sqrt(a[m]))**2));sigma=sref/1000
    for variant in ['matched','event1','event2']:
        truth=observe(cameras[64],variant);out[f'y_{variant}']=truth
        y32=observe(cameras[32],variant)
        yo=observe(reference,variant);yq=observe(primary,variant)
        for n in range(3):
            sel=cameras[64]['orders']==n;sd=np.sqrt(a[sel]);den=np.linalg.norm(truth[sel]/sd)
            checks[f'{variant}_n{n}']=dict(q32_q64=float(np.linalg.norm((truth-y32)[sel]/sd)/den),
                quad_ode_q8=float(np.linalg.norm((yo-yq)[sel]/sd)/np.linalg.norm(yq[sel]/sd)),
                q4_q64=float(np.linalg.norm((observe(cameras[4],variant)-truth)[sel]/sd)/den))
    qpass=max(x['q32_q64'] for x in checks.values())<2e-6
    opass=max(x['quad_ode_q8'] for x in checks.values())<2e-6
    out.update(areas=a,orders=cameras[64]['orders'],baseline=base_ref,sigma=np.array(sigma))
    np.savez_compressed(RESULT/'observations.npz',**out)
    footprint=[]
    for n in range(3):
        c=cameras[64]['coords'][cameras[64]['orders']==n]
        footprint.append(dict(order=n,b_min=bands[n,0],b_max=bands[n,1],area_per_time=float(a[cameras[64]['orders']==n].sum()/5),
                source_time_min=float(c[...,2].min()),source_time_max=float(c[...,2].max()),
                delay_min=float((100-c[...,2]).min()),note='source-time extremes include observer window; full flight extrema separately in radial payload'))
    twin={}
    for v in ['event1','event2']:
        dv=out[f'y_{v}']-out['y_matched']
        twin[v]=dict(direct_max_abs=float(np.max(abs(dv[m]))),
            whitened_distance_at_SNR1000=float(np.linalg.norm(dv/(sigma*np.sqrt(a)))),
            per_order_distance_at_SNR1000=[float(np.linalg.norm(dv[cameras[64]['orders']==n]/(sigma*np.sqrt(a[cameras[64]['orders']==n])))) for n in range(3)])
    gates.update(detector_quadrature=qpass,independent_detector=opass,direct_twins=all(v['direct_max_abs']==0 for v in twin.values()))
    summary=dict(gates=gates,point_errors=d.max(0).tolist(),response_checks=checks,sigma_at1000=sigma,footprints=footprint,twins=twin,
        numerical_certification='Convergence and independent formulation on tested sets; not interval-arithmetic continuum proof',
        forward_definition='Face-on Schwarzschild annulus r in[6,12]; circular emitting material, g^3 specific intensity, ideal camera with exact rescaled solid-angle measure')
    (RESULT/'forward_validation.json').write_text(json.dumps(summary,indent=2))
    if not all(gates.values()):raise RuntimeError('Forward renderer gate failed')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
