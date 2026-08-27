"""The per-family aggregate must follow the freeze, not a global list."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_hmt1_score import PARAM_COMPONENT, family_param_keys  # noqa: E402

FZ = json.loads((ROOT / "artifacts" / "configs"
                 / "HMT1_VALIDATION_FREEZE_V0.json").read_text())


@pytest.mark.parametrize("family", FZ["feature_families"]["declared"])
def test_every_declared_parameter_is_mapped(family):
    """No declared parameter may be silently dropped by being unrecognised."""
    for p in FZ["feature_families"][family]["parameters"]:
        assert p in PARAM_COMPONENT, f"{family}: {p} has no declared mapping"


@pytest.mark.parametrize("family", FZ["feature_families"]["declared"])
def test_position_is_always_scored(family):
    keys = family_param_keys(FZ, family)
    assert "radial" in keys and "angular" in keys, (family, keys)


def test_the_pattern_families_score_only_their_own_mode():
    """The defect that pinned the selection at maximal regularization.

    A pure cos(2 phi) field has no m = 1 content, so scoring its m = 1 mode
    divides by round-off. The freeze never asked for it: it declares a_m2 for
    this family and a_m1 for the other one.
    """
    m1 = family_param_keys(FZ, "m1_rotating_crescent")
    m2 = family_param_keys(FZ, "m2_structural_mode")
    assert "mode_m1" in m1 and "mode_m2" not in m1, m1
    assert "mode_m2" in m2 and "mode_m1" not in m2, m2


@pytest.mark.parametrize("family", ["circular_hotspot_trajectory",
                                    "two_hotspot_trajectories",
                                    "flare_birth_motion_decay",
                                    "plunging_feature"])
def test_hotspot_families_score_no_mode_amplitudes(family):
    keys = family_param_keys(FZ, family)
    assert "mode_m1" not in keys and "mode_m2" not in keys, (family, keys)
    assert "amplitude" in keys, (family, keys)


def test_keys_are_unique_and_ordered():
    """two_hotspot declares r_h1 and r_h2, which are one radial component."""
    keys = family_param_keys(FZ, "two_hotspot_trajectories")
    assert len(keys) == len(set(keys)), keys
