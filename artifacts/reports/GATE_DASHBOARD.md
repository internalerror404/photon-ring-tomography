# GATE DASHBOARD

- commit `03b0d1c9c63131aa553904df0c09849d641dee8f`
- 139 gates, 121 passing

```
    active_blocking_failures:   0
    preserved_literal_failures: 7
    future_phase_not_run:       11
```

A preserved literal failure is a FAIL that has been adjudicated and kept on the record rather than reinterpreted; the status is never edited to match the disposition. A not-run gate belongs to a phase that is not yet in scope. Neither is an unresolved scientific failure.

| preserved failure | disposition |
|---|---|
| `EDGE1_a000_i020_raymap_generation` | `RESOLVED_BY_S0_BACKEND` |
| `G10q_retired_flat_sigma_convention` | `RETIRED_PIXELIZATION_DEPENDENT` |
| `G1_v01_reproduction_relative` | `FAIL_AS_WRITTEN` |
| `G7_grid_convergence_a098_i075` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7_grid_convergence_raw_max` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7b_weighted_operator_discrepancy` | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` |
| `GRID_AUTHORIZATION` | `SUPERSEDED_GRID_COMPLETE` |

## Full roll

| gate | status | disposition | measured | threshold |
|---|---|---|---:|---:|
| `AMD001_probe_is_localized` | PASS | – | 0.0006252 | 0.05 |
| `AMD001_registered_arm_unchanged` | PASS | – | 24 | 24 |
| `AMD001_sharper_than_registered_dct` | PASS | – | 0.2571 | 0.9994 |
| `DQ_fisher_quantile_convergence` | PASS | – | 0.01904 | 0.02 |
| `DQ_solid_angle_quantile_convergence` | PASS | – | 0.0149 | 0.02 |
| `DQ_throughput_quantile_convergence` | PASS | – | 0.01071 | 0.02 |
| `E0_oracle_is_upper_bound` | PASS | – | 0 | 1e-12 |
| `E1_duplicate_order_adds_no_rank` | PASS | – | 0 | 0 |
| `E1_rank_monotone_in_order` | PASS | – | 0 | 0 |
| `E1_zero_amplitude_adds_no_rank` | PASS | – | 0 | 0 |
| `E2_near_null_is_not_null` | PASS | – | -6.909e-08 | 0 |
| `E2_null_injection_invisible` | PASS | – | 3.615e-16 | 1e-08 |
| `E2_null_injection_moves_source` | PASS | – | -2 | -1e-06 |
| `E3C_G2_physical_dense_matrix_free` | PASS | – | 0 | 1e-10 |
| `E3C_G3_physical_adjoint` | PASS | – | 2.674e-13 | 1e-08 |
| `E3C_G4_physical_resolved_unresolved_mixing` | PASS | – | 0 | 1e-10 |
| `E3C_G4b_linear_collapse_covariance_propagation` | PASS | – | 0 | 1e-12 |
| `E3C_G6_physical_Gram_monotonicity` | PASS | – | 1.861e-16 | 1e-10 |
| `E3C_G6b_resolved_dominates_direct` | PASS | – | 1.574e-16 | 1e-10 |
| `E3C_G9w_weight_semantics` | PASS | – | 4.378e-16 | 1e-10 |
| `E3C_H2_registered_statistic_is_an_identity` | PASS | – | 12 | 12 |
| `E3C_freeze_raymap_hashes` | PASS | – | 0 | 0 |
| `E3C_frozen_grid_invariance` | PASS | – | dims=[224] n_ages=[64] | dims=[224] n_ages=[64] |
| `E3D_Gram_monotonicity` | PASS | – | 1.136e-16 | 1e-10 |
| `E3D_adjoint` | PASS | – | 4.89e-13 | 1e-08 |
| `E3D_class_nesting` | PASS | – | 2.73e-14 | 1e-10 |
| `E3D_dense_smoke_comparison` | PASS | – | 0 | 1e-10 |
| `E3D_enrichment_does_not_lose_rank` | PASS | – | 0 | 0 |
| `E3_pilot_meets_registered_ray_count` | PASS | – | 4179 | 1536 |
| `E3_pilot_no_convention_adjustment` | NOT_RUN | `REPLACED` | – | – |
| `EDGE1_a000_i020_raymap_generation` | FAIL | `RESOLVED_BY_S0_BACKEND` | – | – |
| `EDGE2_finite_transfer_weights_and_masks` | PASS | – | 1 | 1 |
| `EDGE2_memory_budget` | PASS | – | 3 | 15.7 |
| `G10q_continuum_noise_quadrature_invariance` | PASS | – | 5.401e-15 | 1e-10 |
| `G10q_retired_flat_sigma_convention` | FAIL | `RETIRED_PIXELIZATION_DEPENDENT` | 7 | 1e-10 |
| `G11_cpu_mps_inference_relative` | NOT_RUN | – | – | 0.0001 |
| `G13_replay` | PASS | – | 0 | 0 |
| `G1_canonical_vs_independent_dimensions` | PASS | – | 24 rows x 7 cols | 24 rows x 7 cols |
| `G1_canonical_vs_independent_mixed_tolerance` | PASS | – | 1.41e-05 | 1 |
| `G1_canonical_vs_independent_ranks_exact` | PASS | – | 0 | 0 |
| `G1_canonical_vs_independent_row_identities` | PASS | – | 0 | 0 |
| `G1_cross_machine_reference` | PASS | – | 0.0001851 | 1 |
| `G1_crossmachine_identifiability_dimensions` | PASS | – | 24 rows x 7 cols | 24 rows x 7 cols |
| `G1_crossmachine_identifiability_mixed_tolerance` | PASS | – | 0 | 1 |
| `G1_crossmachine_identifiability_ranks_exact` | PASS | – | 0 | 0 |
| `G1_crossmachine_identifiability_row_identities` | PASS | – | 0 | 0 |
| `G1_crossmachine_reconstruction_dimensions` | PASS | – | 12 rows x 6 cols | 12 rows x 6 cols |
| `G1_crossmachine_reconstruction_mixed_tolerance` | PASS | – | 0.0001851 | 1 |
| `G1_crossmachine_reconstruction_ranks_exact` | PASS | – | 0 | 0 |
| `G1_crossmachine_reconstruction_row_identities` | PASS | – | 0 | 0 |
| `G1_exact_zero_cell_absolute` | NOT_RUN | `WITHDRAWN` | – | – |
| `G1_generator_sha256` | PASS | – | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 |
| `G1_identifiability_dimensions` | PASS | – | 24 rows x 7 cols | 24 rows x 7 cols |
| `G1_identifiability_floats_relative` | NOT_RUN | `RENAMED` | – | – |
| `G1_identifiability_mixed_tolerance` | PASS | – | 1.41e-05 | 1 |
| `G1_identifiability_ranks_exact` | PASS | – | 0 | 0 |
| `G1_identifiability_row_identities` | PASS | – | 0 | 0 |
| `G1_identifiability_row_keys` | NOT_RUN | `RENAMED` | – | – |
| `G1_matrixfree_adjoint` | PASS | – | 1.148e-14 | 1e-08 |
| `G1_matrixfree_dense_parity` | PASS | – | 0 | 1e-10 |
| `G1_reconstruction_dimensions` | PASS | – | 12 rows x 6 cols | 12 rows x 6 cols |
| `G1_reconstruction_floats_relative` | NOT_RUN | `RENAMED` | – | – |
| `G1_reconstruction_mixed_tolerance` | PASS | – | 0.000732 | 1 |
| `G1_reconstruction_ranks_exact` | PASS | – | 0 | 0 |
| `G1_reconstruction_row_identities` | PASS | – | 0 | 0 |
| `G1_reconstruction_row_keys` | NOT_RUN | `RENAMED` | – | – |
| `G1_reproduction_relative_signal_bearing` | NOT_RUN | `WITHDRAWN` | – | – |
| `G1_scientific_reproduction` | PASS | `PASS_WITH_NUMERICAL_QUALIFICATION` | PASS_WITH_NUMERICAL_QUALIFICATION | PASS_WITH_NUMERICAL_QUALIFICATION |
| `G1_tolerance_specification` | PASS | – | RELATIVE_ONLY_NEAR_ZERO_DEFECT | RELATIVE_ONLY_NEAR_ZERO_DEFECT |
| `G1_v01_reproduction_mixed_tolerance` | PASS | – | 0.000732 | 1 |
| `G1_v01_reproduction_relative` | FAIL | `FAIL_AS_WRITTEN` | 1.313e-08 | 1e-08 |
| `G2_dense_operator_relative` | PASS | – | 0 | 1e-10 |
| `G2_physical_dense_matrix_free` | PASS | – | 0 | 1e-10 |
| `G3_adjoint_relative` | PASS | – | 2.916e-14 | 1e-08 |
| `G3_physical_adjoint` | PASS | – | 7.173e-14 | 1e-08 |
| `G4_order_collapse_relative` | PASS | – | 0 | 1e-10 |
| `G4_physical_resolved_unresolved_mixing` | PASS | – | 0 | 1e-10 |
| `G4b_linear_collapse_covariance_propagation` | PASS | – | 0 | 1e-12 |
| `G5_kernel_normalized_residual` | PASS | – | 5.513e-17 | 1e-08 |
| `G5_natural_null_on_registered_class` | NOT_RUN | `NOT_APPLICABLE_FULL_COLUMN_RANK` | 224 | 224 |
| `G5_physical_injected_null` | NOT_RUN | – | – | – |
| `G5a_detector_recovers_the_known_vector` | PASS | – | 1 | 1 |
| `G5a_manufactured_exact_null` | PASS | – | 0 | 1e-10 |
| `G5b_baseline_unperturbed_sigma_min` | PASS | – | 0.0003201 | 0.0003201 |
| `G5b_near_null_is_monotone_in_epsilon` | PASS | – | 1 | 1 |
| `G5b_near_null_scaling_exponent` | PASS | – | 3.983e-05 | 0.05 |
| `G5b_piecewise_model_residual` | PASS | – | 0.000401 | 0.001 |
| `G6_monotonicity_relative_negative_eigenvalue` | PASS | – | 1.675e-16 | 1e-10 |
| `G6_physical_Gram_monotonicity` | PASS | – | 6.563e-17 | 1e-10 |
| `G6b_resolved_dominates_direct` | PASS | – | 0 | 1e-10 |
| `G7_grid_convergence` | PASS | – | 0.01255 | 0.02 |
| `G7_grid_convergence_a098_i075` | FAIL | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` | – | – |
| `G7_grid_convergence_raw_max` | FAIL | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` | 0.06472 | 0.02 |
| `G7b_fields_are_analytic_not_discretised` | PASS | – | 2.2e-12 | 1e-09 |
| `G7b_fields_are_analytic_not_discretised_a098_i075` | PASS | – | 2.2e-12 | 1e-09 |
| `G7b_pointwise_cross_grid_field_metric` | NOT_RUN | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` | 0.366 | 0.05 |
| `G7b_transfer_field_convergence` | PASS | – | 0.02192 | 0.05 |
| `G7b_transfer_field_convergence_a098_i075` | PASS | – | 0.03088 | 0.05 |
| `G7b_weighted_operator_discrepancy` | FAIL | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` | – | – |
| `G8_cross_tracer` | PASS | – | 1.082e-12 | 1e-09 |
| `G8_cross_tracer_a098_i075` | PASS | – | 1.693e-12 | 1e-09 |
| `G8phi_rigid_origin_alignment` | PASS | – | 6.329e-12 | 1e-08 |
| `G8phi_rigid_origin_alignment_a098_i075` | PASS | – | 2.971e-11 | 1e-08 |
| `G8r_source_radius_no_adjustment` | PASS | – | 1.082e-12 | 1e-09 |
| `G8t_azimuth_after_rigid_offset` | PASS | – | 6.329e-12 | 1e-08 |
| `G8t_azimuth_offset_is_order_independent` | PASS | – | 1.303e-13 | 1e-09 |
| `G8t_emission_time_no_offset` | PASS | – | 2.274e-13 | 1e-06 |
| `G8t_radius_control` | PASS | – | 8.963e-13 | 1e-09 |
| `G8t_retarded_time_a098_i075` | PASS | – | 4.781e-06 | 0.001 |
| `G8t_retarded_time_validation` | PASS | – | 2.763e-06 | 0.001 |
| `G9_source_split_disjoint` | PASS | – | 0 | 0 |
| `G9c_per_order_ray_count` | PASS | – | 4179 | 1536 |
| `G9c_per_order_ray_count_a098_i075` | PASS | – | 9804 | 1536 |
| `G9w_weight_semantics` | PASS | – | 1.692e-16 | 1e-10 |
| `GRID_AUTHORIZATION` | FAIL | `SUPERSEDED_GRID_COMPLETE` | – | – |
| `GRID_all_registered_geometries` | PASS | – | 12 | 12 |
| `GRID_delay_windows_ordered` | PASS | – | 1 | 1 |
| `GRID_min_rays_per_order` | PASS | – | 3090 | 1536 |
| `GRID_no_ray_inside_horizon` | PASS | – | 1.325e-05 | 0 |
| `GRID_shared_time_reference` | PASS | – | 1 | 1 |
| `S0_1_numerical_integrator_cross_check` | PASS | – | 1.841e-05 | 0.001 |
| `S0_2_photon_sphere_double_root` | PASS | – | 0 | 1e-12 |
| `S0_3_critical_impact_parameter` | PASS | – | 2 | 0 |
| `S0_4_exact_horizon` | PASS | – | 1.848e-05 | 0.005 |
| `S0_4_no_ray_inside_horizon` | PASS | – | 2 | 2 |
| `S0_5_aart_low_spin_sequence` | PASS | – | 3 | 3 |
| `S0_5_low_spin_area_approaches_schwarzschild` | PASS | – | 0.01174 | 0.05 |
| `S0_6_operator_convergence` | PASS | – | 0.007364 | 0.05 |
| `S0_7_finite_positive_weights` | PASS | – | 1 | 1 |
| `S0_7_four_velocity_normalisation` | PASS | – | 2.22e-16 | 1e-12 |
| `S0_7_keplerian_closed_form` | PASS | – | 2.22e-16 | 1e-12 |
| `S0_7_quadrature_order0` | PASS | – | 2466 | 0.16 |
| `S0_7_quadrature_order1` | PASS | – | 36.72 | 0.0064 |
| `S0_7_quadrature_order2` | PASS | – | 1.236 | 0.0004 |
| `S0_8_G2_physical_dense_matrix_free` | PASS | – | 0 | 1e-10 |
| `S0_8_G3_physical_adjoint` | PASS | – | 1.366e-14 | 1e-08 |
| `S0_8_G4_resolved_unresolved_mixing` | PASS | – | 0 | 1e-10 |
| `S0_8_G6_Gram_monotonicity` | PASS | – | 0 | 1e-10 |
| `S0_8_G9w_weight_semantics` | PASS | – | 1.264e-16 | 1e-10 |
