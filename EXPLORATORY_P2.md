# Paper 2: exploratory analyses, declared before they run

Written 2026-10-20, while the confirmatory grid was still running (O3 at row 198 of 216; M7,
M1 and the refined cells not yet run). Nothing here changes `PREREG_P2_discoverability.md`,
its estimands, its verdicts or its words. Every result below is reported in the paper under
the heading "Exploratory", separate from the pre-registered results, whatever it shows.
This file is committed before any of these runs starts; its commit time is the record.

## E1. M1 at the scale a UDE needs (GPU or many-core CPU)

**Why.** PREREG_P2 §3 ran M1 only as a demonstration (L-BFGS, at most 50 steps or 2 h), because
one gradient step cost 145 s on this CPU, and it says: "on a GPU the same code is expected to be
feasible". A reader will ask whether a properly trained UDE discovers the law where the
demonstration did not. E1 answers that question and nothing else.

**What.** The same `fit_m1` code, data and readouts as the demonstration (`p2_grid_extra.py`):
Langmuir, Pe ×1, σ = 2 %, ε = 0, O3, the 9 Da levels, N_z = 50, the same 2 × 32 network, loss,
L-BFGS-B, sparse and PySR readouts, and `success_L1` on either readout. Only two settings change:
- at most **1000** L-BFGS iterations (20 × the demonstration) instead of 50;
- a wall budget of **4 h** per fit instead of 2 h.
Replicate 0 first (9 fits). Replicates 1 and 2 only if the money cap below allows all 27 fits.

**Pilot and cap.** A pilot times one gradient step on the cell with Da nearest 10, on the
rented machine's GPU and on its CPU cores, and uses whichever is faster (the code runs in
64-bit floating point, which some GPUs execute slowly). Spending stops at the amount agreed for
this work (planned: about $5 for the pilot, at most $40 in all). If the pilot shows
the 9 fits cannot finish within the cap at 1000 iterations, the iteration limit is lowered to what
fits, and the paper reports the limit actually used.

**Reported.** Per Da level: final loss, iterations used, both readouts' supports, `success_L1`,
k̂ and its relative error, beside the demonstration's row for the same cell. No pooled verdict.

## E2. M8 (KAN) on its declared subgrid, on the local CPU

**Why.** PREREG_P2 §3 declared M8's grid run (216 fits) and gated it on cost: 1144 s per fit
against a 300 s limit, so M8 was NOT RUN, "a machine limit". After the grid, the local CPU is
free for about three days, which removes that limit.

**What.** Exactly the declared configuration: `p2.methods.kan_symbolic` (pykan 0.2.8), raw
variables, lamb = 1e-3, its default steps, on all Da × σ ∈ {0.5 %, 2 %} × ε ∈ {0, 2 %} × both
isotherms × Pe ×1 × O1, 3 replicates = 216 fits; `success_L1`. Runs only after the confirmatory
chain has finished, one job at a time.

**Reported.** Success counts per (isotherm, σ, ε) and per Da level, beside M8's documented
known-answer failure at zero noise. M8 does not enter any confirmatory pool.

## E3. Precision versus coverage of the identifiability criterion (no new compute)

**Why.** PREREG_P2 calls k practically identifiable when the 95 % profile interval lies inside
[k/2, 2k]. On O2, two rows met that criterion with an interval that did not contain the true k
(`paper2/WRITEUP_NOTES.md`). The criterion measures precision, not coverage.

**What.** For every identifiability row (O1, O2, O3): whether the interval meets [k/2, 2k], and
whether it contains the true k. Reported as counts per observation model and Da level, and the
fraction of "identifiable" rows whose interval misses k. Descriptive only; the confirmatory
Da*_ident stays as pre-registered.

## Post-verdict analyses E4-E7 (declared 2026-11-05, AFTER the corrected verdicts, BEFORE running)

Prompted by an internal referee-panel review of the full draft. They are post hoc: they are
reported as such wherever they are used, they enter no confirmatory test, and the pre-registered
verdicts stay as computed (`results/p2_verdicts.json`).

