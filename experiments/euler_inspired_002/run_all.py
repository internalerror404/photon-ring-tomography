"""Reproduce in a new directory. Existing numerical outputs are not overwritten."""
from pathlib import Path
import os,subprocess,sys
root=Path(__file__).resolve().parent
if (root/'neural_results.json').exists():raise SystemExit('Copy source files and protocol.json into a new directory before running.')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
for filename in ['train.py','certify.py','phase_pair_readback.py','summarize.py']:
 subprocess.run([sys.executable,str(root/filename)],cwd=root,env=env,check=True)
