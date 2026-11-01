# Notes for the full article (collected while the grid runs)

Observations made on finished results files. They are for the write-up and do not change any
pre-registered rule, estimand or verdict.

## O2 identifiability (results/p2_o2_ident.json, finished 2026-10-17)

- 216 rows (18 cells x 2 sigma x 2 eps x 3 replicates), 0 errors. Descriptive per PREREG_P2.
- Cost: median 107 s per profile, but two rows of `step_L1_pe1_da31.6` took 39 h and 42 h
  (139,747 s and 151,840 s); the step took 90 h in all. Report the cost distribution, not a mean.
- Precise but biased intervals: in those two rows the 95 % profile interval is about
  [8.2e-4, 8.6e-4] while the true k is 1.02e-3. The interval lies inside [k/2, 2k], so the
  frozen criterion counts k as practically identifiable, yet the interval misses the true value
  by about 18 %. Worth a sentence in Results or Limitations: the [k/2, 2k] criterion measures
  precision against a factor-2 tolerance, not coverage. Check how often this happens across O1
  identifiability (interval inside [k/2, 2k] but not containing k) and report the count.
- At `langmuir_L1_pe1_da1e+03` the upper end of the interval sits at the search bound (hi = 1),
  as expected deep in the equilibrium regime: not identifiable.

## Provenance

- B85: the O2/O3 driver verifies the freeze but writes no `freeze_commit`; the chain log is the
  record and is committed at the end of the grid.

## E3 first pass (2026-10-29, O3 incomplete at 197/216)

- Of the rows the [k/2, 2k] criterion calls identifiable, the interval misses the true k in
  87 % on O1 (33,021 of 37,991) and O2 (137 of 157), and 69 % on O3 so far.
- At sigma = eps = 0 on O1 no interval contains k (0 of 3,240): the intervals are a fraction of a
  percent wide and sit about 0.3 % off the truth, the sampling-resolution bias PREREG_P2 §9
  item 6 already records (+0.61 % on its probe). So the gap is mostly a small systematic bias
  meeting a near-zero-width interval, not the criterion misbehaving. Say this before reading
  E3 as a statement about the criterion. It cannot move any [k/2, 2k] verdict (a factor 2
  tolerance against a 0.3 % bias).
- Coverage falls as eps grows at every sigma (0.5 %: 23 % to 0.9 %): isotherm error shifts the
  estimate while the interval stays narrow. Rerun p2_e3_coverage.py after O3 completes.

## Before E2 runs (check, 2026-10-29)

- The E2 smoke fit (langmuir_L1_pe1_da1, sigma = eps = 2 %, rep 0) took 157 s, not the
  pilot's 1144 s, and its training loss stayed at 3.75e-01 for all 100 steps. The KAN may not
  be training on grid-scale data even though `test_kan_symbolic_recovers_ldf_at_zero_noise`
  passes. Find out why before the 216 fits: if it is a wiring fault, fix and record it; if it
  is M8's documented behaviour, say so. E2 must run M8 in its declared configuration.

## A5 outcome (O3 finished 2026-10-30 03:07)

- O3 identifiability: 216 rows, 0 errors. The 19 rows run after A5 took 4 h in all. Two rows
  had capped solves, both in `step_L1_pe1_da31.6` at eps = 0.02 replicate 2 (6 capped k values
  each, all far above the interval: `capped_adjacent` false in both). The cap changed no
  reported interval's neighbourhood. Report this in Methods in one sentence.

**Resolved 2026-10-30 (`p2_e2_diag.py`):** the KAN does train. The "flat" 3.75e-01 was pykan's
progress-bar text, which only refreshes every `log` steps (log = steps + 1). The recorded
per-step training RMSE (standardised units) falls 0.375 -> 0.365 -> 0.360 and settles at 0.360
by step 50; the true law k(q* - q) fitted by least squares to the same noisy Savitzky-Golay
dq/dt explains R^2 = 0.80 (RMSE about 0.45). So the network fits the data at least as well as
the true law; M8's failure is in the symbolic snapping step (support {1, T, c, q}), its
documented behaviour, not a wiring fault. E2 runs as declared.

## As-run verdicts (2026-11-01, before A6; kept in results/p2_verdicts_asrun.json)

- Positive control: Langmuir passed (discovery 135/135, identifiable 135/135); step failed
  (identifiable 0/135) because of B87, so step was withheld from every verdict (48 of 96 H2b slices).
- H2b, Langmuir: 20 slices "discovery fails before identifiability", 0 "with", 0 "outlives";
  28 slices have no boundary for one of the two on the grid. At Pe x1 the gaps are -1.7 to -2.5
  decades (Da*_disc 0.14 to 7.8; Da*_ident 43 to 562).
- Where eps >= 2 % the best method never reaches 50 % success at any Da, so Da*_disc does not
  exist on the grid while identifiability still holds up to Da of about 35 to 100: isotherm error
  alone puts discovery out of reach. This is the paper's clearest physical message; check it
  survives A6 (it should: Langmuir rows were inside the old k range).
- Some Da*_ident intervals have zero width (e.g. [561.8, 561.8]): P(identifiable) goes from all
  to none between two adjacent Da levels, perfect separation for the logistic. Report such a
  boundary as "between levels a and b", and say why the interval is degenerate.
- H2a: no verdict (no Langmuir condition crosses 50 % in R; step withheld). H2c: no verdict (no
  slice with a verdict). Both must be reported in their declared words, with the reason.


## Code-versus-prereg differences found while drafting Supplementary Note 1 (2026-11-01)
To be judged in the code-versus-prereg review round; each needs either a ledger entry or a
stated reason it is not a deviation. Source comments marked `% DIFF:` in paper2/supplementary.tex.
1. Pe labels: `pe_mult` multiplies D_L, so "pe0.2" is the HIGHEST Pe (about 470; ×1 about 94; ×5 about 19).
   Fixed in the text (levels named by Pe) and in fig_p2_results.py (pe_label). Check every table too.
2. O1 profile refinement uses 21 points per pass; prereg §3 Phase A says 41 for the ODE profile.
3. M7 receives Lib-B without the constant column; prereg says identical features for every method.
4. M1 temperature input scaled as (T - T_in)/10 K; A4 says "scaled by T_in".
5. M5 per-row error SDs collapsed to column means before TLS; channel ranges from noisy data.
6. M2 weak form fallbacks (support 31 if none admissible, 61 if no held-out probe) not stated in prereg.
7. O2 discovery drops edge probes (18 of 20).
8. weak.py / methods.py docstrings swap the M2/M2b names (labels only).
9. A1 text cites the freeze as d562f19 (old ID; 7dcc2fe here via COMMIT_MAP) - fine but say so.
10. H2c refinement grid never solved: no slice had a discovery crossing, so refine levels are empty (as designed).
