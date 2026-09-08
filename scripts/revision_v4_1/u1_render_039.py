#!/usr/bin/env python3
"""Ruling 039: render the publication candidate to HTML and PDF.

Document work only. Nothing numerical is computed: the markdown source is
converted with the repository's own renderer, display equations written as
``$$ ... $$`` lines are promoted to typeset blocks, and headless Chromium
prints the result. The shared renderer is imported, not modified, so earlier
builds remain reproducible.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.manuscript.render import CSS, to_html          # noqa: E402

DOC = ROOT / "docs/revisions/mahakal_v4_1/manuscript039"
STEM = "Photon_Ring_Retarded_Time_Tomography_Candidate_039"
CHROME = "/opt/pw-browsers/chromium"

EXTRA_CSS = """
.eq{margin:.85rem 0 1rem;padding:.15rem 0 .15rem 1.6rem;
font:1.02em/1.75 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
font-style:italic;letter-spacing:.01em;color:var(--ink)}
.eq .sub{font-style:normal}
figure figcaption strong{color:var(--ink)}
h2+p em:first-child{color:var(--muted)}
@media print{.eq{page-break-inside:avoid}}
"""

_EQ_BLOCK = re.compile(r"^<p>(\$\$.*?\$\$)</p>$", re.M | re.S)
_EQ_ONE = re.compile(r"\$\$(.*?)\$\$", re.S)


def promote_equations(html: str) -> tuple[str, int]:
    """Turn ``<p>$$ ... $$</p>`` paragraphs into display-equation blocks.

    The repository renderer has no math mode and adding one would mean
    vendoring a typesetting dependency into a provenance-tracked tree. The
    equations are written in Unicode in the source, so all this needs to do is
    set them apart from running prose.

    Consecutive source lines arrive here as one paragraph, so a block holding
    several ``$$``-delimited equations is split back into one line each rather
    than left with its delimiters showing.
    """
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        eqs = [e.strip() for e in _EQ_ONE.findall(m.group(1))]
        n += len(eqs)
        return ('<div class="eq">'
                + "<br>".join(eqs) + "</div>")

    return _EQ_BLOCK.sub(sub, html), n


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    t0 = time.time()
    md = (DOC / f"{STEM}.md").read_text()
    body, n_eq = promote_equations(to_html(md))
    i = body.find("<h2")
    body = f'<section class="titlepage">{body[:i]}</section>{body[i:]}'
    title = "Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon"
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title>"
        "<meta name='author' content='Hina Dixit and Abhinav Chauhan'>"
        "<meta name='description' content='Publication candidate 039 - "
        "historical reach, supported source dimension and held-out recovery "
        "in a declared finite photon-ring model.'>"
        f"<style>{CSS}{EXTRA_CSS}</style></head>"
        f"<body><main>{body}</main></body></html>")
    hp = DOC / f"{STEM}.html"
    hp.write_text(html)

    pdf = DOC / f"{STEM}.pdf"
    if pdf.exists():
        pdf.unlink()
    r = subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--allow-file-access-from-files",
         "--virtual-time-budget=20000", f"--print-to-pdf={pdf}", hp.as_uri()],
        capture_output=True, text=True, cwd=DOC, timeout=300)
    if not pdf.exists():
        print(r.stderr[-2000:], file=sys.stderr)
        return 1

    figs = sorted((DOC / "figures").glob("*.png"))
    out = {
        "html": {"path": str(hp.relative_to(ROOT)), "sha256": sha(hp),
                 "bytes": hp.stat().st_size},
        "pdf": {"path": str(pdf.relative_to(ROOT)), "sha256": sha(pdf),
                "bytes": pdf.stat().st_size},
        "markdown": {"path": str((DOC / f'{STEM}.md').relative_to(ROOT)),
                     "sha256": sha(DOC / f"{STEM}.md")},
        "display_equations": n_eq,
        "figures_embedded": [f.name for f in figs],
        "renderer": "src/phrt/manuscript/render.py (imported unmodified)",
        "pdf_engine": "chromium headless print-to-pdf",
        "runtime_seconds": time.time() - t0,
    }
    print(json.dumps(out, indent=2))
    (DOC / "RENDER_039.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
