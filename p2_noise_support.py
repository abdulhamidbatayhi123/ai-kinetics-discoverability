"""Why success is not monotone in noise with isotherm error (descriptive check, post hoc, 2026-11-11).

Prompted by a pre-submission review: at 2 % isotherm error the best method succeeded in more
replicates with noise than without. This check reads the stored O1 rows only (no new fits): for
weak-form exact best-subset selection (M4, the best method in 34 of the 37 verdict slices) it
reports, per isotherm, Da and noise level, on the 45 estimation replicates (rep >= 15) and at each
isotherm error, the success fraction, the mean number of selected terms (at most 4) and the fraction
whose support is exactly {q, q*}. It enters no test.

    python p2_noise_support.py  ->  results/p2_noise_support.json
"""
import collections
import json

from p2.io_utils import write_atomic

SRC = "results/p2_o1.json"
OUT = "results/p2_noise_support.json"


def main():
    rows = json.load(open(SRC))["rows"]
    agg = collections.defaultdict(list)
    for key, v in rows.items():
        cell, sig, eps, rep, solver, form = key.split("|")
        if int(rep) < 15 or (solver, form) != ("best_subset", "weak"):
            continue
        iso, da = cell.split("_")[0], cell.split("_da")[1]
        pe = cell.split("_pe")[1].split("_")[0]
        s = set(v["support"])
        agg[(iso, pe, da, sig, eps)].append((bool(v["success"]), len(s), s == {"q", "qstar"}))
    out = {"source": SRC, "method": "best_subset|weak", "replicates": "rep >= 15 (45)", "cells": {}}
    for (iso, pe, da, sig, eps), a in sorted(agg.items()):
        out["cells"]["|".join((iso, pe, da, sig, eps))] = {
            "n": len(a), "success": sum(x[0] for x in a) / len(a),
            "mean_support_size": sum(x[1] for x in a) / len(a),
            "exact_support": sum(x[2] for x in a) / len(a)}
    summ = {}
    for eps in ("0.0", "0.005", "0.02", "0.05"):
        for sig in ("0.0", "0.005", "0.02", "0.05"):
            sizes = [v["mean_support_size"] for k, v in out["cells"].items()
                     if k.split("|")[3] == sig and k.split("|")[4] == eps and float(k.split("|")[2]) <= 10]
            summ[f"eps{eps}|sigma{sig}"] = {"mean_support_size_min": min(sizes), "mean_support_size_max": max(sizes)}
    out["summary_da_le_10"] = summ
    write_atomic(out, OUT)
    for k, v in summ.items():
        print(k, f"{v['mean_support_size_min']:.2f}-{v['mean_support_size_max']:.2f}")


if __name__ == "__main__":
    main()
