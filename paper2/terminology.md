# Paper 2 terminology (each term defined once; use it only with the evidence named)

Pattern taken from pinn-machining `revision_eaai/manuscript/terminology.md`. `paper2/build_p2.py`
enforces the banned-phrase table on the article and the Supplementary Information.

| Term | Meaning in this paper | Evidence required before using it |
|---|---|---|
| discovered (the law) | the selected terms are exactly those of the true law, every sign is right and, for L1, the coefficient ratio q* : q is -1 within 10 % (p2/metric.py success_L1) | a success row; never for "close" or "similar" laws |
| practically identifiable | the 95 % profile-likelihood interval of k lies inside [k/2, 2k] with the true law given | an identifiability row; never "well determined" or "calibrated" (E3: the interval contains k in about 10 % of O1 rows) |
| boundary, Da*_disc, Da*_ident | the 50 % crossing of the unpenalised logistic fit in log10 Da, with a 2000-resample bootstrap interval | a crossing inside the grid; otherwise "no boundary on the grid" |
| gap | log10 Da*_disc - log10 Da*_ident, in decades | both boundaries exist |
| fails before / with / outlives | gap <= -0.25 / between / >= +0.25 decade (pre-registered words, in quotation marks) | the verdict file |
| no verdict | the pre-registered words for a missing boundary or too few crossings | the verdict file |
| window (of discovery) | success above 50 % at intermediate Da and below it on both sides | per-level fractions (figure data); descriptive |
| confirmatory | H2a, H2b, H2c as pre-registered | PREREG_P2 and its amendments |
| exploratory | declared before running in EXPLORATORY_P2.md (E1-E3), or H2d | that file |
| descriptive check (post-verdict) | analyses decided after the verdicts were seen (p2_ident_robustness.py) | must be labelled as such wherever used |
| measured isotherm | q*(c, T)[1 + eps g(c/c_in)], the isotherm every method and the identifiability test receive | - |
| Peclet number | u L / D_L, about 470, 94, 19 for the three dispersion levels (the code's x0.2 is the HIGHEST Pe) | Supplementary Table 1 |

## Banned phrases (with replacements)

| Do not write | Write instead |
|---|---|
| the first (to show, study, ...) | state what was done; prior work is cited |
| novel, groundbreaking, paradigm, unprecedented | describe the finding |
| dramatically, drastically, remarkably, strikingly | give the number |
| robust (as praise) | say what was varied and what did not change |
| significantly (without a test) | give the size of the effect |
| proves, demonstrates conclusively | shows, in this design |
| seamless, leverage, utilize, delve, crucial, pivotal | plain verbs: use, need, important, ... |
| AI discovers / AI fails (as agent) | the methods tested / equation-discovery methods |
| well identified / calibrated interval | practically identifiable (as defined) |
| state-of-the-art (unqualified) | name the methods |
| it is worth noting that, interestingly, notably | delete; state the point |
