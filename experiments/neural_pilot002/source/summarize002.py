"""Derived tables from saved results; no model fitting or physical queries."""
from support import *
import pandas as pd,hashlib,platform

def run():
    inv=json.loads((OUT/'inverse_test.json').read_text());fd=json.loads((OUT/'forward_results.json').read_text());val=json.loads((OUT/'inverse_validation.json').read_text());f=pd.DataFrame(inv['rows']);fw=pd.DataFrame(fd['rows'])
    f.to_csv(OUT/'inverse_per_seed.csv',index=False);fw.drop(columns=['per_channel_relative_error']).to_csv(OUT/'forward_per_seed.csv',index=False)
    pd.DataFrame(val['rows']).drop(columns=['trace']).to_csv(OUT/'validation_per_candidate.csv',index=False)
    gs=f.groupby(['source','acquisition','method']).old_contrast_error.agg(['count','median','min','max']).reset_index()
    gs.to_csv(OUT/'inverse_summary.csv',index=False)
    gf=fw.groupby('model').max_channel_detector_relative_error.agg(['count','median','min','max']).reset_index();gf.to_csv(OUT/'forward_summary.csv',index=False)
    pivot=f[f.acquisition=='all_orders'].pivot(index=['background','seed','source'],columns='method',values='old_contrast_error')
    pairs=[]
    for typ in ['matched','single','double']:
        v=pivot.xs(typ,level='source');diff=(v.quadratic-v.innovation)/v.quadratic
        pairs.append(dict(source=typ,median_paired_relative_reduction=float(diff.median()),wins=int(sum(diff>0)),count=len(diff)))
    selected=json.loads((OUT/'selected_lambdas.json').read_text())
    verification=json.loads((OUT/'verification002.json').read_text())
    summ=dict(scope='Registered development pilot: real Schwarzschild ray-primitive calibration plus separate manufactured inverse tests, not an integrated validated historical imaging system',inverse=gs.to_dict(orient='records'),forward=gf.to_dict(orient='records'),innovation_vs_quadratic=pairs,selected_lambdas=selected,neural_fits=99,classical_inverse_fits=24,physical_ledger=json.loads((OUT/'physical_final_ledger.json').read_text()),twin_checks=inv['twin_checks'],verification_pass=verification['all_checks_pass'],reference_check=json.loads((OUT/'physical_reference_check.json').read_text()),inverse_renderer_max_relative_8_48=max(v['relative_q8_q48'] for v in verification['learned_field_quadrature']),inverse_truth_max_absolute_48_96=max(v['max_abs'] for v in verification['source_truth_quadrature']),physical_response_reference_max_24_48=max(fd['quadrature_24_vs48_perchannel']),Paper_I_unchanged=True)
    save('summary002.json',summ)
    return summ
if __name__=='__main__':run()
