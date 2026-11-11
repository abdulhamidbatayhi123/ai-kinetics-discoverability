"""Summary of the Lib-A held-out fidelity run (p2_liba_fidelity.py -> results/p2_liba_fidelity.json).

Reported per library (A: no isotherm; B: with the measured isotherm), noise level and Da group (Da <= 10,
Da >= 31.6): the median over cells and replicates of the relative RMS error of the predicted dq/dt on the
held-out probes, against the observed-data derivative (fid_obs) and the noise-free one (fid_true), for exact
best-subset selection (M4, strong form). Grouping fixed before the run finished (2026-11-11), from the two Da
ranges the paper already uses (discovery boundaries at Da <= 13; identifiability at Da >= 43).

    python p2_liba_summary.py  ->  results/p2_liba_summary.json
"""
import collections
import json
import statistics

from p2.io_utils import write_atomic


def main():
    d = json.load(open("results/p2_liba_fidelity.json"))
    rows = d["rows"]
    agg = collections.defaultdict(list)
    cells = set()
    for k, v in rows.items():
        cell, s, rep, solver, lib = k.split("|")
        cells.add(cell)
        if solver != "best_subset":
            continue
        grp = "Da<=10" if float(cell.split("_da")[1]) <= 10 else "Da>=31.6"
        agg[(lib, s, grp)].append((v["fid_obs"], v["fid_true"]))
    out = {"source": "results/p2_liba_fidelity.json", "commit_at_start": d.get("commit_at_start"),
           "n_cells": len(cells), "solver": "best_subset (strong form)", "groups": {}}
    for (lib, s, grp), a in sorted(agg.items()):
        out["groups"][f"{lib}|sigma={s}|{grp}"] = {
            "n": len(a), "median_fid_obs": statistics.median(x[0] for x in a),
            "median_fid_true": statistics.median(x[1] for x in a)}
    write_atomic(out, "results/p2_liba_summary.json")
    for k, v in out["groups"].items():
        print(k, v["n"], round(v["median_fid_obs"], 3), round(v["median_fid_true"], 3))


if __name__ == "__main__":
    main()
