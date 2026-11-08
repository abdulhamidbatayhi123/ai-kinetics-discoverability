# When can AI discover adsorption kinetics?

Code, pre-registration, results and manuscript of a pre-registered computational study by
Abdulhamid Batayhi (Yıldız Technical University, ORCID
[0009-0007-0374-6755](https://orcid.org/0009-0007-0374-6755)).

Archived on Zenodo: [doi:10.5281/zenodo.23325994](https://doi.org/10.5281/zenodo.23325994)
(all versions); release v0.1-prereg, the state before the confirmatory grid, is
[doi:10.5281/zenodo.23325995](https://doi.org/10.5281/zenodo.23325995).

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
| H2b, discovery vs identifiability | "discovery fails before identifiability" in all 30 slices with both boundaries; gap 1.6 to 3.4 decades of Da |
| H2a, one error ratio places the boundary | no verdict: one of twelve conditions has a crossing |
| H2c, errors-in-variables moves the boundary | no verdict: no slice has a boundary for both estimators |
| H2d, loading-dependent rate (exploratory) | found almost only at Da = 1 |

The first-run verdicts are kept beside them (`results/p2_verdicts_asrun.json`); the corrections
between the two are listed below and in `RETRACTIONS_P2.md`.

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
wrong coefficient, found by an independent review; fixed and tested against an ODE solver). All O1
identifiability rows were recomputed with A6 and B89 together, and again after B90 (on Kaggle, merged and
validated locally, `kaggle_b90/`, `p2_b90_merge.py`); the four failed M1 fits were rerun with B88.
Earlier result files are kept as `results/*_asrun.json` (first run) and `results/*_preB90.json`.

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
| `p2_grid_o1.py`, `p2_grid_o23.py`, `p2_grid_extra.py` | freeze-guarded grid drivers, resumable row by row |
| `run_p2_grid.sh`, `launch_p2_grid_detached.sh` | the full grid as one resumable chain |
| `p2_rerun_A6.sh`, `p2_rerun_m1_B88.sh` | the corrected recomputations (A6 + B89; B88) |
| `p2_analyze.py` | the pre-registered verdicts, written to `results/p2_verdicts.json` |
| `p2_compare_verdicts.py` | as-run against corrected verdicts |
| `p2_figdata.py` | per-level fractions behind the figures (`results/p2_figdata.json`) |
| `p2_e2_m8.py`, `p2_e3_coverage.py` | exploratory analyses E2 and E3 (declared in `EXPLORATORY_P2.md` before they ran) |
| `p2_ident_robustness.py` | descriptive checks made after the verdicts were seen (labelled so in the paper) |
| `p2_figstyle.py` | one figure style built to Nature Portfolio's artwork rules; the save step asserts them |
| `fig_p2_overview.py`, `fig_p2_results.py`, `fig_p2_extended.py` | Figure 1, Figures 2 to 4, Extended Data figures |
| `paper2/article.tex`, `paper2/supplementary.tex` | manuscript and Supplementary Information |
| `paper2/build_p2.py` | builds both documents and runs the gates (key numbers recomputed from the results files, word and display-item limits, banned phrases, figure provenance) |
| `paper2/terminology.md` | each technical term defined once, and the banned-phrase list |
| `p2_pilot_*.py`, `p2_operating_characteristics.py` | pre-freeze pilots and power simulations |
| `p2_diag_*.py`, `p2_e2_diag.py` | diagnostics behind corrections B87 and the E2 check |
| `tests/` | `python -m pytest tests -q` |
| `RETRACTIONS_P2.md` | every defect found, its cause, its fix and how it was found |

`solver_fd.py`, `isotherm.py`, `fetch_real_mof_data.py` and `figstyle.py` are imported unchanged
from Paper 1 (commit `f2c960b`); the finite-difference solver is the ground truth here. Cite the
Paper 1 archive for them.

## Reproducing

Python 3.12 with the packages in `requirements_p2_venv.txt` (PySR also needs Julia).

```bash
python p2_generate.py                 # ground-truth fields from the manifest
bash launch_p2_grid_detached.sh       # the confirmatory grid, one job at a time, resumable
bash p2_rerun_A6.sh                   # corrected O1 identifiability, then the verdicts
python p2_figdata.py                  # per-level fractions for the figures
python fig_p2_overview.py && python fig_p2_results.py && python fig_p2_extended.py
python paper2/build_p2.py             # article + SI, with every gate
```

The grid took about three weeks on one computer without a graphics processor; every driver
skips rows already on disk.

## Notes on result files

- `results/p2_verdicts.json` `positive_control.<isotherm>.n_success` and `.n_ident` are the NUMBERS OF ROWS
  evaluated (estimation replicates at the lowest Da, sigma = eps = 0), not the numbers that succeeded; the
  fractions are `success_fraction` and `identifiable_fraction`.
- Exploratory and post-verdict analyses (E1-E7) are declared in `EXPLORATORY_P2.md`, each before it ran.

## Licence and citation

MIT (see `LICENSE`). Citation metadata is in `CITATION.cff`.

## Use of AI

The author used a generative AI assistant (Claude, Anthropic) as a tool to assist with
drafting and language editing, with writing and checking code, and with checking
bibliographic records. The author designed the study, made every scientific decision,
reviewed and edited all content, and takes full responsibility for it.
