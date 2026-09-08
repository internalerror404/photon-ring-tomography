"""Aggregate executed results, retaining all seeds and explicit scope."""
from common import *
import pandas as pd

def run():
    inv=pd.DataFrame(json.loads((ROOT/'inverse_results.json').read_text())['results'])
    clas=pd.DataFrame(json.loads((ROOT/'classical_results.json').read_text())['results'])
    fwd=pd.DataFrame(json.loads((ROOT/'forward_results.json').read_text())['results'])
    op=pd.DataFrame(json.loads((ROOT/'operator_results.json').read_text())['results'])
    numeric=['old_contrast_relative_error','full_contrast_relative_error','clean_training_chi2','heldout_observation_relative_error','pde_rms','negative_fraction','seconds','loss']
    invsmall=inv[[c for c in ['seed','model','source','acquisition']+numeric if c in inv.columns]]
    invsmall.to_csv(ROOT/'inverse_per_seed.csv',index=False)
    clas.to_csv(ROOT/'classical_per_seed.csv',index=False)
    fwd.drop(columns=['adam_trace'],errors='ignore').to_csv(ROOT/'forward_per_seed.csv',index=False)
    op.drop(columns=['adam_trace'],errors='ignore').to_csv(ROOT/'operator_per_seed.csv',index=False)
    def aggregate(df,cols,measure):
        v=df.groupby(cols)[measure].agg(['median','min','max']).reset_index()
        return v.to_dict(orient='records')
    summary=dict(
        scope='Manufactured dimensionless surrogate and tomography tests; NOT a validated Kerr renderer or production Kiran/FNO/NeRF benchmark.',
        neural_fits=42,seeds=CFG['seeds'],
        inverse=aggregate(inv,['source','acquisition','model'],'old_contrast_relative_error'),
        classical=aggregate(clas,['source','acquisition','model'],'old_contrast_relative_error'),
        forward=aggregate(fwd,['model'],'whitened_detector_relative_error'),
        operator=aggregate(op,['model'],'median_heldout_field_relative_error'),
        algebra_and_routing=json.loads((ROOT/'algebra_and_routing_results.json').read_text())['checks'],
        verification=json.loads((ROOT/'verification.json').read_text()),
        protocol_qualifications=[
            'Main neural protocol written locally before training, not externally sealed.',
            'Analytic residual comparator in forward.py defined before forward training; not listed separately in initial protocol.',
            'Classical inverse controls added after neural screen as disclosed development crosschecks; alpha by training-data GCV only.',
            'Neural networks use float64 on CPU, not the production ray environment.',
            'No inference about actual Mahakal quadrature or observational feasibility follows.'])
    dump('summary.json',summary)
    print('Summary and four per-seed CSVs saved')
if __name__=='__main__':run()
