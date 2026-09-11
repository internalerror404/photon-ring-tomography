# Movie012 reimplementation failure 001 — dynamic Movie007 import was not registered

The first execution of the deposited reimplementation authenticated no scientific outcome and stopped immediately while importing the frozen Movie007 source. Under Python 3.13, the dynamically created module was not inserted into `sys.modules` before execution; the `@dataclass` machinery therefore could not resolve the module namespace and raised an `AttributeError`.

No Movie012 source candidate, source population, PCA decoder, observation PCA, validation choice, neural weight, checkpoint, reconstruction, or test endpoint was generated. The repair inserts the module into `sys.modules` before `exec_module`, matching ordinary Python import semantics. It changes no physical input, source formula, seed, population, architecture, metric, threshold, or success gate. Corrected source is re-hashed and re-frozen before rerun.
