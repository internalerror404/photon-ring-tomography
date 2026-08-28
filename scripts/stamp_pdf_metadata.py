#!/usr/bin/env python3
"""Stamp the document metadata onto the compiled PDF.

Chromium's print-to-PDF copies the HTML ``<title>`` into the PDF and nothing
else -- no author, no subject, no keywords -- so a reader who opens the file in
anything that shows document properties sees a paper by "Chromium". The fields
are written by ``scripts/build_manuscript.py`` into PDF_METADATA.json and
applied here, after compilation, so the source of truth stays with the builder.

Runs under whichever interpreter has ``pypdf``; the pinned analysis environment
deliberately carries no document dependencies, and stamping a PDF touches no
number, so this is kept out of it rather than added to it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "manuscript"
PDF = OUT / "PAPER_I.pdf"
META = OUT / "PDF_METADATA.json"


def main() -> int:
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        raise SystemExit(
            "pypdf is not importable by this interpreter. Run this script with "
            "one that has it; the metadata stamp is required by "
            "PAPER_I_EDITORIAL_RULING_022 item 6 and is not optional.")

    if not PDF.exists():
        raise SystemExit("compile the manuscript first")
    meta = json.loads(META.read_text())

    reader = PdfReader(str(PDF))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    # Dated from the canonical freeze, not from the clock: stamping "now"
    # would make the PDF differ on every rebuild and churn the source bundle
    # that carries it, for a field nobody reads as a wall-clock time.
    fz = json.loads((ROOT / "artifacts"
                     / "CANONICAL_ARTIFACT_FREEZE_V2.json").read_text())
    stamp = "D:" + fz["created_utc"].replace("-", "").replace(":", "").replace(
        "T", "").replace("Z", "") + "Z"
    writer.add_metadata({
        "/Title": meta["title"],
        "/Author": meta["author"],
        "/Subject": meta["subject"],
        "/Keywords": meta["keywords"],
        "/Creator": "scripts/build_manuscript.py",
        "/Producer": "scripts/compile_manuscript.py + scripts/stamp_pdf_metadata.py",
        "/CreationDate": stamp,
        "/ModDate": stamp,
    })
    tmp = PDF.with_suffix(".pdf.tmp")
    with tmp.open("wb") as fh:
        writer.write(fh)
    tmp.replace(PDF)

    back = PdfReader(str(PDF)).metadata
    for key in ("/Title", "/Author", "/Subject", "/Keywords"):
        if not back.get(key):
            raise SystemExit(f"metadata did not survive the write: {key}")
    print(f"stamped {PDF.relative_to(ROOT)}")
    print(f"  title  {back['/Title'][:70]}...")
    print(f"  author {back['/Author']}")
    print(f"  {len(PdfReader(str(PDF)).pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
