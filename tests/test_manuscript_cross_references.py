"""Every "section N" in the paper must point at a section that exists.

Section numbers were hardcoded in both the headings and the prose, so inserting
a section in the middle silently repointed eight references at the wrong
sections. The numbering is now derived from one ordered list; this checks the
derived numbers and the references agree in the rendered document, which is the
only place the reader sees them.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "artifacts" / "manuscript" / "PAPER_I.md"

HEADING = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)?)[.\s]")
REFERENCE = re.compile(r"[Ss]ection\s+(\d+(?:\.\d+)?)")


def _paper():
    if not PAPER.exists():
        pytest.skip("manuscript not built in this tree")
    return PAPER.read_text()


def test_every_section_reference_resolves():
    text = _paper()
    have = {m.group(1) for line in text.splitlines()
            if (m := HEADING.match(line))}
    assert have, "no numbered headings found; the parser is wrong, not the paper"
    missing = sorted({n for n in REFERENCE.findall(text) if n not in have})
    assert not missing, (f"references to sections that do not exist: {missing}; "
                         f"sections present: {sorted(have)}")


def test_section_numbers_are_contiguous_and_unique():
    text = _paper()
    tops = [m.group(1) for line in text.splitlines()
            if (m := HEADING.match(line)) and "." not in m.group(1)]
    assert tops == sorted(set(tops), key=int) == [str(i) for i in
                                                  range(1, len(tops) + 1)], tops


def test_the_numbering_is_derived_not_typed():
    """A heading with a literal number in the source would drift again."""
    src = (ROOT / "src" / "phrt" / "manuscript" / "sections.py").read_text()
    literal = [ln for ln in src.splitlines()
               if re.match(r"^#{2,3}\s+\d", ln)]
    assert not literal, literal
