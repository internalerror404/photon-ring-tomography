"""The pin has to take effect, and a failed interrogation must not read as a pass."""
import subprocess
import sys

import pytest

from phrt.numerics import (PINNED_ENV, already_imported, environment_as_set,
                           pin, record, require_single_threaded, threadpool_state)

AART = "/tmp/aartvenv/bin/python"


def test_declared_variables_are_the_ruled_set():
    assert set(PINNED_ENV) == {
        "PYTHONHASHSEED", "OMP_NUM_THREADS", "OMP_DYNAMIC", "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS"}
    assert PINNED_ENV["OMP_DYNAMIC"] == "FALSE"
    assert all(v == "1" for k, v in PINNED_ENV.items()
               if k.endswith(("_THREADS", "_MAXIMUM_THREADS")))


def test_pin_refuses_once_numpy_is_loaded():
    import numpy  # noqa: F401  -- the point of the test is that this happened
    assert "numpy" in already_imported()
    with pytest.raises(RuntimeError, match="after numpy"):
        pin()


def test_pin_non_strict_still_sets_the_variables():
    pin(strict=False)
    assert environment_as_set() == PINNED_ENV


def test_threadpool_state_reports_pools_not_an_empty_list():
    import numpy  # noqa: F401  -- pools exist only once the BLAS is loaded
    numpy.linalg.svd(numpy.eye(4), compute_uv=False)
    pools = threadpool_state()
    if pools and "unavailable" in pools[0]:
        pytest.skip("threadpoolctl absent under this interpreter")
    assert pools, "no pool reported; an empty list must not read as serial"
    assert all("unavailable" not in p for p in pools)


def test_pinned_subprocess_is_single_threaded():
    code = ("import sys; sys.path.insert(0, 'src');"
            "from phrt.numerics import pin, require_single_threaded;"
            "pin(); import numpy;"
            "r = require_single_threaded();"
            "print(r['n_pools'], r['all_single_threaded'])")
    out = subprocess.run([AART, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    n, ok = out.stdout.split()
    assert int(n) >= 1 and ok == "True"


def test_unpinned_subprocess_is_refused():
    code = ("import sys, os; sys.path.insert(0, 'src');"
            "[os.environ.pop(k, None) for k in "
            "('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')];"
            "import numpy;"
            "from phrt.numerics import require_single_threaded;"
            "require_single_threaded()")
    env = {k: v for k, v in __import__("os").environ.items()
           if k not in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")}
    out = subprocess.run([AART, "-c", code], capture_output=True, text=True, env=env)
    assert out.returncode != 0
    assert "not pinned" in (out.stdout + out.stderr)


def test_record_is_complete():
    r = record()
    for k in ("pinned_environment", "declared_pin", "threadpool_state",
              "all_pools_single_threaded"):
        assert k in r
