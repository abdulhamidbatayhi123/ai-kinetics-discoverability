# Paper 2 presentation plan (2026-11-05)

Sources: (1) the pinn-machining EAAI Paper 1 revision (`Desktop/pinn-machining/revision_eaai/`:
`figures/fig_style.py`, `fig_workflow.py`, `CAPTIONS.md`, `manuscript/terminology.md`,
`build/gates.py`, professor's comments in `restyle/PROF_COMMENTS_UK.docx`); (2) Nature Portfolio
rules read live on 2026-11-05 (research-figure-guide.nature.com; natcomputsci and natchemeng
content and AIP pages); (3) Rougier et al. 2014 (doi:10.1371/journal.pcbi.1003833), Wong's
Points of View (Nat Methods 2010-2011), Crameri et al. 2020 (doi:10.1038/s41467-020-19160-7).
Nothing illustrative is drawn as if it were a result; every number in a figure is read from a
results file by the script that draws it.

## Hard rules (Nature Portfolio)
- Width 89 mm (single) or 183 mm (double); height <= 170 mm. Arial/Helvetica 5-7 pt; panel
  letters 8 pt bold lowercase. Fonts embedded (pdf.fonttype 42). Vector PDF. RGB.
- No gridlines, shadows or coloured text; no rainbow or red/green; Okabe-Ito palette.
- Legends: short title sentence, panels in order, verbal key cues, n and the meaning of every
  interval; no methods detail. <= 6 main display items; <= 10 Extended Data figures, each cited.

## Steps
- [ ] P1 `p2_figstyle.py`: Paper 2's own style module (Paper 1's `figstyle.py` stays untouched):
      widths, Arial 7/6 pt, 5 pt floor asserted on save, no grid, fixed colour meanings
      (discovery blue, identifiability vermillion, each method one colour + line style for
      greyscale), provenance JSON (SHA-256 of script, style and inputs) per figure.
- [ ] P2 Figures 2-4 moved to `p2_figstyle`; coloured text removed; colour clash (orange =
      identifiability in Fig. 2 and M7 in Fig. 4) removed; metric in legends where useful.
- [ ] P3 Figure 1 redrawn in code as a map of the paper: ground truth -> design axes ->
      observation models -> methods and identifiability -> two boundaries -> hypotheses, each
      box tagged confirmatory / exploratory / descriptive and pointing to its Results section;
      text-fit and overlap assertion (`Canvas.check`, as in pinn-machining `fig_workflow.py`).
- [ ] P4 Extended Data (<= 10, each cited): all 96 H2b slice curves; positive control; estimator
      accuracy with exact data and H2b without Da 316/1000; E3 coverage; O2/O3 identifiability;
      H2d; M1, M8, M9; as-run vs corrected.
- [ ] P5 Legends rewritten to the rules above (short; detail to Methods/SI).
- [ ] P6 Build gate `paper2/build_p2.py`: compile article and SI; every number in the text bound
      to a results file (bindings) and checked; banned-phrase list; em dashes <= 5; abstract
      <= 150 words; main text <= 3,500; <= 6 display items; references in citation order; every
      Extended Data figure cited; fails loudly.
- [ ] P7 `paper2/terminology.md`: each term defined once with the evidence needed to use it
      ("identifiable" = interval inside [k/2, 2k], not calibrated; "discovered" = exact support,
      signs, ratio); banned phrases with replacements.
- [ ] P8 Prose pass: contributions stated plainly at the end of the Introduction; no bold run-in
      labels; Results subheadings as findings; smooth transitions.
- [ ] P9 Review round 2: fresh number trace, live reference recheck, Methods vs code, and an
      independent referee panel (method, domain, statistics, presentation) on the full PDF.
- [ ] P10 Title and journal: deep analysis of results and literature wording (title); live
      search of venues: Q1, prestigious, realistic acceptance, review <= ~1 year, no fee.
