#!/usr/bin/env python3
"""AMENDMENT_001 -- localized historical support diagnostic.

Question the registered arm cannot answer: **how far back does the archive
reach?**

The registered 24-dimensional class is RS = 3 spatial modes crossed with RT = 8
*global* temporal DCT modes.  Every one of those temporal modes spans the whole
history, so the class's restricted spectrum is an average over retarded epochs.
E2 found that faintness correlates with a mode's retarded age, but a DCT mode
does not have a single age -- only a centre of mass -- so that correlation is
suggestive rather than decisive.

This diagnostic replaces the average with a sweep.  For each retarded age it
builds an RS-dimensional class supported on a compact temporal bump at that age
and measures what the operator does to it.  The registered DCT arm is untouched
and remains the primary reported class.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phrt.audits.rank import spectrum_of
from phrt.config import load_registry
from phrt.io.manifests import RunManifest, Gate, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.operators import mixing
from phrt.operators.structured import ToySpec, build_order_blocks
from phrt.sources.localized import (DEFAULT_WIDTH, dct_temporal_localization,
                                    epoch_energy_fraction, localized_epoch_class)
from phrt.sources.toy_classes import REGISTERED_RS, REGISTERED_RT, smooth_separable

N_CELLS, N_SCREEN, HISTORY, WINDOW = 6, 2, 44, 24
MAX_ORDER, DELAY_STEP = 5, 4
OPERATIONAL_THRESHOLD = 1.0
SEED = 9000
GAMMAS = (0.0, 0.3, 0.6, 0.9)
READOUTS = ("direct_only", "resolved", "unresolved_sum")
SPATIALS = ("identical", "rotation_shear")


def spec_for(spatial: str, gamma: float) -> ToySpec:
    return ToySpec(history_length=HISTORY, window=WINDOW, n_screen=N_SCREEN,
                   n_cells=N_CELLS, max_order=MAX_ORDER, delay_step=DELAY_STEP,
                   gamma=gamma, delay="constant", spatial=spatial,
                   attenuation="equalized" if gamma == 0.0 else "exponential")


def mixer_for(readout: str, n: int):
    if readout == "direct_only":
        return mixing.OrderMixer(np.eye(n)[:1], "direct_only")
    if readout == "resolved":
        return mixing.resolved(n)
    if readout == "unresolved_sum":
        return mixing.unresolved(n)
    raise ValueError(readout)


def orders_covering(age: int) -> list[int]:
    """Which orders' windows contain this retarded age.

    Order n samples ages [n*D, n*D + W).  This is the structural reason an
    epoch is reachable at all, independent of how strongly.
    """
    return [n for n in range(MAX_ORDER + 1)
            if n * DELAY_STEP <= age < n * DELAY_STEP + WINDOW]


def sweep(run_id: str, cfg_hash: str) -> list[dict]:
    rows = []
    for spatial in SPATIALS:
        for gamma in GAMMAS:
            spec = spec_for(spatial, gamma)
            blocks = build_order_blocks(spec, SEED)
            for readout in READOUTS:
                m = mixer_for(readout, len(blocks))
                B = m.whiten(blocks)
                for age in range(HISTORY):
                    Q = localized_epoch_class(N_CELLS, HISTORY, float(age))
                    sp = spectrum_of(B @ Q, Q.shape[1],
                                     operational_threshold=OPERATIONAL_THRESHOLD)
                    cov = orders_covering(age)
                    rows.append({
                        "run_id": run_id, "config_hash": cfg_hash,
                        "spatial_structure": spatial, "gamma": gamma,
                        "attenuation": spec.attenuation, "readout": m.name,
                        "retarded_age": age,
                        "class_dimension": int(Q.shape[1]),
                        "epoch_energy_fraction": epoch_energy_fraction(
                            Q, N_CELLS, HISTORY, float(age)),
                        "orders_covering": len(cov),
                        "shallowest_covering_order": min(cov) if cov else -1,
                        "numerical_rank": sp.numerical_rank,
                        "operational_rank": sp.operational_rank,
                        "sigma_max": sp.sigma_max,
                        "sigma_min_positive": sp.sigma_min_positive,
                        "kappa_positive": sp.kappa_positive,
                        "trace_information": sp.trace_information,
                        "detectable": bool(sp.sigma_max >= OPERATIONAL_THRESHOLD),
                    })
    return rows


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    run_id = make_run_id("AMD001", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="AMENDMENT_001",
                      seeds={"seed": SEED, "bump_width": DEFAULT_WIDTH,
                             "RS": REGISTERED_RS, "RT": REGISTERED_RT,
                             "operational_threshold": OPERATIONAL_THRESHOLD})
    man.add_input(reg.path)

    rows = sweep(run_id, reg.sha256)
    import pandas as pd
    df = pd.DataFrame(rows)

    # the probe must actually be localized, or the diagnostic means nothing
    worst_loc = float(df.epoch_energy_fraction.min())
    man.add_gate(gate_from_tolerance(
        "AMD001_probe_is_localized", 1.0 - worst_loc, 0.05,
        note=f"worst fraction of probe energy within 3 samples of its centre: "
             f"{worst_loc:.4f}"))

    # and it must be sharper than anything the registered DCT arm can do
    dct_best = dct_temporal_localization(HISTORY)
    man.add_gate(gate_from_tolerance(
        "AMD001_sharper_than_registered_dct", dct_best, worst_loc,
        note=f"best single registered DCT temporal mode concentrates only "
             f"{dct_best:.4f} of its energy within 3 samples; the probe "
             f"concentrates at least {worst_loc:.4f}. The registered arm cannot "
             f"resolve an epoch, which is why this amendment exists."))

    # registered arm untouched
    Qreg = smooth_separable(N_CELLS, HISTORY)
    man.add_gate(Gate("AMD001_registered_arm_unchanged",
                      "PASS" if Qreg.shape[1] == REGISTERED_RS * REGISTERED_RT else "FAIL",
                      measured=int(Qreg.shape[1]),
                      threshold=REGISTERED_RS * REGISTERED_RT,
                      note="the registered DCT class is added to, never replaced"))

    p = write_table(rows, "amd001_localized_support")
    man.add_output(p)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    key = df[(df.spatial_structure == "rotation_shear") & (df.readout == "resolved")]
    print(f"rows {len(df)}   probe localization >= {worst_loc:.4f} "
          f"(best registered DCT mode: {dct_best:.4f})")
    print("\ndeepest detectable retarded age, by attenuation "
          "(resolved, rotation+shear):")
    for g in GAMMAS:
        s = key[(key.gamma == g) & (key.detectable)]
        deepest = int(s.retarded_age.max()) if len(s) else -1
        n_det = int(len(s))
        print(f"  Gamma = {g:.1f}   deepest detectable age {deepest:3d} / {HISTORY-1}"
              f"   epochs detectable {n_det:3d}/{HISTORY}")
    print("\ndeepest detectable retarded age, by readout (Gamma = 0.6, rotation+shear):")
    for ro in df.readout.unique():
        s = df[(df.spatial_structure == "rotation_shear") & (df.gamma == 0.6)
               & (df.readout == ro) & (df.detectable)]
        deepest = int(s.retarded_age.max()) if len(s) else -1
        print(f"  {ro:32s} deepest age {deepest:3d}   epochs {len(s):3d}/{HISTORY}")
    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:38s} {g.status:8s} measured={g.measured}")
    print(f"\nmanifest {mp}\ntotal {time.time()-t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
