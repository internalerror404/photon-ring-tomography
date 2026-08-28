#!/usr/bin/env python3
"""Compile the manuscript HTML to PDF and page images for visual inspection.

No LaTeX or pandoc is available in the pinned environment, so the compile step
is headless Chromium via Playwright, which is already provisioned. The point is
not typesetting quality -- it is that somebody, or something, looks at the
rendered pages before the paper is called finished. A table that overflows its
column or a heading orphaned at a page break does not show up in the markdown.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "manuscript"
HTML = OUT / "PAPER_I.html"
PDF = OUT / "PAPER_I.pdf"
SHOTS = OUT / "pages"
META = OUT / "PDF_METADATA.json"

# Short enough to sit in a header without wrapping. The full title is on the
# title page and in the PDF metadata.
RUNNING_HEAD = "Photon-Ring Retarded-Time Tomography I: The Shiva Effect"
RUNNING_AUTHORS = "Dixit &amp; Chauhan"


def main() -> int:
    from playwright.sync_api import sync_playwright

    if not HTML.exists():
        raise SystemExit("build the manuscript first")
    SHOTS.mkdir(parents=True, exist_ok=True)
    for old in SHOTS.glob("page_*.png"):
        old.unlink()

    with sync_playwright() as pw:
        # The pinned browser build in this environment does not match the
        # Playwright package's expected revision, and re-downloading browsers is
        # not permitted here, so launch the provisioned binary directly.
        exe = Path("/opt/pw-browsers/chromium")
        browser = (pw.chromium.launch(executable_path=str(exe)) if exe.exists()
                   else pw.chromium.launch())
        pg = browser.new_page(viewport={"width": 1100, "height": 1400},
                              device_scale_factor=2)
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.emulate_media(media="print")
        # A running header and a page number. Chromium ignores CSS @page
        # margin boxes, so the templates are the only route; they are rendered
        # at a fixed 9pt independent of the page's own styles, and the title
        # page suppresses its own header via display_header_footer's first-page
        # behaviour being unavailable -- so the header is deliberately short
        # enough to sit above a title page without looking wrong.
        head = (
            "<div style=\"font:400 8pt -apple-system,Segoe UI,Roboto,sans-serif;"
            "color:#666;width:100%;padding:0 16mm;display:flex;"
            "justify-content:space-between\">"
            f"<span>{RUNNING_HEAD}</span><span>{RUNNING_AUTHORS}</span></div>")
        foot = (
            "<div style=\"font:400 8pt -apple-system,Segoe UI,Roboto,sans-serif;"
            "color:#666;width:100%;padding:0 16mm;text-align:center\">"
            "<span class=\"pageNumber\"></span> of "
            "<span class=\"totalPages\"></span></div>")
        pg.pdf(path=str(PDF), format="A4", print_background=True,
               display_header_footer=True,
               header_template=head, footer_template=foot,
               margin={"top": "20mm", "bottom": "20mm",
                       "left": "16mm", "right": "16mm"})

        # page images for inspection: screen media, scrolled in viewport steps
        pg.emulate_media(media="screen")
        height = pg.evaluate("document.body.scrollHeight")
        step = 1400
        n = 0
        for y in range(0, height, step):
            pg.evaluate(f"window.scrollTo(0, {y})")
            pg.wait_for_timeout(60)
            pg.screenshot(path=str(SHOTS / f"page_{n:02d}.png"))
            n += 1

        # anything overflowing its container horizontally is a layout bug
        overflow = pg.evaluate("""() => {
            const bad = [];
            document.querySelectorAll('table, pre, .tablewrap').forEach(el => {
                if (el.scrollWidth > el.clientWidth + 2) {
                    const h = el.closest('div,section,main');
                    bad.push({tag: el.tagName,
                              w: el.scrollWidth, c: el.clientWidth,
                              text: (el.innerText || '').slice(0, 60)});
                }
            });
            return bad;
        }""")
        doc_w = pg.evaluate("document.documentElement.scrollWidth")
        view_w = pg.evaluate("document.documentElement.clientWidth")
        browser.close()

    print(f"wrote {PDF.relative_to(ROOT)} ({PDF.stat().st_size // 1024} KB)")
    print(f"wrote {n} page images under {SHOTS.relative_to(ROOT)}")
    print(f"document width {doc_w}px against viewport {view_w}px")
    if doc_w > view_w + 2:
        print("  WARNING: the page scrolls horizontally")
    if overflow:
        print(f"  {len(overflow)} element(s) overflow their container "
              "(scroll inside their own box, which is intended for wide tables):")
        for o in overflow[:8]:
            print(f"    {o['tag']} {o['w']}>{o['c']} :: "
                  f"{o['text'].replace(chr(10), ' ')}")
    else:
        print("  no element overflows its container")

    # The metadata stamp lives in its own script because it needs pypdf, which
    # the pinned analysis environment does not carry. Run it with whichever
    # interpreter can import it rather than leaving the PDF unattributed.
    stamped = False
    for exe in (sys.executable, "python3", "/usr/bin/python3"):
        r = subprocess.run([exe, str(ROOT / "scripts" / "stamp_pdf_metadata.py")],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            print("  " + r.stdout.strip().replace("\n", "\n  "))
            stamped = True
            break
    if not stamped:
        print("  WARNING: PDF metadata not stamped; no interpreter here has "
              "pypdf. The PDF carries no author or subject.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
