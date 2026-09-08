"""Run the pilot in a new directory. No internet, external data or GPU required.
Set OPENBLAS_NUM_THREADS=1 before execution for consistent CPU use.
This is the final source reproducer; original execution and registration phases
are documented separately. It refuses to overwrite an existing results folder.
"""
from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parents[1]
if (r/'results').exists() and any((r/'results').iterdir()):
    raise SystemExit('Refusing to overwrite results. Use a fresh source-package directory.')
sys.path.insert(0,str(r/'source'))
from physical_kernel import radial_quad, orbit_ode
import numpy as np
for d in [np.exp(-5),.03,.1,.5,2.]:
    radial_quad(3+d); orbit_ode(3+d)
for cmd in [('forward002.py',),('inverse002.py','validation'),('inverse002.py','test'),('verify002.py',),('summarize002.py',)]:
    subprocess.run([sys.executable,str(r/'source'/cmd[0]),*cmd[1:]],cwd=r,check=True)
