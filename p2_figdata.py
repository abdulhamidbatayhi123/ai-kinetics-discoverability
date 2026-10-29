"""Paper 2 figure data: the per-level fractions that Figures 2-4 draw and that
results/p2_verdicts.json does not store (it keeps boundaries, intervals and words only;
p2_analyze.py lines 225-229, 142-143, 302-304).

Pure helpers. Every filter is p2_analyze.py's own (_parse, _est, _outcome, and the
main-grid rule of _main_grid: refined H2c cells are left out), so each fraction drawn comes
from exactly the replicates its boundary was estimated on: the ESTIMATION replicates
(rep >= N_SEL), an error row counted as a failure (A2). The best method of every H2b slice
and every H2a condition is READ from p2_verdicts.json, never re-selected here. The only
fit made here is a display curve: the same unpenalised logistic regression in log10 x as
p2.analysis._fit, stored as (w, c) with P = 1 / (1 + exp(-(w x + c))).

Reads (each loaded on its own and released before the next, for memory):
  data/p2/manifest.json          cells: Da, iso, law, pe_mult, refined
  results/p2_verdicts.json       H2b[slice]["best_method"]; the H2a condition keys
                                 (H2a["rstar"] and H2a["no_crossing"], "obs|iso|pe=X|method|form")
  results/p2_o1.json             O1 rows (M2, M2b, M3, M4)   -> Fig 2 discovery, Fig 3 O1, Fig 4
  results/p2_extra_m7.json       M7 rows, merged into O1 exactly as p2_analyze.main() does
  results/p2_extra_o1ident.json  O1 identifiability rows ('profile|o1') -> Fig 2
  results/p2_o2.json             O2 rows                      -> Fig 3 (O2 conditions)
  results/p2_rstats.json         delta, eps_rec per cell      -> R for Fig 3
  results/p2_extra_m5.json       M5 rows (the oracle)         -> Fig 4 only
  results/p2_extra_m9.json       M9 rows (its own target)     -> Fig 4 only
A missing file is skipped and listed under "_missing".

Writes results/p2_figdata.json:
  {"h2b": {slice: {"best_method", "disc": [[Da, n_success, n], ...] | None, "disc_fit",
                   "ident": [[Da, n_ident, n], ...], "ident_fit"}},
   "h2a": {condition: {"levels": [[R, n_success, n], ...], "fit"}},
   "methods": {slice: {"method|form": [[Da, n_success, n], ...]}},
   "_reads": [...], "_missing": [...]}

    python p2_figdata.py      # after p2_analyze.py; loads the large row files one by one
"""
import gc
import json
import os
from collections import defaultdict

import numpy as np

from p2_analyze import _est, _outcome, _parse

VERDICTS = "results/p2_verdicts.json"
MANIFEST = "data/p2/manifest.json"
OUT = "results/p2_figdata.json"


def parse_slice(key):
    """'sigma=0.02|eps=0.005|langmuir|pe=1.0' (p2_analyze.py line 212) -> (0.02, 0.005, 'langmuir', 1.0)."""
    s, e, iso, pe = key.split("|")
    return float(s.split("=")[1]), float(e.split("=")[1]), iso, float(pe.split("=")[1])


def parse_condition(key):
    """'O1|langmuir|pe=1.0|best_subset|weak' (p2_analyze.py line 271) -> ('O1', 'langmuir', 1.0, 'best_subset|weak')."""
    obs, iso, pe, method, form = key.split("|")
    return obs, iso, float(pe.split("=")[1]), f"{method}|{form}"


def level_counts(rows, cells, reps=_est):
    """{(cell, sigma, eps, 'method|form'): [n_success, n]} over the main grid (refined cells
    out, as p2_analyze._main_grid), the replicates passing `reps` (default: estimation set),
    an error row a failure (p2_analyze._outcome)."""
    out = defaultdict(lambda: [0, 0])
    for key, r in rows.items():
        name, s, e, rep, method, form = _parse(key)
        c = cells[name]
        if c.get("refined") or not reps(rep):
            continue
        t = out[(name, s, e, f"{method}|{form}")]
        t[0] += int(_outcome(r, c.get("k_LDF", np.nan), "success"))
        t[1] += 1
    return dict(out)


def slice_levels(counts, cells, sigma, eps, iso, pe, method):
    """[[Da, n_success, n], ...] by Da for one H2b slice (the keep() of p2_analyze.py lines
    213-214) and one method label; [] if the method has no rows there."""
    agg = defaultdict(lambda: [0, 0])
    for (name, s, e, m), (k, n) in counts.items():
        c = cells[name]
        if (m == method and s == sigma and e == eps and c["iso"] == iso and c["law"] == "L1"
                and c["pe_mult"] == pe):
            agg[c["Da"]][0] += k
            agg[c["Da"]][1] += n
    return [[float(d), int(agg[d][0]), int(agg[d][1])] for d in sorted(agg)]


