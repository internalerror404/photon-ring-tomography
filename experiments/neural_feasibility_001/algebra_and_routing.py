"""Exact obstruction and bounded-support routing tests on manufactured data.
This is a Kiran-inspired access-policy proxy, not the deployed Kiran network.
"""
from common import *
from inverse import source,observation_design,evaluate_true
from scipy import sparse

def run():
    checks=[]
    def ck(name,cond,**values):
        checks.append(dict(name=name,passed=bool(cond),**values))
        if not cond: raise AssertionError(name)
    # Measurement non-identifiability and compensating renderer clock error.
    d=observation_design([0,1,2],64)
    coords,w,areas,_=d
    truth=evaluate_true(d,False)
    shift=.15
    shifted_coords=coords.copy();shifted_coords[...,1]-=shift
    compensating=np.sum(w*source(shifted_coords[...,0],shifted_coords[...,1]+shift,False),axis=1)
    ph,tt=np.meshgrid(np.linspace(0,2*np.pi,128,endpoint=False),np.linspace(-.95,-.38,61),indexing='ij')
    actual=source(ph,tt,False); alternative=source(ph,tt+shift,False)
    clocksourceerror=relative(alternative-1,actual-1)
    ck('wrong_common_delay_can_have_identical_data_and_exact_advection',np.max(abs(compensating-truth))<1e-14,
       maximum_data_discrepancy=float(np.max(abs(compensating-truth))),source_contrast_error=clocksourceerror,
       pde_residual_both='exactly zero analytically')
    y0=evaluate_true(d,False);y1=evaluate_true(d,True);direct=d[3]==0
    sep=float(np.linalg.norm((y0-y1)/(.01*np.sqrt(areas))))
    ck('two_distinct_histories_give_identical_direct_data',np.array_equal(y0[direct],y1[direct]),
       direct_difference=float(np.max(abs(y0[direct]-y1[direct]))),stack_whitened_separation=sep)
    # A pointwise sensitivity map cannot identify which linear combination is measured.
    A=np.array([[1.,1.]])/np.sqrt(2);_,s,vt=np.linalg.svd(A,full_matrices=True)
    P=vt[:1].T@vt[:1]; null=np.array([1.,-1.])/np.sqrt(2)
    ck('both_pixels_sensitive_but_one_contrast_null',np.all(np.diag(A.T@A)>0) and np.linalg.norm(A@null)<1e-14,
       diagonal_information=np.diag(A.T@A).tolist(),null_vector=null.tolist(),singular_values=s.tolist())
    x=np.array([3.,1.]);supported=P@x;completion=(np.eye(2)-P)@x
    ck('mode_projection_preserves_data_but_is_not_a_pixel_mask',np.linalg.norm(A@completion)<1e-14 and not np.allclose(P,np.diag(np.diag(P))),
       source=x.tolist(),supported=supported.tolist(),null_completion=completion.tolist())
    # Fixed sparsity of bilinear source-field evaluation, not dropping ray contributions.
    rng=np.random.default_rng(83); nx,nt=64,32; n=1000
    xy=rng.uniform(size=(n,2));px=xy[:,0]*nx;pt=xy[:,1]*(nt-1)
    ix=np.floor(px).astype(int);it=np.floor(pt).astype(int);fx=px-ix;ft=pt-it
    ids=np.stack([ix*nt+it,((ix+1)%nx)*nt+it,ix*nt+it+1,((ix+1)%nx)*nt+it+1],axis=1)
    weights=np.stack([(1-fx)*(1-ft),fx*(1-ft),(1-fx)*ft,fx*ft],axis=1)
    values=rng.normal(size=(nx*nt,8))
    local=(values[ids]*weights[...,None]).sum(axis=1)
    S=sparse.csr_matrix((weights.ravel(),(np.repeat(np.arange(n),4),ids.ravel())),shape=(n,nx*nt))
    dense=S.toarray()@values
    maxerr=float(np.max(abs(local-dense)))
    ck('four_corner_routing_equals_dense_interpolator',maxerr<1e-12,max_abs_error=maxerr,
       local_entries_per_query=4,dense_entries_per_query=nx*nt,entry_ratio=nx*nt/4)
    top=np.argsort(weights,axis=1)[:,-2:]
    chosen=np.take_along_axis(ids,top,axis=1);ww=np.take_along_axis(weights,top,axis=1)
    dropped=(values[chosen]*ww[...,None]).sum(axis=1)
    err=relative(dropped,local)
    allowedbound=np.sum(np.abs(values[ids])*weights[...,None],axis=1)-np.sum(np.abs(values[chosen])*ww[...,None],axis=1)
    ck('top2_discards_nonzero_support_and_changes_field',err>1e-3,relative_error=err)
    ck('discarded_contribution_envelope_bounds_router_error',np.all(abs(dropped-local)<=allowedbound+1e-12),
       max_bound_violation=float(np.max(abs(dropped-local)-allowedbound)))
    ck('partition_of_unity_is_preserved_by_full_route',np.max(abs(weights.sum(axis=1)-1))<1e-15)
    # Neural fields do not create new rank; known dynamics may shrink admitted class.
    J=np.array([[1.,0.],[0.,.2],[0.,0.]])
    R=np.array([[1.,1.],[0.,0.]])
    ck('composition_cannot_increase_measurement_rank',np.linalg.matrix_rank(J@R)<=np.linalg.matrix_rank(J))
    dump('algebra_and_routing_results.json',dict(checks=checks,n_checks=len(checks),scope=__doc__,
          conclusion='Support-limited routing is exact for a chosen local representation; physical-data null directions remain.'))
    print(len(checks),'checks passed',flush=True)
if __name__=='__main__':run()