## E4. Matched success criteria (no new compute; re-scoring stored rows)

**Why.** Discovery must return the exact terms with the coefficient ratio q* : q = -1 within 10 %;
identifiability asks only for the 95 % interval inside [k/2, 2k]. The gap could partly reflect
this asymmetry. **What.** H2b recomputed with `p2_analyze.verdicts` unchanged except the outcome
of each row: (a) discovery relaxed to "exactly the terms {q, q*} with a negative q coefficient"
(the ratio test dropped; the q* coefficient is not stored, so its sign cannot be checked);
(b) identifiability strict, 95 % interval inside [0.9 k, 1.1 k]; (c) identifiability by the point
estimate, the interval's geometric midpoint inside [k/2, 2k] (ignores the interval's width, so
it does not rely on the interval's calibration); (d) = (a) with (c). Verdict words per slice and
overall, and gaps, against the pre-registered ones. Boundaries by the same logistic estimator.

## E5. Library conditioning against Da (no new compute if stored; otherwise from the fields)

**Why.** The Discussion attributes part of the failure to collinear candidate terms near
equilibrium. **What.** The condition number of the standardised library matrix on the O1
observations at sigma = eps = 0, per isotherm, Pe and Da (PREREG_P2 lists it as a mechanistic
predictor).

## E6. Model selection among a few candidate laws (the comparator the Discussion recommends)

**Why.** The Discussion recommends choosing among a few candidate rate laws when open discovery
fails; the study does not test this. **What.** On O1, for a declared subgrid (Pe ~94; sigma 0.5
and 2 %; eps 0 and 2 %; all Da; both isotherms; estimation replicates), fit each candidate law by
the output-error likelihood used for identifiability (the exact update along the observed c and T)
and choose by BIC: LDF k(q* - q); quadratic driving force k(q*^2 - q^2)/(2q); pseudo-second order
k(q* - q)^2 (the three kinetic models most used in adsorption practice; amended 2026-11-05 before
the run, replacing a rate linear in the fluid concentration, so that all three candidates are
standard and fitted by the same stable implicit update). Each law is integrated by implicit Euler
on the identifiability profile's upsampled q*(t) path, k profiled on 10^-7..10 at 10 points per
decade; all three have one parameter, so BIC picks the largest likelihood. Success = LDF chosen;
also reported: LDF chosen and its k within [k/2, 2k]. Reported by Da beside discovery and
identifiability.

## E7. Systematic isotherm error (step isotherm)

**Why.** The pre-registered isotherm error is a smooth random multiplicative function; real
water-isotherm errors are often a shift of the step position. **What.** For the step isotherm,
O1, sigma 0.5 and 2 %, a measured isotherm whose step is shifted by +-1 % and +-2 % relative
humidity (the error model only; fields unchanged), discovery (the six sparse solvers) and O1
identifiability, estimation replicates; descriptive.

## E8. Sampling rate (declared 2026-11-08, after E6's corrected rows, BEFORE running)

**Why.** After B91, E6 still chose the wrong law at Da >= 31.6 with an exact isotherm. A six-replicate
pilot (not reported as a result; noise drawn outside p2_observe) suggested the cause is the time
resolution: at Da = 31.6 the step isotherm's LDF law lost to the quadratic driving force at 200 time
points and won at 400, with noise on q alone or on c, q and T alike. The Discussion recommends
choosing sampling rates; this tests that recommendation. **What.** O1, both isotherms, Pe ~94, all
nine Da, sigma 0.5 and 2 %, eps 0, replicates 0..59, at two sampling rates: N_T = 200 (the grid's;
identical to p2_observe.observe) and N_T = 400 (every stored time of the ground-truth fields, the
same noise SD per sample). Per row: discovery by the six sparse solvers in both forms (success_L1),
O1 identifiability (profile_interval_o1, the pre-registered criterion) and, for replicates 15..59,
E6's model selection (p2_e6_modelselect.select). Boundaries as in E7 (best discovery method chosen
on replicates 0..14, logistic 50 % crossings on 15..59). Reported: success against Da for each
quantity at both rates, and the boundary shift from 200 to 400 samples; descriptive, no verdict.
*Clarification added before running (2026-11-08):* every method runs unchanged. Their windows are
defined in samples (the 21-sample Savitzky-Golay derivative, the weak-form supports), so at
N_T = 400 they span half the time they span at 200; this is what applying the methods as published
to faster-sampled data does, and it is reported as such.

