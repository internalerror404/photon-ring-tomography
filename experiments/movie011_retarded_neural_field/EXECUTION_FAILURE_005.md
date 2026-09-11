# Movie011 execution failure 005 — closeout predicate ordering

The deterministic candidate-ledger closeout stopped after 3.25 seconds because candidates rejected before positivity evaluation now correctly carry `minimum_emissivity = null`, but the Boolean expression compared that null value with 0.35 before checking the already-failed activity predicate.

The frozen 157 MB population and source-spec files were only read; no byte was changed. No neural model, checkpoint, reconstruction, or endpoint exists. The repair changes the Boolean evaluation order to test `active >= 9` first and to require a non-null minimum only for activity-eligible candidates. It is logically identical to the admission rule used to create the preserved population and affects reporting/replay only.
