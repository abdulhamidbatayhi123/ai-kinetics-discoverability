# Paper 2 pre-submission revision, 2026-11-11

Five independent read-only reviews at commit 4a704c5 (number trace; live references; Methods vs code
vs pre-registration; NCS editor + referee with the live author guide; presentation lessons from
pinn-machining Paper 1/Paper A and umut2) plus the captain's submission checklist
(~/.claude/PAPER_WORKFLOW_LESSONS.md section 1b). Every item below was checked against the files
before it was listed. Status: [ ] open, [x] done.

## A. Integrity and completeness (pre-registration)
- [ ] M6 (SINDy-PI, isothermal control) result: 0 of 2,160 fits, every support has six terms
      (results/p2_extra_m6.json). Report in Results + ED methods figure.
- [ ] Lib-A held-out fidelity (prereg s.3, s.4.3) never computed: driver p2_liba_fidelity.py committed
      98f8fab before its first run; report in SI, disclose the late run as a deviation.
- [ ] Prereg s.5 S1 on the map: Santana et al. Da = k t_stoich = 0.22 min^-1 x 39.9 min = 8.8
      (residence form 0.86), from arXiv 2303.13555v3 Table 1 and Appendix A (v = 0.51 dm/min
      interstitial, L = 2.0 dm, eps = 0.5, Langmuir 55.54*1.8c/(1+1.8c), c_in 5.5 mg/L, k = 0.22).
      Add a script + results file; Discussion sentence; SI Table 2 row.
- [ ] Prereg s.5 real MOF-303 data (exploratory): not done. Declare as deviation with the reason
      (no method discovers from outlet data alone in the simulations, so an outlet-only application
      could not be interpreted; S39 kinetics exist only as figures).
- [ ] E11 (about 2,000 samples): pending on Kaggle; report under its fixed reading (abstract if the
      gap falls below 0.25 decade in any slice).
- [ ] Printed "Deviations from the pre-registration" table in SI Note 1: M5 column weights (mean SD;
      ranges from data), weak support fallback 31/61 and per-replicate choice, weak-form BIC floor on
      the weak target, M1 maxfun 60, O2/O3 likelihood SD from the true range, M7 gate noise relative,
      positive control pooled over Pe, Lib-A run late, s.5 MOF-303 not run, O1 reported first.
- [ ] Minor prereg items: k accuracy (<= 10 %) reported; M3 inclusion probabilities not stored
      (disclose); O2/O3 boundaries are point values from 3 reps (say so); power 0.887 for a shallow
      boundary; Gram eigenvalue/delta descriptive (disclose not reported or report); "optimistic with
      respect to library size" sentence; M8 "machine limit"; WENDy "NOT RUN".
- [ ] Table 1: mark "no verdict" words as the analysis code's default (not prereg words).
- [ ] "minimum detectable effect" -> "decision threshold" (Fig. 3 caption).
- [ ] E5, M7 last-level, O1-any-method vs O3 labelled post hoc/descriptive; fix "Every exploratory
      analysis was declared ... before it ran".
- [ ] "five errors in our own code" -> "after the grid started"; A1.7 refined-grid wording.

## B. Numbers (trace review)
1 Table 1 any-method: 37 gaps + 2 more (3.2, 3.7). 2 O3 vs discovery: lower bound 0 not 0.25.
3 E6 77 % (35/45). 4 M7 1.0 to 1.4. 5 factor 2.5 -> about 2.5 (0.39 k). 6 "never failed without
noise" -> exact data. 7 B90 moved 36 of 71 (none higher), 22 more on grid; SI consistent.
8 M9 50 % only with exact data; ED5e pooled. 9 SI E6 "unanimous" exceptions. 10 SI E10 38 units vs QDF.
Fig. 4c caption denominators.

## C. References (live audit)
santana2023 wording (spurious constant under Langmuir; exact LDF only for Sips by SR; readout on the
network's uptake inside the bed); loman2026 attribution; dejaco2024 placement; data + code DOIs as
references; split paper1; drop arXiv duplicates; delgado2025 title; shumaylov v3 wording; liu2024
ICLR 2025; journal reference style (Surname, Initials; abbreviations; en dashes).

## D. Presentation (editor + lessons)
Abstract plain (define Da, no LDF acronym, 145 words max); intro: define Da, slice, boundary, gap,
identifiability; split paragraph 2; drop "Repeated database searches"; cite Fig. 1; no internal codes in
main text (names, codes once in Methods); headings true (H2a, L2); Results 1 restructured; no rhetorical
questions; code-error paragraph to Methods; "verified" not "validated"; one gap sign convention; one
evidence-label set (pre-registered / exploratory declared before the verdicts / post hoc); funding
statement; main text <= 3,400 words; Extended Data and Supplementary numbered in citation order.
Figures: Fig. 1 asterisk + O3 label + box 6 names; Fig. 3 verdict colour (not orange), diamonds on 0.5,
legend split, drop unused verdicts, describe bars; Fig. 4 legend colour, overlap note, denominators,
one y-label; ED5 c-d not duplicating Fig. 4; ED6 colour-bar wording + minus signs; ED7 codes;
ED8 line colour; remove stale fig_design.*.
Non-monotone noise at 2 % isotherm error (editor C7): quick descriptive check of support size vs sigma.

## E. Package (checklist 1b)
Line and page numbers; margin under limits; upload package + copy-paste sheet; final fresh-eyes
readability and compliance reviews; look at every rendered page.
