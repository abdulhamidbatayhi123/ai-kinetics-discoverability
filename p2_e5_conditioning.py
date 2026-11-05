"""E5 (post-verdict, declared in EXPLORATORY_P2.md before running): conditioning of the candidate
library against Da. For every L1 main-grid cell, the O1 observation at sigma = eps = 0 (replicate
15, the first estimation replicate) is read through p2_observe.observe exactly as the methods see
it; Lib-B (p2.features.lib_b) is built over all probes and times; the constant column is dropped
and each remaining column standardised (zero mean, unit SD). Reported: the condition number of that
matrix (largest over smallest singular value) and the smallest singular value relative to the
largest of the two-column block {q, q*} (how nearly the true law's two terms are collinear).
Writes results/p2_e5_conditioning.json.

    python p2_e5_conditioning.py
"""
import json

import numpy as np

from p2.features import lib_b
from p2.io_utils import write_atomic
from p2_observe import observe


def cond(cols):
    X = np.column_stack(cols)
    X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1.0)
    s = np.linalg.svd(X, compute_uv=False)
    return float(s[0] / s[-1]) if s[-1] > 0 else float("inf"), float(s[-1] / s[0])


def main():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    out = {"_what": __doc__.splitlines()[0], "cells": {}}
    for name, c in sorted(cells.items()):
        if c["law"] != "L1" or c["iso"] == "langmuir_iso" or c.get("refined"):
            continue
        obs = observe(name, 15, 0.0, 0.0, "O1")
        ch = obs["channels"]
        c_, q_, T_ = (np.concatenate(ch[k]) for k in ("c", "q", "T"))
        qs = obs["qstar_meas"](c_, T_)
        F = lib_b(c_, q_, T_, qs)
        names = [k for k in F if k != "1"]
        k_all, _ = cond([F[k] for k in names])
        _, pair = cond([F["q"], F["qstar"]])
        out["cells"][name] = {"iso": c["iso"], "pe_mult": c["pe_mult"], "Da": c["Da"],
                              "cond_library": k_all, "q_qstar_min_over_max_sv": pair}
        print(f"{name:<28} cond {k_all:10.3g}  q/q* sv ratio {pair:.3g}", flush=True)
    write_atomic(out, "results/p2_e5_conditioning.json")


if __name__ == "__main__":
    main()
