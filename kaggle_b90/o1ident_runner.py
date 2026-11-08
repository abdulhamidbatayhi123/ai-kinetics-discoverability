"""B90 O1 identifiability rerun on Kaggle (RETRACTIONS_P2 B90, PREREG_P2 amendment A7).

Reproduces exactly the o1ident branch of p2_grid_extra.py (commit with the corrected
p2.identifiability._ldf_exact): for every assigned main-grid L1 cell (not the isothermal control,
not refined), every sigma in SIGMAS, eps in EPSS and replicate 0..59, the O1 observation
(p2_observe.observe) is profiled with profile_interval_o1 at sq = max(sigma, 1e-4) * ptp(q), and the
row is {"success": identifiable(lo, hi, k_LDF), "sec": ..., "interval": {"lo", "hi"}}, or
{"success": False, "error": ...} on an exception (errors are failures, never dropped; A2).
Keys: "<cell>|<sigma>|<eps>|<rep>|profile|o1". Cells run in parallel (one process per cell).

    python o1ident_runner.py <kit_dir> <out_json> <cell> [<cell> ...]
"""
import json
import os
import sys
import time
from multiprocessing import Pool

SIGMAS = (0.0, 0.005, 0.02, 0.05)      # p2_grid_o1.SIGMAS
EPSS = (0.0, 0.005, 0.02, 0.05)        # p2_grid_o1.EPSS
N_REP = 60                             # p2_grid_o1.N_REP (A1)


def run_cell(args):
    kit, name = args
    os.chdir(kit)
    sys.path.insert(0, kit)
    import numpy as np
    from p2.identifiability import identifiable, profile_interval_o1
    from p2_observe import observe
    man = json.load(open("data/p2/manifest.json"))["cells"][name]
    rows, t0 = {}, time.time()
    for sigma in SIGMAS:
        for eps in EPSS:
            for rep in range(N_REP):
                key = f"{name}|{sigma}|{eps}|{rep}|profile|o1"
                obs = observe(name, rep, sigma, eps, "O1")
                t1 = time.time()
                try:
                    ch = obs["channels"]
                    sq = max(sigma, 1e-4) * float(np.ptp(ch["q"]))
                    lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]),
                                                 obs["qstar_meas"], sq, Ts=list(ch["T"]))
                    rows[key] = {"success": bool(identifiable(lo, hi, man["k_LDF"])), "sec": time.time() - t1,
                                 "interval": {"lo": lo, "hi": hi}}
                except Exception as e:      # recorded, never dropped (A2)
                    rows[key] = {"success": False, "error": f"{type(e).__name__}: {e}"}
    print(f"o1ident {name:<34} [{time.time() - t0:.0f}s]", flush=True)
    return name, rows


def main():
    kit, out, cells = sys.argv[1], sys.argv[2], sys.argv[3:]
    res = {"rows": {}, "cells": [], "note": "B90 Kaggle rerun; corrected _ldf_exact"}
    with Pool(min(4, len(cells))) as pool:
        for name, rows in pool.imap_unordered(run_cell, [(kit, c) for c in cells]):
            res["rows"].update(rows)
            res["cells"].append(name)
            json.dump(res, open(out, "w"))
    print("DONE", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    main()
