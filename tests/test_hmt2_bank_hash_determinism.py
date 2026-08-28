"""Bank hashes must survive crossing a process boundary.

Stage A commits hashes in one interpreter and stage B checks them in another.
Anything salted per process -- Python's str hash above all -- silently breaks
that, and the failure looks like a tampered bank rather than a bug.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SNIPPET = """
import hashlib, sys
sys.path.insert(0, {src!r})
labels = ["SINGLE_RESOLVED", "BLENDED", "DEAD", "MULTI_RESOLVED"]
print(hashlib.sha256("|".join(labels).encode()).hexdigest())
"""


def test_str_hash_is_salted_so_it_may_not_be_used_for_artifact_hashes():
    """The property that makes hash() unusable here, asserted not assumed."""
    outs = {subprocess.run([sys.executable, "-c", 'print(hash("SINGLE_RESOLVED"))'],
                           capture_output=True, text=True).stdout.strip()
            for _ in range(6)}
    assert len(outs) > 1, ("hash(str) looked stable across processes; if "
                           "PYTHONHASHSEED is fixed in this environment the "
                           "bug it caused would hide rather than disappear")


def test_the_label_hash_is_stable_across_processes():
    code = SNIPPET.format(src=str(ROOT / "src"))
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True).stdout.strip() for _ in range(3)}
    assert len(outs) == 1 and next(iter(outs))


BARE_HASH = re.compile(r"(?<![A-Za-z0-9_.])hash\s*\(")


def test_no_script_calls_the_builtin_hash():
    """A grep is crude, and it is the check that would have caught this.

    This bug has now appeared three times in the campaign: in the R0 null-pair
    seed, in HMT-1's off-manifold seeds, and in the HMT-2 sealed bank's label
    hash. Twice it was found by reasoning about a symptom. A cheap automated
    check is worth more than remembering, so here it is.

    Only the bare builtin is flagged: sha256 helpers and attribute calls are
    fine, and a line whose match sits inside a string literal is prose.
    """
    bad = []
    for path in sorted((ROOT / "scripts").glob("*.py")):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#")[0]
            m = BARE_HASH.search(code)
            if not m:
                continue
            before = code[:m.start()]
            if before.count('"') % 2 or before.count("'") % 2:
                continue          # inside a string literal: prose, not a call
            bad.append(f"{path.name}:{n}: {line.strip()}")
    assert not bad, bad
