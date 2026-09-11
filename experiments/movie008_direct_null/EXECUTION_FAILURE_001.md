# Movie008 execution failure 001 — scalar implementation timeout

The first post-mode-bank execution was terminated by the local 600-second command limit. The run had generated fresh backgrounds, target combinations, noise and some estimates only in process memory, but it wrote none of them: no source bank, observation, reconstruction, metric, summary or movie endpoint exists on disk. The only persisted result files remain the separately frozen `MODE_BANK.json` and `MODE_BANK.npz`.

The log contains one NumPy warning from `np.where` evaluating an unused zero-denominator correlation branch. No numerical failure or endpoint was emitted. No ray, Kerr integral, ODE trajectory, hull/root or Paper-I unit was used.

The bottleneck is operational: the scalar loop repeatedly evaluates 30,720-pixel movie frames and applies already-factorized linear estimators one case at a time. A successor implementation may batch fixed linear solves and frame evaluations, provided it leaves the authenticated inputs, frozen mode bank, source/noise seeds, target/nuisance spaces, estimators, amplitudes, thresholds and endpoints unchanged, and validates batched/scalar equivalence on a fixed fixture before fresh completion.
