# Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon

Hina Dixit and Abhinav Chauhan

## Manuscript revision 043

Revision 042 plus the order-attribution result, promoted into the abstract,
the nuisance-adjusted results section, the conclusion and a new appendix. See
`CHANGES_043.md` for the exact additions and `VERIFICATION_043.json` for what
was and was not checked.

Compile the modular source from this directory:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

**No PDF is shipped with this revision.** No TeX engine was available where the
source was edited, so the document was not compiled and no rendered page was
inspected. The source passed a structural check only: balanced environments,
no dangling cross-references, and correct column counts in the three new
tables. A compile and a page inspection are still required before this
revision is posted anywhere.

The four scientific figures remain encoded in the LaTeX source with PGFPlots;
no external images or repository runners are required to typeset them. No
result, source class, estimator, truth bank or physical query was changed or
recomputed for this revision. Earlier manuscripts and numerical archives are
not overwritten.
