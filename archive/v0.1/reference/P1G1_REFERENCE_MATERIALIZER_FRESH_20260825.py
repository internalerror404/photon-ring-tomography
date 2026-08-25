from pathlib import Path
import hashlib

IDENT = 'spatial_channels,readout,max_order,rank,smallest_nonzero_singular_value,prior_subspace_rank,prior_subspace_smallest_singular_value\nidentical,resolved,0,48,1.0,16,0.0\nidentical,resolved,1,56,0.5488116360940261,16,0.0\nidentical,resolved,2,64,0.3011942119122019,16,0.0\nidentical,resolved,3,72,0.16529888822158642,16,0.0\nidentical,resolved,4,80,0.0907179532894124,16,0.0\nidentical,resolved,5,88,0.04978706836786391,16,0.0\nidentical,unresolved,0,48,1.0,16,0.0\nidentical,unresolved,1,48,0.558811072712042,16,0.0\nidentical,unresolved,2,48,0.6724141127590967,16,0.0\nidentical,unresolved,3,48,0.6587793721116642,16,0.0\nidentical,unresolved,4,48,0.6655791050772037,16,0.0\nidentical,unresolved,5,48,0.6647962190193994,16,0.0\ndiverse,resolved,0,48,1.0,16,0.0\ndiverse,resolved,1,96,0.2570217198630979,24,1.598505527140347e-05\ndiverse,resolved,2,144,0.0037349089769260165,24,0.00031082567711834396\ndiverse,resolved,3,168,0.003734908976926049,24,0.0015870734240465176\ndiverse,resolved,4,192,0.0037349089769260764,24,0.007460516734913701\ndiverse,resolved,5,216,0.003734908976926087,24,0.01876416259035676\ndiverse,unresolved,0,48,1.0,16,0.0\ndiverse,unresolved,1,48,0.7884469998939074,23,0.0\ndiverse,unresolved,2,48,0.7608348568118096,23,0.0\ndiverse,unresolved,3,48,0.7384929210210204,23,0.0\ndiverse,unresolved,4,48,0.7458786864722062,23,0.0\ndiverse,unresolved,5,48,0.7465699210570901,23,0.0\n'
RECON = 'relative_noise,full_space_oracle_tikhonov_error,full_space_lambda,prior_subspace_oracle_ridge_error,prior_subspace_lambda,readout\n0.0,0.4518113729771207,1e-12,5.576922946067787e-10,1e-12,resolved\n0.001,0.4521649482306849,1e-06,0.001895098018614348,1e-12,resolved\n0.003,0.4543849999219873,4.641588833612773e-06,0.0060666176426691166,1e-12,resolved\n0.01,0.46231279080880033,4.641588833612772e-05,0.01934209812143585,2.1544346900318822e-06,resolved\n0.03,0.4828659316936739,0.00046415888336127724,0.05938568100996253,2.1544346900318823e-05,resolved\n0.1,0.5595419576696903,0.004641588833612773,0.18081811578938747,0.00021544346900318777,resolved\n0.0,0.9017590530497192,1e-11,0.27745846387565626,1e-12,unresolved\n0.001,0.9017592197813366,1e-12,0.5381603890862702,2.1544346900318822e-07,unresolved\n0.003,0.9017605379543104,0.0001,0.565707998131018,1e-06,unresolved\n0.01,0.9017756753056227,0.00021544346900318777,0.6151553005282979,2.1544346900318823e-05,unresolved\n0.03,0.9019057149013299,0.0021544346900318778,0.6557162242833747,0.00021544346900318777,unresolved\n0.1,0.9033760603049785,0.021544346900318777,0.6914379244296168,0.0021544346900318778,unresolved\n'
EXPECTED = {
    "paper1_identifiability.csv": "3173f38ad56d11cdba01819d4f8a2ed33bd6a336335e208e373087e270930f49",
    "paper1_reconstruction.csv": "806b9472dac91e0e18c345aa3f682f6cc586738866ecc60612886068e07aa363",
}

out = Path(__file__).resolve().parent / "reference_results"
out.mkdir(parents=True, exist_ok=True)

for name, payload in [
    ("paper1_identifiability.csv", IDENT),
    ("paper1_reconstruction.csv", RECON),
]:
    path = out / name
    path.write_text(payload, encoding="utf-8", newline="")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED[name]:
        raise SystemExit(f"hash mismatch for {name}: {actual} != {EXPECTED[name]}")
    print(f"{actual}  {path}")
