# Equation discovery fails before rate constants become unidentifiable in simulated adsorption columns

Code, pre-registration, results and manuscript of this pre-registered computational study by
Abdulhamid Batayhi (Yıldız Technical University, ORCID
[0009-0007-0374-6755](https://orcid.org/0009-0007-0374-6755)). The manuscript and the
Supplementary Information are `paper2/article.pdf` and `paper2/supplementary_main.pdf`, built from
`paper2/article.tex` and `paper2/supplementary.tex`.

Archived on Zenodo: [doi:10.5281/zenodo.23325994](https://doi.org/10.5281/zenodo.23325994)
(all versions); release v0.1-prereg, the state before the confirmatory grid, is
[doi:10.5281/zenodo.23325995](https://doi.org/10.5281/zenodo.23325995), and release v1.0-submitted,
the state of the submitted manuscript, is
[doi:10.5281/zenodo.24090779](https://doi.org/10.5281/zenodo.24090779); release v1.0.1-submitted,
which adds the table of published columns (now Supplementary Table 1), is [doi:10.5281/zenodo.24101317](https://doi.org/10.5281/zenodo.24101317); release v1.0.2-submitted, an earlier submission candidate
(with E11, Figure 5 and Source Data), is [doi:10.5281/zenodo.24149951](https://doi.org/10.5281/zenodo.24149951); release v1.0.3-submitted, which
supersedes it as the submitted version (title without "long", the information-matched comparison and the
second system E12/E12b), is [doi:10.5281/zenodo.24244392](https://doi.org/10.5281/zenodo.24244392).

## The question and the answer in brief

Equation-discovery methods offer to learn the uptake rate law of a fixed-bed adsorption column
from its data. This study asks for which regimes they can, and whether discovery fails where the
rate constant itself stops being practically identifiable, or earlier. Breakthrough data were
simulated for a Langmuir sorbent and a MOF-303-like step isotherm over four decades of
Damköhler number (Da), three Péclet numbers, four noise levels and four levels of isotherm
error, observed through interior probes (with or without uptake) or at the outlet only. The
design, thresholds and verdict words were frozen before any method ran.

| Hypothesis | Pre-registered verdict (corrected run, `results/p2_verdicts.json`) |
|---|---|
| Positive control | both isotherms pass (discovery and identifiability 135 of 135 each) |
| H2b, discovery vs identifiability | "discovery fails before identifiability" in all 37 slices with both boundaries; gap 1.6 to 3.7 decades of Da |
| H2a, one error ratio places the boundary | no verdict: one of twelve conditions has a crossing |
| H2c, errors-in-variables moves the boundary | no verdict: no slice has a boundary for both estimators |
| H2d, loading-dependent rate (exploratory) | found almost only at Da = 1 |

The first-run verdicts (`results/p2_verdicts_asrun.json`) and those computed before the last
correction, B90 (`results/p2_verdicts_preB90.json`, 30 slices with a verdict), are kept beside
them; the corrections are listed below and in `RETRACTIONS_P2.md`. No correction changed a
verdict word.

Post hoc checks, each declared before it ran (`EXPLORATORY_P2.md`), leave the H2b word unchanged
under four alternative success rules (E4, `results/p2_e4_criteria.json`: gaps 0.89 to 3.75 decades)
and at twice the sampling rate (E8, `results/p2_e8_summary.json`: every boundary moves up or stays, the gap
stays at least 1.25 decades), and at about ten times the sampling rate (E11, declared before it ran,
`results/p2_e11_summary.json`: discovery rises 0.7 to 1.9 decades, the gap stays 0.72 to 2.01 decades
where both boundaries exist). Choosing among three candidate laws by likelihood (E6) finds the
LDF law in every replicate up to Da = 10 with an exact isotherm, further than open discovery, but
in none from Da = 100 on; noise-free forcing (E9, `results/p2_e9_summary.json`) restores
the choice only for the Langmuir sorbent at Da = 31.6; on noise-free data, finer sampling restores it in three of four cells at
Da >= 100 (E10, `results/p2_e10_resolution.json`). A systematic isotherm error limits the rate constant too: shifting the
step of the MOF-303-like isotherm by 1 % relative humidity (E7, `results/p2_e7_summary.json`)
biases the fitted k and lowers the identifiability boundary to Da = 17 to 57, while discovery
stays at or below 31 % at every rate. A second system, a reversible reaction in a stirred tank
(E12 and E12b, `results/p2_e12_summary.json`, `results/p2_e12b_summary.json`), is consistent with
this but does not test it: with 0.5 or 2 % noise, discovery reached at most 40 % of replicates at
any Da in both declared designs while k stayed identifiable up to Da of about 110 to 870, so the
positive control failed and no gap is read; on exact data, weak-form best-subset selection recovered
the law at every Da (post hoc, `results/p2_e12_noisefree.json`). At the grid's 200 observation times with the noise divided by sqrt(10), which carries
about the information of 2,000 observations (E13, `results/p2_e13_summary.json`), every discovery boundary
lies within 0.25 decade of its 2,000-observation value, so the gain from denser sampling is information, not
time resolution; discovery still fails first in three of four slices, and in the fourth (step isotherm, 0.16 %
noise) the fitted boundaries meet while the measured success at Da = 316 is 4 % with k identifiable in all
replicates. Parallel symbolic enumeration (E14, `results/p2_e14_summary.json`) closes the gap in no slice: its
last level with at least 50 % success lies 1.25 to 2.08 decades below the identifiability boundary.

## Quick check for reviewers

Every row-level result of the grid is shipped in `results/`, so the verdicts, every figure except
Fig. 2, and both documents can be rebuilt without solving any column. Run every command from the
repository root.

**Setup.** Python 3.12 (3.12.10 was used), then

```bash
pip install -r requirements_p2.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

`requirements_p2.txt` pins every package the code imports; the extra index serves the CPU wheel
of PyTorch. The study was developed and run on Windows 11 with Python 3.12.10; the Kaggle runs (B90, E6,
E8, E11, E13, E14) used Kaggle's Linux images, so the analysis code has run on both. No graphics processor is
needed. The install time was not measured; the largest downloads are PyTorch (CPU) and JAX. These
environment variables are read:

| Variable | Read by | Default |
|---|---|---|
| `TECTONIC` | `paper2/build_p2.py`: the Tectonic executable that compiles both documents (Tectonic 0.17.0 was used) | `tectonic` on the PATH |
| `P2_PY` | the `.sh` and `.cmd` launchers: the Python interpreter they call (set it to the Python 3.12 environment above, without quotes) | `python` |
| `KAGGLE_EXE` | the Kaggle queues (`kaggle_*/queue.py`): the Kaggle command-line tool | `kaggle` on the PATH |

**Steps that take minutes.**

```bash
python paper2/build_p2.py        # both PDFs; recomputes the key numbers in the text from results/*.json and checks
                                 # word and display-item limits, banned phrases and figure provenance (needs Tectonic)
python p2_check_prov.py          # every figure was drawn from the current style file, script and inputs (exit 1 if not)
python fig_p2_results.py         # Figs 3, 4 and Extended Data Fig. 4 (about a minute)
python -m pytest -m "not slow"   # the test suite without its ten slowest tests (about 4 to 5 min of CPU:
                                 # it solves a few small columns and trains the neural model briefly)
```

The other figure scripts that need no fields run the same way: `fig_p2_overview.py`,
`fig_p2_guide.py`, `fig_p2_extended.py` and `fig_p2_ed6_reaction.py`.

**Steps that take half an hour or more.**

```bash
python p2_generate.py            # ground-truth fields data/p2/*.npz from the seeds in data/p2/manifest.json:
                                 # about 30 min (1,787 s of cell solves in logs/p2_generate.log)
python p2_analyze.py             # verdicts from the row files -> results/p2_verdicts.json: about 1.5 h on one
                                 # laptop CPU (2,000 bootstrap resamples per boundary)
git diff --stat results/p2_verdicts.json   # prints nothing: the shipped verdicts are reproduced
python -m pytest                 # the full test suite: about 76 min (logs/pytest_p2.log)
```

The fields are not tracked, so `p2_generate.py` must run before Fig. 2 (`fig_p2_examples.py`), the
Source Data (`p2_source_data.py`) and the two tests in `tests/test_e8_sampling.py`; those tests are
skipped, with the reason, while the fields are absent. In `logs/pytest_p2.log` the ten tests now
marked `slow` took 72 of the 76 minutes.

## Where each figure and number comes from

Every figure, Source Data file and file that `paper2/build_p2.py` reads, with the script that writes
it. Figures are `paper2/<name>.{pdf,png,prov.json}` (the Stage 1 design figure has no provenance file);
each provenance file records the SHA-256 of the
style file, the script and every input. Results files are in `results/`; "fields" are the untracked
`data/p2/*.npz`. Run times are wall-clock times (CPU times where marked) from the logs named or from
earlier measurements; "not timed" means no record exists. Rows that ran on Kaggle were merged locally
by the script named.

| Output | Written by | Main inputs | Run time |
|---|---|---|---|
| Fig. 1, `fig_p2_overview` | `fig_p2_overview.py` | schematic: `PREREG_P2_discoverability.md`, `data/p2/manifest.json`, `p2_generate.py`, `isotherm.py` | not timed |
| Fig. 2, `fig_p2_examples` | `fig_p2_examples.py` | `p2_figdata.json`, `p2_o1.json`, manifest, fields | not timed |
| Figs 3 and 4, `fig_p2_map`, `fig_p2_methods`; Extended Data Fig. 4, `fig_ed4_h2a` | `fig_p2_results.py` | `p2_verdicts.json`, `p2_figdata.json`, `p2_e6_modelselect.json`, manifest | about a minute |
| Fig. 5, `fig_p2_guide` | `fig_p2_guide.py` | `p2_verdicts.json`, `p2_e8_summary.json`, `p2_practical_da.json`, `p2_s1_anchor.json` | not timed |
| Extended Data Figs 1 and 2, `fig_ed1_h2b_langmuir`, `fig_ed2_h2b_step` | `fig_p2_extended.py` | `p2_verdicts.json`, `p2_figdata.json`, manifest | not timed |
| Extended Data Fig. 3, `fig_ed3_ident` | `fig_p2_extended.py` | `p2_ident_robustness.json`, `p2_verdicts.json` | not timed |
| Extended Data Fig. 5, `fig_ed5_methods` | `fig_p2_extended.py` | `p2_figdata.json`, `p2_extra_m9.json`, `p2_e2_m8.json`, `p2_extra_m1.json`, manifest | not timed |
| Extended Data Fig. 6, `fig_ed6_reaction` | `fig_p2_ed6_reaction.py` | `p2_e12b_summary.json`, `p2_e12_noisefree.json` | not timed |
| Extended Data Fig. 7, `fig_ed7_h2d` | `fig_p2_extended.py` | `p2_verdicts.json` | not timed |
| Extended Data Fig. 8, `fig_ed8_coverage` | `fig_p2_extended.py` | `p2_e3_coverage.json` | not timed |
| Extended Data Fig. 9, `fig_ed9_asrun` | `fig_p2_extended.py` | `p2_verdicts_asrun.json`, `p2_verdicts_preB90.json`, `p2_verdicts.json` | not timed |
| Stage 1 design figure, `fig_design` | `fig_p2_design.py` | schematic, no input file | not timed |
| `paper2/source_data/Source_Data_Fig{2,3,4,5}.xlsx` | `p2_source_data.py` | the inputs of Figs 2 to 5, fields included | not timed |
| `data/p2/manifest.json` and the fields | `p2_generate.py` | the design written in the script | about 30 min (`logs/p2_generate.log`) |
| `p2_verdicts.json` | `p2_analyze.py` | `p2_o1.json`, `p2_o2.json`, `p2_o2_ident.json`, `p2_o3_ident.json`, `p2_extra_{m5,m7,l2,o1ident}.json`, `p2_rstats.json`, manifest | about 1.5 h |
| `p2_extra_o1ident.json` | `p2_grid_extra.py o1ident`; recomputed by `p2_rerun_A6.sh` (A6, B89) and on Kaggle (`kaggle_b90/`, merged by `p2_b90_merge.py`; B90) | fields | 6.7 h in the grid (`p2_grid_chain.log.gz`); B90 merge and check 2 min (`logs/p2_rerun_B90.log`) |
| `p2_verdicts_preB90.json`, `p2_extra_o1ident_preB90.json` | the same two scripts before the B90 fix; unchanged since commit `d114952` | as for the files above | as for the files above |
| `p2_extra_m1.json` | `p2_grid_extra.py m1`; the four failed fits rerun by `p2_rerun_m1_B88.sh` (B88) | fields | 14.5 h in the grid (`p2_grid_chain.log.gz`); rerun 6.8 h (`logs/p2_rerun_m1_B88.log`) |
| `p2_figdata.json` | `p2_figdata.py` | `p2_verdicts.json` and the row files | 1.4 min (`logs/p2_rerun_B90.log`) |
| `p2_ident_robustness.json` | `p2_ident_robustness.py` | `p2_extra_o1ident.json`, `p2_verdicts.json`, `p2_figdata.json`, manifest | 11 s (`logs/p2_rerun_B90.log`) |
| `p2_e2_m8.json` (E2) | `p2_e2_m8.py` | fields | 8.4 h (`p2_e2_m8.log.gz`) |
| `p2_e3_coverage.json` (E3) | `p2_e3_coverage.py` | `p2_extra_o1ident.json`, `p2_o2_ident.json`, `p2_o3_ident.json`, manifest | 37 s (`logs/p2_rerun_B90.log`) |
| `p2_e4_criteria.json` (E4) | `p2_e4_criteria.py`, in three parts (`p2_e4_parallel.sh`) | the row files `p2_analyze.py` reads | 3.1 h for the parts in parallel (`logs/p2_rerun_B90.log`) |
| `p2_e6_modelselect.json` (E6) | `p2_e6_modelselect.py`, on Kaggle (`kaggle_e6/`, merged by `p2_e6_merge.py`) | fields | 3.5 h locally before B91 (`logs/p2_e6_modelselect.log`) |
| `p2_e7_stepshift.json`, `p2_e7_summary.json` (E7) | `p2_e7_stepshift.py`; identifiability rerun after B90 in three parts (`p2_e7_parallel.sh`) | fields | 6.5 h before B90 (`logs/p2_e7_stepshift.log`); rerun 1.1 h (`logs/p2_rerun_B90.log`) |
| `p2_e8_summary.json` (E8) | `p2_e8_sampling.py`, on Kaggle (`kaggle_e8/`, merged by `p2_e8_merge.py`) | fields | not timed |
| `p2_e9_summary.json` (E9) | `p2_e9_cleanforcing.py` | fields, `p2_e6_modelselect.json` | not timed |
| `p2_e10_resolution.json` (E10) | `p2_e10_resolution.py` | four cells re-solved into `scratch_e10/`, checked against the fields | not timed |
| `p2_e11_summary.json` (E11) | `p2_e11_fine.py`, on Kaggle (`kaggle_e11/`) | cells re-solved with 3,991 stored times, checked against the fields | not timed |
| `p2_e12_summary.json`, `p2_e12b_summary.json` (E12, E12b) | `p2_e12_reaction.py rows`, then `summary` (add `--variant-b` for E12b) | none: the script simulates its own system | about 18 and 17 CPU min (`logs/p2_e12.log`, `logs/p2_e12b.log`) |
| `p2_e12_noisefree.json` | `p2_e12_noisefree.py` | none | not timed |
| `p2_liba_summary.json` | `p2_liba_summary.py` | `p2_liba_fidelity.json`, from `p2_liba_fidelity.py` (fields; 39 CPU min, `logs/p2_liba.log`) | not timed |
| `p2_practical_da.json` | `p2_practical_da.py` | `data/practical_da_sources.csv` | not timed |
| `p2_s1_anchor.json` | `p2_s1_anchor.py` | published inputs written in the script | not timed |
| `p2_kh.json` | `p2_kh.py` | `p2_verdicts.json`, fields | not timed |
| `p2_noise_support.json` | `p2_noise_support.py` | `p2_o1.json` | not timed |
| `p2_m6_summary.json` | `p2_m6_summary.py` | `p2_extra_m6.json` | not timed |
| `p2_strong_exact.json` | `p2_strong_exact.py` | `p2_o1.json`, manifest | not timed |
| `p2_referee_checks.json` | `p2_referee_checks.py` | `p2_verdicts.json`, `p2_figdata.json`, `p2_e8_summary.json`, `p2_e11_summary.json`, `p2_kh.json` | not timed |

The row files (`p2_o1.json`, `p2_o2.json`, `p2_o2_ident.json`, `p2_o3_ident.json`,
`p2_extra_*.json`) come from the grid drivers listed under Layout; the grid took about three weeks
on one computer without a graphics processor.

## Pre-registration and amendments

`PREREG_P2_discoverability.md` was frozen before any discovery method ran on any grid cell.
Every grid driver refuses to run unless the pre-registration is unchanged since the latest
commit whose subject contains "FREEZE PREREG_P2".

| Commit | Date | What |
|---|---|---|
| `7dcc2fe` | 2026-10-11 09:12 | FREEZE PREREG_P2 |
| `ef3ade8` | 2026-10-12 14:17 | A1: selection split, 60 replicates, smallest effect of interest, two-thirds rule |
| `397d9ea` | 2026-10-12 14:54 | A2: oracle out of the pooled verdicts, Péclet a slicing axis, errors as failures |
| `d892ab9` | 2026-10-12 17:42 | A3: the grid runs now; reported as a pre-registered study |
| `ffc8d88` | 2026-10-12 17:53 | A4: the M1 demonstration implemented |
| `97150f6` | 2026-10-29 22:58 | A5: a 600 s cap per column solve in the O2/O3 profile (made while the grid ran) |
| `375552b` | 2026-11-01 10:49 | A6: the O1 profile's k range widened (made after the first verdicts) |
| `539d9a7` | 2026-11-08 | A7: two implementation corrections to the O1 profile recorded (B89 refinement points, B90 exact LDF update) |

Corrections after the grid started (`RETRACTIONS_P2.md`): B86 (a solve that could run for days,
fixed by A5), B87 (the O1 k range excluded three step cells; caught by the positive control;
fixed by A6), B88 (M1 now keeps its best parameters when a solve fails), B89 (the O1 profile now
refines with the pre-registered 41 points per pass), B90 (the O1 likelihood's "exact" LDF update had a
wrong coefficient, found by an independent AI-assisted review; fixed and tested against an ODE solver). All O1
identifiability rows were recomputed with A6 and B89 together, and again after B90 (on Kaggle, merged and
validated locally, `kaggle_b90/`, `p2_b90_merge.py`); the four failed M1 fits were rerun with B88.
B91 (the exploratory model-selection check E6 read each law's rate constant off a coarse grid; now
refined, and E6 rerun on Kaggle, `kaggle_e6/`, `p2_e6_merge.py`) affects no confirmatory result.
Earlier result files are kept as `results/*_asrun.json` (first run), `results/*_preB90.json` and
`results/p2_e6_modelselect_v1.json`.

**Where the history comes from.** The study began inside the repository of the author's first
paper, [ai-mof-cof-dynamics](https://github.com/abdulhamidbatayhi123/ai-mof-cof-dynamics)
(archived as [doi:10.5281/zenodo.23323685](https://doi.org/10.5281/zenodo.23323685)), and was
moved here with `git-filter-repo`, keeping every commit that touched a Paper 2 file. Dates,
authors and contents are unchanged; only the commit IDs differ. [`COMMIT_MAP.tsv`](COMMIT_MAP.tsv)
maps each original commit to its copy here (the original freeze is `d562f19`). Results files
written before the move record the original freeze commit (`fafed1b` for A4, here `ffc8d88`).

## Layout

| Path | Contents |
|---|---|
| `p2/` | harness: discovery methods, weak form, errors-in-variables, identifiability (profile likelihood), analysis estimands, success metrics |
| `p2_generate.py`, `data/p2/manifest.json` | ground-truth fields (regenerated from the manifest; the `.npz` files are not tracked) |
| `p2_observe.py` | observation models O1 to O3, noise and isotherm error |
| `p2_rstats.py` | the ground-truth quantities behind H2a's error ratio (`results/p2_rstats.json`) |
| `p2_grid_o1.py`, `p2_grid_o23.py`, `p2_grid_extra.py` | freeze-guarded grid drivers, resumable row by row |
| `run_p2_grid.sh`, `launch_p2_grid_detached.sh` | the full grid as one resumable chain |
| `p2_rerun_A6.sh`, `p2_rerun_m1_B88.sh` | the corrected recomputations (A6 + B89; B88) |
| `p2_rerun_B90.sh`, `kaggle_b90/`, `p2_b90_merge.py` | the B90 recomputation of every O1 identifiability row (Kaggle) and its local validation, then everything downstream |
| `p2_e4_parallel.sh`, `p2_e7_parallel.sh` | the last two steps of `p2_rerun_B90.sh` (E4, E7 identifiability) split into parallel parts and merged, after the machine ran out of process slots on 2026-11-09; same computation |
| `p2_analyze.py` | the pre-registered verdicts, written to `results/p2_verdicts.json` |
| `p2_compare_verdicts.py` | as-run against corrected verdicts |
| `p2_figdata.py` | per-level fractions behind the figures (`results/p2_figdata.json`) |
| `p2_e2_m8.py`, `p2_e3_coverage.py` | exploratory analyses E2 and E3 (declared in `EXPLORATORY_P2.md` before they ran) |
| `p2_e4_criteria.py`, `p2_e5_conditioning.py`, `p2_e6_modelselect.py`, `p2_e7_stepshift.py`, `p2_e8_sampling.py`, `p2_e9_cleanforcing.py`, `p2_e10_resolution.py`, `p2_e11_fine.py`, `p2_e12_reaction.py` | post-verdict analyses E4 to E12, each declared in `EXPLORATORY_P2.md` before it ran |
| `p2_e12_noisefree.py`, `p2_diag_e9_noisefree.py` | the diagnostics made after E12/E12b and after E9, not declared in advance (labelled so) |
| `kaggle_e6/`, `p2_e6_merge.py`, `kaggle_e8/`, `p2_e8_merge.py`, `kaggle_e11/` | E6, E8 and E11 on Kaggle: kits, kernels, queues and merges (E6 and E8 with local spot checks) |
| `p2_e13_infomatched.py`, `kaggle_e13/` | E13: information-matched sampling, declared in `EXPLORATORY_P2.md` before it ran (Kaggle; `results/p2_e13_summary.json`) |
| `p2_e14_pse.py`, `kaggle_e14/` | E14: parallel symbolic enumeration on the symbolic-regression subgrid, declared before it ran (Kaggle GPUs; `results/p2_e14_summary.json`) |
| `p2_practical_da.py`, `data/practical_da_sources.csv` | Da of published laboratory columns (Supplementary Table 1), from inputs printed in four studies, each with its location in the paper |
| `p2_s1_anchor.py` | the closest prior study on the Da map (PREREG_P2 s.5) |
| `p2_ident_robustness.py`, `p2_kh.py`, `p2_noise_support.py`, `p2_m6_summary.py`, `p2_referee_checks.py`, `p2_strong_exact.py`, `p2_liba_fidelity.py`, `p2_liba_summary.py` | descriptive checks made after the verdicts were seen (labelled so in the paper) |
| `p2_freeze_evidence.py` | GitHub's server-side record that the frozen pre-registration was public before the grid ran (`results/freeze_push_evidence.json`) |
| `p2_figstyle.py` | one figure style built to Nature Portfolio's artwork rules; the save step asserts them and writes each figure's provenance file |
| `fig_p2_overview.py`, `fig_p2_examples.py`, `fig_p2_results.py`, `fig_p2_guide.py` | Fig. 1; Fig. 2; Figs 3, 4 and Extended Data Fig. 4; Fig. 5 |
| `fig_p2_extended.py`, `fig_p2_ed6_reaction.py`, `fig_p2_design.py` | Extended Data Figs 1 to 3, 5 and 7 to 9; Extended Data Fig. 6; the Stage 1 design figure |
| `p2_check_prov.py` | recomputes the hashes in every `paper2/*.prov.json` and lists any figure drawn from an older script, style file or input |
| `p2_source_data.py` | Source Data for Figs 2 to 5 (`paper2/source_data/`) |
| `paper2/article.tex`, `paper2/supplementary.tex` | manuscript and Supplementary Information (`paper2/supplementary_main.tex` compiles the SI) |
| `paper2/build_p2.py` | builds both documents and runs the gates (key numbers recomputed from the results files, word and display-item limits, banned phrases, figure provenance) |
| `paper2/terminology.md` | each technical term defined once, and the banned-phrase list |
| `p2_pilot_*.py`, `p2_operating_characteristics.py` | pre-freeze pilots and power simulations |
| `p2_diag_step_*.py`, `p2_e2_diag.py` | diagnostics behind correction B87 and the E2 check |
| `tests/`, `pytest.ini` | unit and known-answer tests (`python -m pytest`; `-m "not slow"` leaves out the ten slowest) |
| `requirements_p2.txt` | the Python packages, pinned to the versions used |
| `requirements_p2_venv.txt` | the full freeze of the shared environment the runs used, kept as the record the Stage 1 manuscript cites (one line naming a local package unrelated to this study is redacted); install from `requirements_p2.txt` |
| `logs/` | run logs: field generation, the B88 and B90 reruns, E4, E6, E7, the E8 merge, Lib-A, the pre-freeze pilots and power simulations, and the test suite; the logs of the grid chain, the A6 rerun and E2 are compressed at the root (`*.log.gz`) |
| `RETRACTIONS_P2.md` | every defect found, its cause, its fix and how it was found |

`solver_fd.py`, `isotherm.py`, `fetch_real_mof_data.py` and `figstyle.py` are imported unchanged
from Paper 1 (commit `f2c960b`); the finite-difference solver is the ground truth here. Cite the
Paper 1 archive for them.

## Reproducing

Python 3.12 with `requirements_p2.txt` (install as above). PySR (M7) installs Julia through
juliapkg on first use; the runs used Julia 1.11.9. Every driver skips rows already on disk.

```bash
python p2_generate.py              # ground-truth fields from the manifest (about 30 min)
python p2_rstats.py                # delta and eps_rec per cell, behind H2a's error ratio
bash launch_p2_grid_detached.sh    # the confirmatory grid, one job at a time, resumable (about three weeks)
bash p2_rerun_A6.sh                # corrected O1 identifiability (A6 + B89), then the verdicts
bash p2_rerun_m1_B88.sh            # the four failed M1 fits, rerun with B88
bash p2_rerun_B90.sh               # O1 identifiability with the B90 fix, verdicts, figdata, robustness, E3, E4, E7
                                   # (the O1 rows ran on Kaggle: kaggle_b90/, then python p2_b90_merge.py)
python p2_e2_m8.py                 # E2; E5, E6, E9 and E10 run the same way: p2_e5_conditioning.py,
                                   # p2_e6_modelselect.py, p2_e9_cleanforcing.py, p2_e10_resolution.py
python p2_e12_reaction.py rows && python p2_e12_reaction.py summary   # E12; add --variant-b to both for E12b
python p2_e12_noisefree.py         # the noise-free diagnostic made after E12 and E12b
python p2_liba_fidelity.py && python p2_liba_summary.py
python p2_practical_da.py && python p2_s1_anchor.py && python p2_kh.py
python p2_noise_support.py && python p2_m6_summary.py && python p2_referee_checks.py
python fig_p2_overview.py && python fig_p2_examples.py && python fig_p2_results.py
python fig_p2_guide.py && python fig_p2_extended.py && python fig_p2_ed6_reaction.py
python p2_source_data.py           # Source Data for Figs 2 to 5
python paper2/build_p2.py          # article and SI, with every gate
```

E6, E8, E11, E13 and E14 ran on Kaggle (`kaggle_e6/`, `kaggle_e8/`, `kaggle_e11/`, `kaggle_e13/`, `kaggle_e14/`). The kernels and
kit datasets are private to the author's Kaggle account: to rerun them, replace the `abdulhamidbatayhi/` prefix
in the kernel metadata with your own user name and upload the kit; the merged results in `results/` are the
record. `p2_e6_merge.py`,
`p2_e8_merge.py` and `python p2_e11_fine.py summary` merge the downloaded parts into `results/`.

## Notes on result files

- `results/p2_verdicts.json` `positive_control.<isotherm>.n_success` and `.n_ident` are the NUMBERS OF ROWS
  evaluated (estimation replicates at the lowest Da, sigma = eps = 0), not the numbers that succeeded; the
  fractions are `success_fraction` and `identifiable_fraction`.
- The exploratory and post-verdict analyses E1 to E14 are declared in `EXPLORATORY_P2.md`. E2 to E14
  ran after their declarations and their results are in `results/`; E1 needs a graphics processor and
  has not run.

## Licence and citation

MIT (see `LICENSE`). Citation metadata is in `CITATION.cff`.

## Use of AI

The author used a generative AI assistant (Claude, Anthropic; through the Claude Code and Claude desktop
applications, September to November 2026) as a tool to assist with
drafting and language editing, with writing and checking code, and with checking
bibliographic records. The author designed the study, made every scientific decision,
reviewed and edited all content, and takes full responsibility for it.
