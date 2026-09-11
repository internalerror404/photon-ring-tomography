# Movie007 execution failure 001

The first actual execution completed and saved all q8/q12 Kerr physical tuples, both source-linear operators, the support weights, and the independent ODE gate. It then stopped before generating any validation or test source because the tensor-projection `einsum` returned the quadrature-time index instead of the temporal-basis index (`iat` rather than `iak`), producing 1,400 values where 595 were required.

No source bank, regularization choice, test reconstruction, movie span, or success-gate outcome existed at failure. The physical cache is retained byte-for-byte and will be reused; the limited physical calls are not repeated. The corrected source changes only the projection output index and adds a cache-resume path. Thresholds, source definitions, seeds, physical geometry, and registered endpoints are unchanged.
