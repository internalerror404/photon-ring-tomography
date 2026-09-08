# Inverse model selection — before heldout test fits

Both physics penalties selected lambda=0.03 from the registered common grid [0.03,0.1,0.3,1.0], using the mean heldout-observation chi-square across the two validation histories. Data-only lambda is0. No ground-truth source reconstruction score was used to select either weight. This is the lower edge of the registered grid, which limits claims about an optimum; the grid will not be extended after looking at test results.

Local selected_lambdas.json SHA256: 80ee5429860d9875ba656d719fd57e4d9197af9f785cedfb26a422cf1c74a3d1.

The six test histories, three noise/initialization seeds, all-order/direct comparisons, training duration and architecture remain as registered. No test fit or test-source-error outcome has been inspected at this freeze. The unrelated physical forward calibration is already running under its registered specification; its outputs do not select inverse hyperparameters. These two experiments are intentionally not claimed to be one validated system.
