# When can AI discover adsorption kinetics?

Code, pre-registration and results for Paper 2 of an AI-for-adsorption research programme by
Abdulhamid Batayhi (Yıldız Technical University, ORCID
[0009-0007-0374-6755](https://orcid.org/0009-0007-0374-6755)).

The study asks when equation-discovery methods recover the kinetic law of a fixed-bed
adsorption column from its data, and whether that boundary is set by the methods or by
identifiability. Nine methods (sparse regression, best-subset BIC, errors-in-variables,
SINDy-PI, symbolic regression, a universal differential equation and others) are compared
over a grid of noise, Damköhler and Péclet numbers and three observation models, against a
profile-likelihood identifiability boundary.

## Pre-registration

`PREREG_P2_discoverability.md` was frozen before any discovery method ran on any grid cell,
and amended four times (its §9), each time before the runs the amendment governs:

| Commit | Date | What |
|---|---|---|
| `7dcc2fe` | 2026-10-11 09:12 | FREEZE PREREG_P2 |
| `ef3ade8` | 2026-10-12 14:17 | A1: selection split, 60 replicates, smallest effect of interest |
| `397d9ea` | 2026-10-12 14:54 | A2: oracle out of the pooled verdicts, Péclet a slicing axis, errors as failures |
| `d892ab9` | 2026-10-12 17:42 | A3: the grid runs now; reported as a pre-registered study |
| `ffc8d88` | 2026-10-12 17:53 | A4: the M1 demonstration implemented |

Every grid driver refuses to run unless the pre-registration is unchanged since the latest
commit whose subject contains "FREEZE PREREG_P2".

**Where the history comes from.** The study began inside the repository of the author's
first paper, [ai-mof-cof-dynamics](https://github.com/abdulhamidbatayhi123/ai-mof-cof-dynamics)
(archived as [doi:10.5281/zenodo.23323685](https://doi.org/10.5281/zenodo.23323685)), and was
moved here with `git-filter-repo`, keeping every commit that touched a Paper 2 file. Dates,
authors and contents are unchanged; only the commit IDs differ. The original commits stay
public in that repository (the original freeze is `d562f19`), and
[`COMMIT_MAP.tsv`](COMMIT_MAP.tsv) maps each original commit to its copy here. Results files
written before the move record the original freeze commit (`fafed1b` for A4, here `ffc8d88`).

## Layout

| Path | Contents |
|---|---|
| `p2/` | harness: kinetic forms, discovery methods, analysis estimands, I/O |
| `p2_generate.py`, `data/p2/manifest.json` | ground-truth fields (regenerated from the manifest; the `.npz` files are not tracked) |
| `p2_observe.py` | observation models O1 to O3 |
| `p2_grid_o1.py`, `p2_grid_o23.py`, `p2_grid_extra.py` | freeze-guarded grid drivers, resumable cell by cell |
| `run_p2_grid.sh`, `launch_p2_grid_detached.sh` | the full grid as one resumable chain |
| `p2_analyze.py` | verdicts, written to `results/p2_verdicts.json` |
| `p2_pilot_*.py`, `p2_operating_characteristics.py` | pre-freeze pilots and power simulations |
| `paper2/` | manuscript |
| `tests/` | `python -m pytest tests -q` |
| `RETRACTIONS_P2.md` | every defect found, and its fix |

`solver_fd.py`, `isotherm.py`, `fetch_real_mof_data.py` and `figstyle.py` are imported
unchanged from Paper 1 (commit `f2c960b`); the finite-difference solver is the ground truth
here. Cite the Paper 1 archive for them.

## Running

Python 3.12 with the packages in `requirements_p2_venv.txt` (PySR also needs Julia). Then

```bash
bash run_p2_grid.sh status
bash launch_p2_grid_detached.sh
```

The chain runs one job at a time, writes a marker per finished step in
`results/.p2_grid_done/` and resumes where it stopped.

## Licence and citation

MIT (see `LICENSE`). Citation metadata is in `CITATION.cff`.

## Use of AI

The author used a generative AI assistant (Claude, Anthropic) as a tool to assist with
drafting and language editing, with writing and checking code, and with checking
bibliographic records. The author designed the study, made every scientific decision,
reviewed and edited all content, and takes full responsibility for it.
