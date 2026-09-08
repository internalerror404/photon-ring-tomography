# Source-grounded final measurement passages, review 040

These insertions explain the archived E3C implementation; they do not change its
weights, source class or stored endpoints. Repository sources were read at
5985fe90f523d7cc3b0b1e11da9fa3897f6708c2.

## 1. Replace the E3C noise-table entry

> Pixel-integrated flux with white-noise variance
> \(\operatorname{Var}(\epsilon_p)=\sigma_{\Omega,g}(S)^2 a_p\).
> At a fixed geometry, radial-support setting and reference-SNR value, one
> density is used for all arms; derived readout covariances follow the same
> linear maps. The direct-source calibration is recalculated across geometries,
> so matched reference SNR does not mean one common absolute instrument-noise
> density over the twelve-geometry audit.

Here a_p denotes the screen quadrature weight used by the named archived
experiment. Do not assert that every legacy a_p is a corrected C13 geometric area.
The covariance is for integrated flux, not pixel-average intensity. The latter
would have variance sigma^2/a_p. An intensity-to-integrated-flux conversion must
transform the covariance as well as the signal.

## 2. State the E3C probe and SNR normalization explicitly

> The localized probe is
> \[
> q_a(r,\phi,t)=\frac{\mathbf1_{[r_{\rm in},r_{\rm out}]}(r)}{N_h}
> \exp\!\left[-\frac{(t+a)^2}{2h^2}\right],\qquad h=3M,
> \]
> with
> \[
> N_h^2=\pi(r_{\rm out}^2-r_{\rm in}^2)h\sqrt\pi.
> \]
> This gives unit squared norm under \(r\,dr\,d\phi\,dt\) over the
> annulus and temporal line. The full Gaussian is used in the forward probe;
> any operational-support convention used for anchor bookkeeping is stated
> separately. The sampled age grid and source-model windows are not redefined
> by this normalization.
>
> Let \(B^{(1)}_{g,r}\) be the chosen arm at unit noise density in geometry
> and support case g. With \(j_{\rm ref}=1\), define
> \[
> s_g=\frac{\|B^{(1)}_{g,0}j_{\rm ref}\|_2}{\sqrt{m_{g,0}}},\quad
> \sigma_{\Omega,g}(S)=\frac{s_g}{S},\quad
> B_{g,r}(S)=\frac{S}{s_g}B^{(1)}_{g,r}.
> \]
> The information per unit \(S^2\) and the information at the actual sweep
> value are different quantities:
> \[
> \widehat{\mathcal I}_{g,r}(a)=
> \frac{\|B^{(1)}_{g,r}q_a\|_2^2}{s_g^2},\qquad
> \mathcal I_{g,r}(a;S)=S^2\widehat{\mathcal I}_{g,r}(a).
> \]
> Thus the oldest passing grid center is
> \[
> \sup\{a:S^2\widehat{\mathcal I}_{g,r}(a)\ge\rho^2\},\qquad\rho=1.
> \]
> Equivalently, use \(\mathcal I(a;S)\ge\rho^2\) without another SNR
> factor. Empty passing sets and grid-ceiling censoring retain their recorded
> conventions. Reach, longest passing run, and anchor-connected span remain
> distinct from held-out estimator recovery.

Source selectors: run_e3c_operator_grid.py::snr_scale, age_norm, age_direction,
evaluate (s_ref, ihat, age_rows), depth_from_curve; physical.py::OrderRays and
PhysicalOperator. The E3C code stores information_per_snr2 and
information_at_reference_snr explicitly. A synthetic algebra check in the
provenance record confirms the normalization identity only, not campaign results.

The R2 calculation already includes its physical noise scaling in the whitened
matrix. Keep its own Gram, target/nuisance model and threshold unchanged. Do not
import the E3C per-SNR convention as an extra factor on R2's singular values.

## 3. Figure 2 provenance correction

> Statistics are aggregated over the geometries actually present in the filtered
> E3D source tables, whose IDs and count are recorded in the figure manifest.
> The primary E3D report specifies three anchors, unlike E3C's twelve-cell audit.
> The depth panel is an aggregate over that declared population, not a result
> at a single reconstruction geometry unless the selector explicitly says so.

Replace the generic paragraph with the actual table IDs after a zero-physics
row readback. In the current builder, '12 geometries' is a literal description;
no corresponding unique-ID count is computed. Do not regenerate source operators
to repair this description, and do not change plotted values unless the existing
row selection is itself found to be wrong.

## 4. Accurate opening and eta wording

> Different image orders have different, generally overlapping distributions of
> ray delays, so the same observer-time data can sample different source epochs.
> We distinguish that historical access from finite-model supported dimension
> and recovery of a specified source object.

> The R1 normalization floor is specified by a deterministic fit-split rule,
> but its realized scalar was not recovered from the inspected archived outputs.
> The reported endpoints are retained as archived results. No eta-sensitivity
> claim or new exact reproduction is made here; reconstructing the fit-only
> normalization would be a separately identified computation.

These paragraphs preserve the surviving science without portraying the paper as
a new law of geodesic propagation or asserting an unmeasured insensitivity to eta.
