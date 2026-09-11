# Movie011 execution amendment 001 — bounded fitted-field readback

Before generating any Movie011 source or neural weight, bound the direct continuous-decoder q8/q12 readback to the first four test pairs in each family, both siblings, and the first paired noise draw: 32 fields per arm per neural seed.

The analytic clean-truth q8/q12 gate still runs on every validation and test sibling. The fitted subset is selected by pair index before source generation, spans all four families including the held-out radial plume, and is identical across seeds and arms. The registered numerical thresholds remain `5e-4` relative and `0.1` whitened. This amendment controls CPU cost; it does not select fields by reconstruction quality or change any scientific endpoint.
