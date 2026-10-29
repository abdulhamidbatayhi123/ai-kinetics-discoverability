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
