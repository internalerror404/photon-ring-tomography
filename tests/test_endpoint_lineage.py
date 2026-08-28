"""The endpoint-lineage firewall. Item 11 of ruling 017."""
import pytest

from phrt.io.endpoint_lineage import offending, rows_offending, screen


def test_the_column_that_actually_leaked_is_caught():
    """hmt1_main_noiseless_control carried the endpoint under a control name."""
    cols = ["regime", "arm", "estimator", "snr0", "median_noisy",
            "median_noiseless", "median_noise_displacement_relative",
            "noise_changes_the_reconstruction", "noiseless_endpoint_is_lower"]
    bad = offending(cols)
    assert "median_noisy" in bad and "median_noiseless" in bad
    assert "noiseless_endpoint_is_lower" in bad
    assert "median_noise_displacement_relative" not in bad
    assert "regime" not in bad


@pytest.mark.parametrize("col", [
    "old_band_feature_error", "noiseless_old_band_feature_error",
    "radial_error_old", "angular_error_old_rad", "t_birth_error",
    "tau_decay_error", "median", "cell_mean", "mean_direct", "mean_arm",
    "median_ci_low", "mean_ci_high", "meets_materiality",
    "n_families_improved", "improved_circular_hotspot_trajectory",
    "L_stable_features_M", "pass_to_age_M", "selection_error",
    "median_relative_reduction",
])
def test_endpoint_columns_are_blocked(col):
    assert offending([col]) == [col]


@pytest.mark.parametrize("col", [
    "regime", "arm", "estimator", "snr0", "family", "index", "truth_seed",
    "min_total", "min_background", "zero_mean_max_abs",
    "azimuthal_mean_max_abs", "contrast_fraction", "positivity_scale",
    "relative_error", "max_absolute_error", "bias", "min_estimate",
    "target_separation_sigma", "realized_separation_sigma",
    "radial_cells", "azimuthal_cells", "hyperparameter",
    "median_noise_displacement_relative", "scored",
])
def test_diagnostic_columns_are_not_blocked(col):
    """Over-broad is the right bias, but not so broad it blocks a repair."""
    assert offending([col]) == []


def test_screen_refuses_rather_than_trims():
    rows = [{"regime": "x", "old_band_feature_error": 0.5}]
    ok, bad = screen("anything", rows, withheld=True)
    assert ok is False and bad == ["old_band_feature_error"]


def test_screen_allows_the_same_table_when_nothing_failed():
    rows = [{"regime": "x", "old_band_feature_error": 0.5}]
    ok, bad = screen("anything", rows, withheld=False)
    assert ok is True and bad == ["old_band_feature_error"]


def test_a_clean_table_passes_under_withholding():
    rows = [{"family": "f", "index": 0, "min_total": 0.0}]
    assert screen("hmt1_main_source_banks", rows, withheld=True) == (True, [])


def test_lineage_not_filename():
    """Renaming a table must not change what it is allowed to carry."""
    rows = [{"median_noisy": 1.0}]
    for name in ("hmt1_main_endpoint", "controls", "harmless_diagnostics"):
        assert screen(name, rows, withheld=True)[0] is False


def test_the_firewall_is_not_weakened_to_fit_a_column_name():
    """`in_endpoint` was a harmless boolean flag that the pattern caught.

    The flag was renamed rather than the pattern narrowed. A firewall that
    gives ground to make a diagnostic fit is one that will give ground again.
    """
    assert offending(["in_endpoint"]) == ["in_endpoint"]
    assert offending(["scored"]) == []


def test_rows_offending_unions_across_rows():
    rows = [{"a": 1}, {"median": 2}]
    assert rows_offending(rows) == ["median"]
