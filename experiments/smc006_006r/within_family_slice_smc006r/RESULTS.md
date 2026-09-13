# WITHIN_FAMILY_SLICE_SMC_006R — completed diagnostic failure

The fresh corrected run completed 128 datasets and 480 method-case runs. On the primary 8D benchmark, random-walk SMC had mean maximum-coordinate posterior-mean error 0.0520733. Two independent slice runs reduced this to 0.0268166 and 0.0262723; a 256-particle ladder reached 0.0211177.

The physical-release gate nevertheless failed. The two slice-128 runs had family-probability errors 0.0572748 and 0.0682915, versus the fixed <0.04 threshold. The slice-256 ladder remained at 0.0483898. Independent runs differed by 0.100766 in mean family-probability L-infinity distance and 0.417397 in mean absolute log evidence.

A postplanned exact-family-weight diagnostic retained the sampled conditional distributions but replaced estimated family weights with exact reference probabilities. Posterior-mean error then remained near 0.0234. This supports the bounded conclusion that within-family exploration is now adequate on this synthetic panel, while conditional evidence estimation/family weighting is the dominant measured algorithmic bottleneck.

The experiment produced zero physical observations, zero Kerr rays, zero movie reconstructions, and zero Paper-I units. The next registered target is evidence estimation on fresh exact-reference problems, not another photon-ring run.
