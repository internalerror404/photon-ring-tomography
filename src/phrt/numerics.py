"""Pin the numerical environment, and refuse to run if the pin did not take.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 5 and 6.

Stage 1 produced identical scientific conclusions on two executions and
different last bits, because the BLAS thread count was neither pinned nor
recorded. A multithreaded reduction sums partial results in whatever order the
pool happens to finish in, so the smallest singular value of a matrix with
condition number 1e10 can move by a part in 1e6 between runs while every rank
and nullity stays fixed. That is invisible to a gate and fatal to a
reproducibility claim.

Two things follow, and this module does both.

**Pin before NumPy loads.** Every one of these variables is read once, when the
threading runtime initialises, which happens when NumPy pulls in its BLAS. Set
after that and it is decoration: ``threadpool_info`` will still report four
threads. So ``pin()`` refuses to be a no-op -- it raises if NumPy is already in
``sys.modules``, rather than letting a caller believe a late pin worked.

**Assert, do not assume.** ``require_single_threaded()`` interrogates the
runtime that actually loaded and aborts unless every active pool reports one
thread. An environment variable that was set is not evidence; a pool that
reports one thread is.

This module must not import NumPy at module scope, directly or transitively,
or importing it would itself be the event it exists to precede.
"""
from __future__ import annotations

import os
import sys

PINNED_ENV: dict[str, str] = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OMP_DYNAMIC": "FALSE",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}

_NUMERIC_MODULES = ("numpy", "scipy", "pandas", "sklearn")


def already_imported() -> list[str]:
    """Numeric modules present in ``sys.modules``, i.e. too late to pin."""
    return [m for m in _NUMERIC_MODULES if m in sys.modules]


def pin(strict: bool = True) -> dict[str, str]:
    """Set the pinned environment. Call before importing NumPy.

    Returns the variables as set. With ``strict`` the call raises if a numeric
    module is already loaded, because at that point the pin cannot take effect
    and silently returning would manufacture a false record.
    """
    late = already_imported()
    if late and strict:
        raise RuntimeError(
            f"phrt.numerics.pin() called after {', '.join(late)} was imported. "
            "Thread-pool sizes are read once when the BLAS loads, so pinning "
            "now would have no effect while appearing to succeed. Move the "
            "pin above every numeric import.")
    for k, v in PINNED_ENV.items():
        os.environ[k] = v
    return dict(PINNED_ENV)


def environment_as_set() -> dict[str, str | None]:
    """What the pinned variables actually hold right now."""
    return {k: os.environ.get(k) for k in PINNED_ENV}


def threadpool_state() -> list[dict]:
    """Every BLAS/OpenMP pool the process has actually loaded.

    Uses ``threadpoolctl`` when present. Its absence is reported as an explicit
    unavailable record rather than as an empty list, so "no pools found"
    cannot be mistaken for "no pools are multithreaded".
    """
    try:
        import threadpoolctl
    except ImportError:
        return [{"unavailable": "threadpoolctl is not installed, so the "
                                "effective pool state cannot be interrogated"}]
    keys = ("user_api", "internal_api", "num_threads", "version",
            "threading_layer", "architecture", "filepath")
    return [{k: info.get(k) for k in keys if k in info}
            for info in threadpoolctl.threadpool_info()]


def require_single_threaded() -> dict:
    """Abort unless every active pool reports exactly one thread.

    An empty pool list is also an abort. On this machine NumPy always loads
    OpenBLAS, so finding no pool means the interrogation failed, not that the
    process is serial -- and passing on a failed interrogation is exactly the
    kind of vacuous check this campaign has already been caught by once.
    """
    pools = threadpool_state()
    unavailable = [p for p in pools if "unavailable" in p]
    if unavailable:
        raise SystemExit(f"cannot verify thread-pool state: "
                         f"{unavailable[0]['unavailable']}")
    if not pools:
        raise SystemExit(
            "no BLAS thread pool was found. NumPy on this machine always loads "
            "OpenBLAS, so an empty pool list means the interrogation failed. "
            "Refusing to record a single-threaded claim that was not measured")
    bad = [p for p in pools if p.get("num_threads") != 1]
    if bad:
        raise SystemExit(
            "the numerical environment is not pinned: "
            + "; ".join(f"{p.get('internal_api')} reports "
                        f"{p.get('num_threads')} threads" for p in bad)
            + ". Set the pinned environment before importing NumPy")
    return {"pools": pools, "n_pools": len(pools), "all_single_threaded": True,
            "environment": environment_as_set()}


def record() -> dict:
    """The full numerical-determinism record for a run manifest."""
    return {"pinned_environment": environment_as_set(),
            "declared_pin": dict(PINNED_ENV),
            "threadpool_state": threadpool_state(),
            "all_pools_single_threaded":
                all(p.get("num_threads") == 1 for p in threadpool_state())
                and bool(threadpool_state())
                and not any("unavailable" in p for p in threadpool_state())}
