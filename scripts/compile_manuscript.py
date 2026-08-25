#!/usr/bin/env python3
"""Compile the manuscript HTML to PDF and page images for visual inspection.

No LaTeX or pandoc is available in the pinned environment, so the compile step
is headless Chromium via Playwright, which is already provisioned. The point is
not typesetting quality -- it is that somebody, or something, looks at the
rendered pages before the paper is called finished. A table that overflows its
column or a heading orphaned at a page break does not show up in the markdown.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "manuscript"
HTML = OUT / "PAPER_I.html"
PDF = OUT / "PAPER_I.pdf"
SHOTS = OUT / "pages"


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
        pg.pdf(path=str(PDF), format="A4", print_background=True,
               margin={"top": "18mm", "bottom": "18mm",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
