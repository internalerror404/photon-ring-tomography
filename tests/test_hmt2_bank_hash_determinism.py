"""Bank hashes must survive crossing a process boundary.

Stage A commits hashes in one interpreter and stage B checks them in another.
Anything salted per process -- Python's str hash above all -- silently breaks
that, and the failure looks like a tampered bank rather than a bug.
"""
import subprocess
import sys
import tokenize
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


def _bare_hash_calls(path):
    """Lines where the builtin ``hash`` is *called*, by tokens not by grep.

    Tokenizing rather than matching text is what makes this usable: a string
    literal and a comment are their own token kinds, so prose that mentions
    ``hash()`` -- of which this campaign's records contain a good deal -- is
    skipped structurally instead of by counting quotes on a line, which a
    triple-quoted block defeats.
    """
    with path.open() as fh:
        toks = list(tokenize.generate_tokens(fh.readline))
    skip = (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT,
            tokenize.DEDENT)
    out = []
    for i, t in enumerate(toks):
        if t.type != tokenize.NAME or t.string != "hash":
            continue
        prev = toks[i - 1] if i else None
        nxt = next((x for x in toks[i + 1:] if x.type not in skip), None)
        if prev and prev.type == tokenize.OP and prev.string == ".":
            continue              # hashlib.sha256(...).hash(...) and friends
        if nxt and nxt.type == tokenize.OP and nxt.string == "(":
            out.append(f"{path.name}:{t.start[0]}: {t.line.strip()}")
    return out


def test_no_script_calls_the_builtin_hash():
    """The check that would have caught this, run over the whole tree.

    This bug has now appeared three times in the campaign: in the R0 null-pair
    seed, in HMT-1's off-manifold seeds, and in the HMT-2 sealed bank's label
    hash. Twice it was found by reasoning about a symptom. A cheap automated
    check is worth more than remembering, so here it is.

    Only the bare builtin is flagged: ``hashlib`` helpers and attribute calls
    are fine.
    """
    paths = (sorted((ROOT / "scripts").glob("*.py"))
             + sorted((ROOT / "src").rglob("*.py"))
             + sorted((ROOT / "tests").glob("*.py")))
    bad = [hit for p in paths for hit in _bare_hash_calls(p)]
    assert not bad, bad


def test_the_csv_twin_is_capped():
    """A convenience mirror must not make an artifact unpushable."""
    import pandas as pd
    from phrt.io.tables import CSV_TWIN_MAX_ROWS, write_table
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        small = [{"a": i} for i in range(10)]
        write_table(small, "small", out_dir=d)
        assert (Path(d) / "small.csv").exists()

        big = [{"a": i} for i in range(CSV_TWIN_MAX_ROWS + 1)]
        write_table(big, "big", out_dir=d)
        assert (Path(d) / "big.parquet").exists()
        assert not (Path(d) / "big.csv").exists()
        assert (Path(d) / "big.csv.skipped").exists()
