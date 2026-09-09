"""Execute in an input-populated fresh directory; refuses result overwrite.
No Internet, geodesics, physical quadratures, critical-curve roots or Paper-I data
mutation. Source-field evaluation/inversion is deliberately new Paper-II work.
"""
from pathlib import Path
import subprocess,sys,os
root=Path(__file__).resolve().parents[1]
if (root/'results/LINEAR_RESULTS.json').exists():raise SystemExit('Results exist; reproduce in fresh directory')
for d in ['results','models','logs','figures']:(root/d).mkdir(exist_ok=True)
env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
for file in ['linear_inverse.py','neural_inverse.py','summarize.py']:
    subprocess.run([sys.executable,str(root/'source'/file)],env=env,check=True,cwd=root)