## E9. Noise in the forcing of E6 (declared 2026-11-09, after review round 2, BEFORE running)

**Why.** Review round 2 (M3) noted that with an exact isotherm E6 never chose the LDF law at Da >= 100,
yet with 2 % isotherm error it chose it in 23 of 45 replicates (Langmuir, sigma 0.5 %, Da 100), and
asked whether the failure belongs to the data or to the likelihood. The likelihood drives each law
with q*(t) computed from the NOISY observed c and T (errors in variables). One row was run to time
this check before this declaration (Langmuir, Da 100, sigma 0.5 %, replicate 15): it chose the
quadratic driving force with both forcings, and every law's log-likelihood rose from about -3,365
with the observed forcing to about -2,000 with the clean one. That row is recomputed below, not
reported separately. **What.** E6 unchanged (p2_e6_modelselect.select: same laws, k grid, Brent
refinement, NSUB, noise SD rule) except that q*(t) is computed from the noise-free c and T at the
same probes and times (p2_observe.observe with sigma = 0, same replicate), while q is observed with
noise as in E6. Subgrid: O1, both isotherms, Pe ~94, Da 31.6, 100, 316 and 1000, sigma 0.5 and 2 %,
eps 0, replicates 15..59 (720 rows). Reported: the fraction choosing the LDF law per cell, beside
E6's eps = 0 fractions, and each law's median log-likelihood. **Reading fixed in advance.** Where the
LDF fraction rises from E6's to at least two thirds, the failure there is attributed to noise in the
forcing (a property of the likelihood, not of the data); where it stays at or below one third, it is
not; otherwise mixed. Descriptive, no verdict; it changes no confirmatory result.

**Outcome (2026-11-09, results/p2_e9_summary.json, 720 rows, 0 errors).** LDF fraction with noise-free
forcing (E6's in brackets): Langmuir Da 31.6, sigma 0.5 % 1.00 (0.69) and 2 % 0.69 (0): attributed to
noise in the forcing at 2 %, already chosen at 0.5 %. Langmuir Da 100, 316, 1000: at most 0.22 (all 0 in
E6): not attributed. Step isotherm, all four Da and both sigma: 0 (0): not attributed. A diagnostic made
afterwards and NOT declared (p2_diag_e9_noisefree.py, replicate 15, q, c and T all noise-free): the LDF
law was still not chosen at Da 100 (both isotherms; LDF k_hat/k 0.984 and 1.007) or 1000 (Langmuir), so
the misfit there is deterministic. Reported in Supplementary Note 3 (E9), labelled as such.

## E10. Time resolution of the forcing behind E6's deterministic misfit (declared 2026-11-09, after E9, BEFORE running)

**Why.** E9 and its undeclared noise-free diagnostic showed that at Da 100 and 1000 the integrated LDF law
(the truth) loses to another law even on fully noise-free O1 data, while its k is within 2 %. At the grid's
200 observation times k h is about 2 at Da 100 and 20 at Da 1000 (h = t_horizon / 199), so q lags q* by
less than one sampling interval and every law is driven by q*(t) reconstructed (PCHIP) between samples.
E8 doubled the sampling (400) without restoring the choice at Da 100. **What.** Four cells (O1 geometry,
Pe ~94, L1; Langmuir and step; Da 100 and 1000) are re-solved with the unchanged solver and settings
(p2_generate.solve_cell) but 3,991 stored times (every 10th equals one of the grid's 400; checked against
the stored fields). On noise-free c, q, T at the 20 O1 probes, E6's select() (unchanged; sigma =
1e-4 x range of q, as in the E9 diagnostic) is run at 200, 400, 1,996 and 3,991 evenly spaced times.
Reported: the chosen law, each law's log-likelihood relative to the best, and LDF k_hat/k, per cell and
resolution. **Reading fixed in advance.** If the LDF law is chosen at 3,991 times in a cell where it is
not at 200, the misfit there is attributed to the reconstruction of q* between samples (a property of
the sampling); if it is not chosen even at 3,991, the cause lies elsewhere and is reported as unresolved.
Descriptive, no verdict; it changes no confirmatory result. Fields are written to a scratch directory,
not to data/p2.

