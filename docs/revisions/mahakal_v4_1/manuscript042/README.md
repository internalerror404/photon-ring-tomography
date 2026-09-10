# Mahakal manuscript revision 042

Complete constructive-feedback revision of the attached 041 paper. The title, authors, mathematical results, experimental numbers, and negative endpoints are preserved. The writing foregrounds source-history identifiability, adds an evidence overview, updates the nearest related work, and makes the future validation path specific to the physical claims.

## Files

- `main.tex`, `sections/`, `references.tex`: complete modular LaTeX source.
- `Photon_Ring_Retarded_Time_Tomography_042.tex`: self-contained source in the downloadable package.
- `Photon_Ring_Retarded_Time_Tomography_042.pdf`: rendered paper in the downloadable package.
- `FEEDBACK_INTEGRATION_042.md`: feedback-to-edit map and remaining limitations.
- `VERIFICATION_042.json`: input identity, original-block preservation, compile/render checks.
- `SOURCE_MAP_041.json`: inherited numerical-source identity index; no numerical results were regenerated.
- `LITERATURE_ADDITIONS_042.json`: the two new primary references and the scope checked.
- `CHANGES_041_TO_042.diff`: complete text-source comparison in the downloadable package.

Compile from this directory with:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The four existing figures are typeset from their unchanged PGFPlots source. No geodesics, inference experiments, external figure downloads, or source-data regeneration are required to compile the paper. Standard LaTeX packages and fonts must be installed; font files are not redistributed.

The output remains an author-review manuscript with explicit scientific limitations, not evidence that a journal has accepted the paper or that its full physical imaging operator is qualified. Earlier manuscript and experiment files are not overwritten.
