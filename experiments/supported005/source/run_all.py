"""Run in an unpacked SOURCE+INPUTS copy, never over completed results."""
from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parents[1]
if (root/'results/RESULTS.json').exists():raise SystemExit('Results exist; use a fresh source/input copy')
for x in ('results','figures'):(root/x).mkdir(exist_ok=True)
for name in ('experiment.py','numerical_closeout.py','box_metric.py','finalize.py'):
    subprocess.run([sys.executable,str(root/'source'/name)],cwd=root,check=True,
                   env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
