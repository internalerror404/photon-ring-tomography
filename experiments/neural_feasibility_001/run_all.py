"""Run the fixed manufactured feasibility suite in a NEW directory.
Usage: python run_all.py
Requires numpy, scipy, torch, pandas; CPU float64; no internet or external data.
Refuses overwriting results. Run in an unpacked source-only copy for reproduction.
"""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
if (root/'inverse_results.json').exists():
    raise SystemExit('Results already exist. Copy source files and protocol.json to a NEW directory before running.')
for name in ['inverse.py','forward.py','operator_learning.py','algebra_and_routing.py','classical_crosscheck.py','verify.py','summarize.py']:
    print('RUN',name,flush=True)
    subprocess.run([sys.executable,str(root/name)],cwd=root,check=True)
