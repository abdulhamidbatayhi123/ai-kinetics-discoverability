# Paper 2 full article: plan (written 2026-10-20, before the verdicts exist)

## Format (checked live on nature.com, 2026-10-20)

Nature Computational Science and Nature Chemical Engineering have the same Article format:
main text up to 3,500 words (excluding abstract, Methods, references and figure legends);
abstract up to 150 words, no references; up to 6 display items; about 50 references
recommended. Sections: introduction with no heading, Results with topical subheadings,
Discussion with no subheadings, then Methods with topical subheadings. Nature Chemical
Engineering also allows up to 10 Extended Data figures.

Consequences for the Stage-1 text: it has 67 references and must come down to about 50
(cut the least necessary, never a source a claim rests on). The abstract goes from 195 to
150 words or fewer. Most of the design detail moves to Methods and the Supplementary
Information.

## Journal choice: decided by the verdicts, by this rule, before seeing them

- If the main finding is about methods (H2a holds or fails cleanly; H2b gives a single word
  across slices), send it to **Nature Computational Science**: "where equation discovery
  works and why".
- If the main finding is about the process (the boundary sits at an engineering-relevant
  Da, H2d says something about MOF step isotherms), send it to **Nature Chemical
  Engineering**.
- Both are free under the subscription route. No open-access fee.

## Display items (6)

1. **Design and question.** Column → observation models O1 to O3 → methods → two
   boundaries (discovery and identifiability). The existing `fig_design` is redrawn to fit.
2. **The map.** P(success) for the best method and P(identifiable) against log10 Da, per
   slice, with Da*_disc and Da*_ident marked and their intervals; the H2b words per slice.
   This is the paper's main figure.
3. **H2a collapse.** P(success) against R = δ/ε_eff for every condition on one axis, with
   R* per condition and the spread against the half-decade and one-decade thresholds.
4. **Methods compared.** Success by method (M2 to M7, M9; M5 marked as the oracle) across
   Da, at the main noise levels; H2c's EIV shift with its interval.
5. **Realistic observation (O2, O3).** Identifiability from probes and outlet only, the M1
   demonstration beside it, and E1 (exploratory) if it ran.
6. **Table: verdicts.** Every hypothesis, its pre-declared words, the estimate and interval,
   and whether it holds. One line each.

Extended Data / Supplementary: the positive control; the H2c refined grid; the H2d (MOF step
isotherm, k(q)) cells; the operating characteristics; E2 (M8); E3 (precision against coverage);
the full per-slice table; cost of every step; the corrections ledger summary.

## Word budget (3,500)

Introduction 550; Results 2,200 (about 450 per display item 2 to 5, plus the table);
Discussion 750.

## Title

Chosen after the verdicts, from what they say, at most 15 words, with no claim the results do
not support. The working title stays "When can AI discover adsorption kinetics?".

## Writing rules (from the author)

Plain, natural prose; at most five em dashes in the whole paper; no AI-sounding phrases; every
number resolved from a results file by the build; nothing claimed beyond the data; the AI
statement in the author's own wording (as in the README).