def logistic_fit(levels, rising=False):
    """Display curve through [[x, k, n], ...]: the estimator of p2.analysis._fit (unpenalised
    logistic ML in log10 x), returned as [w, c]; None if every outcome is the same."""
    x = np.concatenate([[np.log10(v)] * n for v, k, n in levels]) if levels else np.array([])
    y = np.concatenate([[1] * k + [0] * (n - k) for v, k, n in levels]) if levels else np.array([])
    if y.size == 0 or y.all() or not y.any():
        return None
    from sklearn.linear_model import LogisticRegression
    m = LogisticRegression(penalty=None, max_iter=1000).fit(x[:, None], y.astype(int))
    return [float(m.coef_[0, 0]), float(m.intercept_[0])]


def h2b_curves(verdicts, cells, o1_counts, ident_counts):
    """Per H2b slice: the per-level success of the slice's best method (as recorded in the
    verdicts) and the per-level identifiable fraction ('profile|o1')."""
    out = {}
    for key, v in verdicts.get("H2b", {}).items():
        s, e, iso, pe = parse_slice(key)
        best = v.get("best_method")
        disc = slice_levels(o1_counts, cells, s, e, iso, pe, best) if best else None
        ident = slice_levels(ident_counts, cells, s, e, iso, pe, "profile|o1")
        out[key] = {"best_method": best, "disc": disc, "disc_fit": logistic_fit(disc) if disc else None,
                    "ident": ident, "ident_fit": logistic_fit(ident) if ident else None}
    return out


def methods_by_slice(counts, cells, slice_keys):
    """Per H2b slice: every method's per-level success (oracle and M9 included, for Fig 4)."""
    methods = sorted({m for (_, _, _, m) in counts})
    out = {}
    for key in slice_keys:
        s, e, iso, pe = parse_slice(key)
        d = {m: slice_levels(counts, cells, s, e, iso, pe, m) for m in methods}
        out[key] = {m: v for m, v in d.items() if v}
    return out


def h2a_levels(rows, cells, rstats, conditions, obs):
    """Per H2a condition of observation `obs`: [[R, n_success, n], ...], built exactly as
    p2_analyze.py lines 253-271 (the condition's best method, estimation replicates, R =
    delta / sqrt(sigma^2 + eps^2 + eps_rec^2), eps_rec = 0 on O1, sigma = eps = 0 left out
    on O1, R rounded to 12 digits)."""
    want = {}
    for cond in conditions:
        o, iso, pe, method = parse_condition(cond)
        if o == obs:
            want[(iso, pe, method)] = cond
    acc = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for key, r in rows.items():
        name, s, e, rep, method, form = _parse(key)
        c = cells[name]
        if c.get("refined") or c["law"] != "L1" or not _est(rep):
            continue
        cond = want.get((c["iso"], c["pe_mult"], f"{method}|{form}"))
        if cond is None or (obs == "O1" and s == 0.0 and e == 0.0):
            continue
        er = rstats[name]["eps_rec"] if obs == "O2" else 0.0
        eff = float(np.sqrt(s ** 2 + e ** 2 + er ** 2))
        if eff == 0:
            continue
        t = acc[cond][round(rstats[name]["delta"] / eff, 12)]
        t[0] += int(_outcome(r, np.nan, "success"))
        t[1] += 1
    out = {}
    for cond, d in acc.items():
        lv = [[float(R), int(d[R][0]), int(d[R][1])] for R in sorted(d)]
        out[cond] = {"levels": lv, "fit": logistic_fit(lv, rising=True)}
    return out


def h2a_conditions(verdicts):
    h = verdicts.get("H2a", {})
    return sorted(set(h.get("rstar", {})) | set(h.get("no_crossing", [])))


def main():
    reads, missing = [MANIFEST, VERDICTS], []

    def load(p):
        if not os.path.exists(p):
            missing.append(p)
            return {}
        reads.append(p)
        with open(p) as f:
            return json.load(f)["rows"]

    cells = json.load(open(MANIFEST))["cells"]
    verdicts = json.load(open(VERDICTS))
    conds = h2a_conditions(verdicts)
    slices = sorted(verdicts.get("H2b", {}))

    o1 = load("results/p2_o1.json")
    o1.update(load("results/p2_extra_m7.json"))
    rstats = json.load(open("results/p2_rstats.json"))["cells"]
    reads.append("results/p2_rstats.json")
    o1c = level_counts(o1, cells)
    h2a = h2a_levels(o1, cells, rstats, conds, "O1")
    del o1
    gc.collect()
    o2 = load("results/p2_o2.json")
    h2a.update(h2a_levels(o2, cells, rstats, conds, "O2"))
    del o2
    gc.collect()
    idc = level_counts(load("results/p2_extra_o1ident.json"), cells)
    gc.collect()
    allc = dict(o1c)
    for p in ("results/p2_extra_m5.json", "results/p2_extra_m9.json"):
        allc.update(level_counts(load(p), cells))
        gc.collect()
    out = {"_what": "Per-level fractions for fig_p2_results.py; written by p2_figdata.py "
                    "from the row files listed in _reads (estimation replicates only).",
           "_reads": reads, "_missing": missing,
           "h2b": h2b_curves(verdicts, cells, o1c, idc),
           "h2a": h2a,
           "methods": methods_by_slice(allc, cells, slices)}
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT, "| missing:", missing or "none")


if __name__ == "__main__":
    main()
