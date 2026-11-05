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
