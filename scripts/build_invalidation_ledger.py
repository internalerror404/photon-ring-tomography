#!/usr/bin/env python3
"""Emit PREFIX_INVALIDATION_LEDGER.json.

Every artifact produced before a defect was corrected is invalid, whether or
not its numbers happen to have changed.  The ledger records which defect
invalidated what, and pairs the superseded hash with the replacement hash so a
reviewer can tell a genuine regeneration from an unchanged file.

The defect table is declared here; the hashes are measured.  Nothing in the
output is typed by hand.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phrt.io.manifests import utcnow

DEFECTS = [
    {
        "id": "D-A_identical_independent_collapse",
        "summary": "The 'independent' matched-rank spatial control was silently "
                   "identical to the 'identical' arm, because the low-rank "
                   "sampler accepted a generator it never used.",
        "consequence": "Any comparison between structured and order-specific "
                       "spatial diversity was a comparison of an arm with "
                       "itself. The matched-rank control did not exist.",
        "corrected_in": "8468c0b",
        "invalidates": ["e1_*"],
    },
    {
        "id": "D-B_linearoperator_h_collision",
        "summary": "Dimension attributes H/W/K/M shadowed "
                   "scipy LinearOperator.H, the Hermitian adjoint property.",
        "consequence": "Construction raised rather than silently miscomputing, "
                       "so no numerical artifact carries this defect. Recorded "
                       "because the fix renamed public attributes.",
        "corrected_in": "8468c0b",
        "invalidates": [],
    },
    {
        "id": "D-C_silent_delay_clamping",
        "summary": "A delay ladder longer than the history was clipped to fit "
                   "instead of refused, collapsing every order onto delay zero.",
        "consequence": "A misconfigured spec would have deleted the delay "
                       "mechanism entirely while still reporting success. No "
                       "shipped artifact used such a spec; the registered "
                       "ladder fits exactly (44 = 24 + 5*4).",
        "corrected_in": "8468c0b",
        "invalidates": [],
    },
    {
        "id": "D-D_mixer_noise_propagation",
        "summary": "Every readout was whitened at a flat sigma. Channel c "
                   "observes sum_n L[c,n](A_n x + eta_n) and carries noise "
                   "sigma*||L[c,:]||_2.",
        "consequence": "MATERIAL. The unresolved channel received a free "
                       "sqrt(6) amplitude gain purely for summing orders. Its "
                       "operational rank was reported as 6, better than "
                       "resolved; corrected it is 0. Every cross-readout "
                       "comparison before the fix is retracted.",
        "corrected_in": "430db48",
        "invalidates": ["e0_*", "e1_*", "e2_*"],
    },
    {
        "id": "D-E_retarded_age_sign",
        "summary": "Mode labels computed retarded age as (H-1-com), reflecting "
                   "the history axis. Order n samples ages [nD, nD+W), so the "
                   "index is the age already.",
        "consequence": "MATERIAL for interpretation. The correlation of "
                       "log10(sigma) with age had the wrong sign, reporting the "
                       "deep past as the best-seen epoch instead of the worst.",
        "corrected_in": "430db48",
        "invalidates": ["e2_*"],
    },
    {
        "id": "D-F_dct_nan_columns",
        "summary": "Requesting more DCT modes than an axis has samples padded "
                   "with zero columns and then normalised, yielding NaN basis "
                   "vectors that survived QR as a quietly smaller class.",
        "consequence": "Affected only the rejected (K, M) reading, where the "
                       "class does not exist. Now refused explicitly.",
        "corrected_in": "8468c0b",
        "invalidates": ["e0_*"],
    },
    {
        "id": "D-G_restricted_class_rs_rt_misinference",
        "summary": "The 24-dimensional smooth class was inferred as 4 spatial x "
                   "6 temporal. The reviewer ruling pins it to RS = 3 spatial x "
                   "RT = 8 temporal.",
        "consequence": "MATERIAL. The analytic rank cap rank(P)*RT changes from "
                       "12 to 16 and every restricted-class number moves. The "
                       "qualitative conclusion is unchanged: with a common "
                       "sampler the cap binds regardless of the delay ladder. "
                       "RS = 3 also settles the (K, M) reading independently, "
                       "since three spatial modes cannot exist over two cells.",
        "corrected_in": "PENDING_COMMIT",
        "invalidates": ["e0_*", "e1_*", "e2_*"],
    },
    {
        "id": "D-H_flat_sigma_measurement_convention",
        "summary": "The physical operator used the forward coefficient c = g^3 "
                   "with a flat per-row sigma, so Fisher information scaled with "
                   "the number of rows rather than with solid angle. Splitting "
                   "one pixel into k identical children multiplied the Gram by "
                   "k (relative error 1.0, 3.0, 7.0 at k = 2, 4, 8). The "
                   "corrected pixel-integrated model gives every row "
                   "sqrt(dOmega) * g^3 / sigma_Omega and is invariant to "
                   "5.4e-15 under the same split/merge test.",
        "consequence": "MATERIAL for every E3B information statement. Because "
                       "the lensing bands differ in solid angle by a factor of "
                       "~1500, an equal 1536-row budget per order handed the "
                       "thin deep bands a far quieter detector per unit sky. "
                       "Corrected: median Gamma_sensitivity_matched moves from "
                       "0.576 / 0.387 to 2.486 / 2.120, so 'information decays "
                       "seven to ten times more slowly than amplitude' becomes "
                       "'about twice as slowly'; the equalized-arm depth "
                       "advantage moves from one grid step to tens of M, "
                       "reversing the claim that attenuation costs little "
                       "reach; and the resolved stack's trace-information gain "
                       "over the direct image falls from 82% to 1.1% while its "
                       "operational rank still rises 153 -> 201. UNCHANGED: "
                       "delay diversity supplies the reach and spatial "
                       "remapping supplies none (DELAY_ONLY tracks RESOLVED and "
                       "SPATIAL_ONLY tracks DIRECT at every SNR), "
                       "PAIRING_DESTROYED remains the best-conditioned arm, and "
                       "every arm still reaches full algebraic rank on C224.",
        "corrected_in": "PENDING_COMMIT",
        "invalidates": ["e3b_*", "s0_operator_comparison*"],
    },
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*a: str) -> str:
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pre_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    pre = json.loads(pre_path.read_text()) if pre_path and pre_path.exists() else {"artifacts": {}}
    pre_hashes = pre.get("artifacts", {})
    pre_commit = pre.get("commit", "UNKNOWN")

    now = {}
    for p in sorted(root.glob("artifacts/**/*")):
        if p.is_file():
            now[str(p.relative_to(root))] = sha(p)

    entries = []
    for key in sorted(set(pre_hashes) | set(now)):
        before, after = pre_hashes.get(key), now.get(key)
        if before is None:
            state = "created_after_correction"
        elif after is None:
            state = "withdrawn"
        elif before == after:
            state = "byte_identical_after_regeneration"
        else:
            state = "superseded"
        entries.append({"path": key, "state": state,
                        "sha256_before": before, "sha256_after": after})

    doc = {
        "schema": "PREFIX_INVALIDATION_LEDGER/1",
        "generated_at": utcnow(),
        "invalidated_prefix_commit": pre_commit,
        "corrected_commit": git("rev-parse", "HEAD"),
        "statement": (
            "Every artifact produced at or before the invalidated prefix commit "
            "is withdrawn. Files listed as byte_identical_after_regeneration are "
            "still withdrawn as evidence from the prefix; the identical hash "
            "means only that the defect did not reach that file's contents, not "
            "that the prefix run may be cited."
        ),
        "defects": DEFECTS,
        "artifacts": entries,
        "summary": {
            "n_artifacts": len(entries),
            "superseded": sum(1 for e in entries if e["state"] == "superseded"),
            "byte_identical_after_regeneration":
                sum(1 for e in entries if e["state"] == "byte_identical_after_regeneration"),
            "created_after_correction":
                sum(1 for e in entries if e["state"] == "created_after_correction"),
            "withdrawn": sum(1 for e in entries if e["state"] == "withdrawn"),
            "material_defects": [d["id"] for d in DEFECTS
                                 if d["consequence"].startswith("MATERIAL")],
        },
    }
    out = root / "artifacts" / "PREFIX_INVALIDATION_LEDGER.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out}")
    for k, v in doc["summary"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
