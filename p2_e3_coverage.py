"""Paper 2 exploratory analysis E3: precision versus coverage of the identifiability criterion.

EXPLORATORY, declared in EXPLORATORY_P2.md (section E3) before this script was run. It is
descriptive only and changes no pre-registered rule: the confirmatory Da*_ident stays as
PREREG_P2 s.4.3 defines it ('practically identifiable' iff the 95 % profile interval lies
within [k/2, 2k]), and nothing here enters p2_analyze.py or results/p2_verdicts.json.

For every identifiability row (no new compute):
  (a) identifiable  -- the interval lies inside [k/2, 2k] (p2.identifiability.identifiable,
                       the pre-registered criterion, recomputed from lo, hi and the true k);
  (b) covers        -- the interval contains the true k (lo <= k <= hi).
A row with an "error" key, or without a finite interval, counts as neither (errors are
failures, never dropped; PREREG_P2 A2).

Reads:
  results/p2_extra_o1ident.json  O1, keys cell|sigma|eps|rep|profile|o1, values {'interval':
                                 {'lo','hi'}, 'success'}; true k from the manifest's k_LDF
  results/p2_o2_ident.json       O2, keys cell|sigma|eps|rep, values {'lo','hi','k','identifiable'}
  results/p2_o3_ident.json       O3, same shape as O2; may be incomplete, what exists is read
  data/p2/manifest.json          cells -> name -> Da, k_LDF
Writes results/p2_e3_coverage.json (atomically): counts per observation model, per (model, Da),
per (model, sigma, eps), the fraction of 'identifiable' rows whose interval misses k, and the
rows where a stored verdict or k disagrees with the recomputed one (should be none).

    python p2_e3_coverage.py
"""
import json
import math
import os
from collections import defaultdict

from p2.identifiability import identifiable
from p2.io_utils import write_atomic

FILES = {"O1": "results/p2_extra_o1ident.json",
         "O2": "results/p2_o2_ident.json",
         "O3": "results/p2_o3_ident.json"}
OUT = "results/p2_e3_coverage.json"
K_RTOL = 1e-9              # a stored O2/O3 k must equal the manifest's k_LDF to this tolerance


def _finite(*xs):
    return all(x is not None and math.isfinite(x) for x in xs)


def classify(r, k_true):
    """(identifiable, covers) for one row. An error row, or a row without a finite interval
    or true k, is (False, False): a failure, never dropped."""
    if "error" in r:
        return False, False
    iv = r.get("interval", r)          # O1 nests the interval; O2/O3 store lo, hi flat
    lo, hi = iv.get("lo"), iv.get("hi")
    if not _finite(lo, hi, k_true):
        return False, False
    return bool(identifiable(lo, hi, k_true)), bool(lo <= k_true <= hi)


def _empty():
    return {"n": 0, "n_error": 0, "identifiable": 0, "covers": 0,
            "identifiable_covers": 0, "identifiable_misses": 0,
            "not_identifiable_covers": 0, "not_identifiable_misses": 0}


def _add(tally, ident, cov, err):
    tally["n"] += 1
    tally["n_error"] += int(err)
    tally["identifiable"] += int(ident)
    tally["covers"] += int(cov)
    tally[("identifiable_" if ident else "not_identifiable_") + ("covers" if cov else "misses")] += 1


def _finish(tally):
    t = dict(tally)
    t["frac_identifiable_missing_k"] = (t["identifiable_misses"] / t["identifiable"]
                                        if t["identifiable"] else None)
    t["coverage"] = t["covers"] / t["n"] if t["n"] else None
    return t


def coverage(cells, rows_by_model):
    """Pure function of the manifest cells and {model: rows}. Returns the E3 summary dict."""
    per_model = defaultdict(_empty)
    per_da = defaultdict(lambda: defaultdict(_empty))
    per_se = defaultdict(lambda: defaultdict(_empty))
    mismatches = []
    unknown_cells = defaultdict(int)
    refined = defaultdict(int)
    for model, rows in rows_by_model.items():
        for key, r in rows.items():
            parts = key.split("|")
            name, sigma, eps = parts[0], float(parts[1]), float(parts[2])
            c = cells.get(name)
            if c is None:
                unknown_cells[model] += 1
                k_true, da = None, None
            else:
                k_true, da = c.get("k_LDF"), c.get("Da")
                refined[model] += int(bool(c.get("refined")))
            ident, cov = classify(r, k_true)
            err = "error" in r
            # consistency of what the drivers stored with the recomputed criterion and k
            stored = r.get("success") if model == "O1" else r.get("identifiable")
            if not err and stored is not None and bool(stored) != ident:
                mismatches.append({"model": model, "key": key, "stored": bool(stored),
                                   "recomputed": ident})
            if model != "O1" and not err and _finite(r.get("k"), k_true) \
                    and abs(r["k"] - k_true) > K_RTOL * k_true:
                mismatches.append({"model": model, "key": key, "stored_k": r["k"],
                                   "manifest_k": k_true})
            _add(per_model[model], ident, cov, err)
            _add(per_da[model][str(da)], ident, cov, err)
            _add(per_se[model][f"sigma={sigma}|eps={eps}"], ident, cov, err)
    return {
        "analysis": "E3 (exploratory, EXPLORATORY_P2.md; descriptive, no pre-registered rule changed)",
        "criterion": "identifiable iff lo >= k/2 and hi <= 2k (p2.identifiability.identifiable); "
                     "covers iff lo <= k <= hi; error rows count as neither",
        "per_model": {m: _finish(t) for m, t in per_model.items()},
        "per_model_da": {m: {da: _finish(t) for da, t in sorted(v.items(), key=lambda x: float(x[0]))}
                         for m, v in per_da.items()},
        "per_model_sigma_eps": {m: {se: _finish(t) for se, t in sorted(v.items())}
                                for m, v in per_se.items()},
        "rows_in_refined_cells": dict(refined),
        "rows_with_unknown_cell": dict(unknown_cells),
        "stored_vs_recomputed_mismatches": mismatches,
    }


def _print_table(title, table):
    print(f"\n{title}")
    print(f"  {'':<26}{'n':>7}{'err':>5}{'ident':>7}{'covers':>8}{'id&miss':>9}{'frac_id_miss':>14}")
    for label, t in table.items():
        f = t["frac_identifiable_missing_k"]
        print(f"  {label:<26}{t['n']:>7}{t['n_error']:>5}{t['identifiable']:>7}{t['covers']:>8}"
              f"{t['identifiable_misses']:>9}{('-' if f is None else f'{f:.3f}'):>14}")


def main():
    load = lambda p: json.load(open(p))["rows"] if os.path.exists(p) else {}
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    out = coverage(cells, {m: load(p) for m, p in FILES.items()})
    out["inputs"] = {m: p for m, p in FILES.items() if os.path.exists(p)}
    write_atomic(out, OUT)
    _print_table("E3 per observation model", out["per_model"])
    for m, v in out["per_model_da"].items():
        _print_table(f"E3 {m} per Da", v)
    for m, v in out["per_model_sigma_eps"].items():
        _print_table(f"E3 {m} per (sigma, eps)", v)
    print(f"\nrows in refined cells: {out['rows_in_refined_cells']}; "
          f"unknown cells: {out['rows_with_unknown_cell']}; "
          f"stored-vs-recomputed mismatches: {len(out['stored_vs_recomputed_mismatches'])}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