**Outcome (2026-11-09, results/p2_e10_resolution.json).** Re-solved fields equal the stored ones at the shared
times (max difference 0). Chosen law (LDF k_hat/k) at the grid's own 200 / 400 times, 1,996, 3,991: Langmuir
Da 100 QDF (0.98) / LDF (1.05) / LDF (1.01) / LDF (1.01); step Da 100 QDF (1.01) / QDF (1.08) / LDF / LDF;
Langmuir Da 1000 PSO (0.51) / LDF (0.96) / LDF / LDF; step Da 1000 QDF at every resolution (unresolved; k h
still ~1 at 3,991). Reading: the misfit is attributed to the reconstruction of q* between samples in three of
four cells. Deviation, disclosed: the declared 200 and 400 times were spaced evenly on the fine grid and
differ by up to half a grid interval from the grid's own; the grid's exact 200 and 400 times were added after
the first rows (keys grid200, grid400). The evenly spaced rows agree with them except Langmuir Da 1000 at
200 (LDF by 38 log-likelihood units vs PSO at the grid times). Reported in Supplementary Note 3 (E10).

## E11. The boundaries at about 2,000 samples per run (declared 2026-11-11, after an independent review, BEFORE running)

**Why.** An independent review (2026-11-10) noted that every boundary assumes the grid's 200 observation
times, that E8 at 400 moved discovery up by 0.4 to 0.7 decade and identifiability by 0 to 0.3, and that
real breakthrough rigs sample more finely; it asked whether the gap survives much finer sampling.
**What.** As E8, at about ten times the grid's rate. Cells: O1, both isotherms, Pe ~94, L1, all nine Da,
sigma 0.5 and 2 %, eps 0, replicates 0..59 (2,160 rows). Each cell is re-solved with the unchanged solver
(p2_generate.solve_cell, as in E10) with 3,991 stored times; observations use every second stored time
(1,996 times, which include the grid's 200), the same probes and the same noise SD per sample, with a noise
stream of its own. Per row:
(a) discovery by the six sparse solvers in both forms, run unchanged (windows in samples, so the
    weak-form supports 31/61/121 and the 21-sample derivative span a tenth of the time they span at 200);
(b) the same twelve, with windows matched in time to the grid's (supports 309/609/1,209, derivative 209);
(c) O1 identifiability (profile_interval_o1, the pre-registered criterion);
(d) for replicates 15..59, E6's choice among three laws.
The best discovery method is chosen on replicates 0..14 among the 24 candidates of (a) and (b), and the
logistic 50 % crossings are taken on replicates 15..59, as in E8. (a) and (b) are also reported
separately.
**Reading fixed in advance.** For each of the four (isotherm, sigma) slices with both boundaries:
- if log10(Da*_ident / Da*_disc) stays at or above 0.25 decade (the pre-registered verdict threshold),
  "discovery fails before identifiability" holds at about 2,000 samples;
- if the gap falls below 0.25 or reverses in any slice, that is reported in the abstract and Results as a
  limit of the main finding;
- a slice without one of the boundaries is reported as such.
Descriptive, no verdict; it changes no confirmatory result. Fields go to a scratch directory, not data/p2.
One row may be run first to time the job; it is recomputed with the rest.
