"""The sparse solvers on the grid's exact column data (post hoc, descriptive; written 2026-11-15 after a final
pre-submission review). Reads results only.

On the six exact slices (sigma = eps = 0, O1, both isotherms, three Peclet numbers) and the estimation replicates
15..59, for each solver and form: the success fraction per Da, the lowest Da from which success is 1.0 at every
higher level, and, for strong-form best-subset selection, the size of the returned support and how often it
contains the true pair {q, qstar}.

    python p2_strong_exact.py  ->  results/p2_strong_exact.json
"""
import json
from collections import Counter, defaultdict

from p2.io_utils import write_atomic

ROWS = "results/p2_o1.json"
OUT = "results/p2_strong_exact.json"


def main():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    rows = json.load(open(ROWS))["rows"]
    frac = defaultdict(lambda: defaultdict(list))      # (slice, method) -> Da -> [success]
    sizes, true_pair, n_bs = Counter(), 0, 0
    for key, r in rows.items():
        cell, s, e, rep, solver, form = key.split("|")
        if s != "0.0" or e != "0.0" or int(rep) < 15:
            continue
        c = cells[cell]
        slc = f"{c['iso']}|pe={c['pe_mult']}"
        frac[(slc, f"{solver}|{form}")][c["Da"]].append(bool(r["success"]))
        if solver == "best_subset" and form == "strong":
            n_bs += 1
            sizes[len(r["support"])] += 1
            true_pair += ("q" in r["support"] and "qstar" in r["support"])
    del rows
    out = {"slices": {}, "onset_from_da": {}, "best_subset_strong": {
        "rows": n_bs, "support_size_counts": {str(k): v for k, v in sorted(sizes.items())},
        "rows_with_true_pair": true_pair}}
    for (slc, m), by in sorted(frac.items()):
        das = sorted(by)
        f = [sum(by[d]) / len(by[d]) for d in das]
        out["slices"].setdefault(slc, {})[m] = {str(d): v for d, v in zip(das, f)}
        onset = None
        for i in range(len(das)):
            if all(x == 1.0 for x in f[i:]):
                onset = das[i]
                break
        out["onset_from_da"].setdefault(m, {})[slc] = onset
    write_atomic(out, OUT)
    print(json.dumps({"onset_from_da": out["onset_from_da"], "best_subset_strong": out["best_subset_strong"]},
                     indent=1))


if __name__ == "__main__":
    main()
