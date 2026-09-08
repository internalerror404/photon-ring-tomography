"""Reproduce in a fresh source directory. No API calls or external data needed.
Composed after individually executed phases; not separately rerun end-to-end.
A fresh run does NOT repeat the historical failed JSON export, hence its ledger
has 192 fewer attempted rays than the first recorded experiment.
"""
from pathlib import Path
import subprocess,os,sys
ROOT=Path(__file__).resolve().parent.parent
results=ROOT/'results';results.mkdir(exist_ok=True)
if (results/'forward_validation.json').exists():raise SystemExit('Use a NEW directory; no overwriting archived results')
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
for name,args in [('geodesics003.py',[]),('build003.py',[]),('inverse003.py',[]),('inverse003.py',['--classical']),('diagnostics003.py',[]),('diagnostics003.py',['--inverse']),('readout_diagnostic003.py',[]),('verify003.py',[])]:
    subprocess.run([sys.executable,str(ROOT/'source'/name),*args],cwd=ROOT,env=env,check=True)
