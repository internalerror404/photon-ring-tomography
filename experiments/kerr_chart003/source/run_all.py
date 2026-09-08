"""Reproduce a fresh registered numerical run, not geometry discovery.
Copy source/ and protocol.json into an empty writable directory, then:
OPENBLAS_NUM_THREADS=1 python source/run_all.py
The local execution included a timeout recovery; an uninterrupted run does not
need resume_training.py and produces the same fixed-seed candidate definitions.
"""
from pathlib import Path
import os,sys,subprocess
root=Path(__file__).resolve().parents[1]
if (root/'results/training.json').exists():raise SystemExit('Refuse overwrite: use an empty output copy')
for d in ('models','results','attempts','figures'):(root/d).mkdir(exist_ok=True)
for s in ('experiment.py','evaluate.py','closeout.py','package_results.py'):
    subprocess.run([sys.executable,str(root/'source'/s)],cwd=root,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},check=True)
