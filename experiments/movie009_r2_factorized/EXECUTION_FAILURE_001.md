# Movie009-R2 execution failure 001 — dynamically loaded Movie007 module not registered

The first execution under actual source freeze `5ed4cd1419bc2437aaf4c55d3f9a86a7ec2eb2e5` stopped immediately while importing the authenticated Movie007 source. The loader created a module with `importlib.util.module_from_spec` but did not insert it into `sys.modules` before `exec_module`. Under Python 3.13, the `@dataclass` decorator in `movie007_run.py` therefore failed while resolving the class module namespace.

No Movie009-R2 source candidate, training/validation/test population, PCA decoder, regularization choice, neural weight, checkpoint, reconstruction, metric, or scientific endpoint was generated. The only local result file is the implementation-failure traceback.

The repair inserts the dynamically loaded module into `sys.modules` before executing it. It changes no source family, seed, physical operator, noise draw, latent rank, inverse definition, architecture, validation grid, threshold, success gate, or Paper-I state. The corrected source is syntax-checked, self-tested, re-hashed, and committed before rerun.