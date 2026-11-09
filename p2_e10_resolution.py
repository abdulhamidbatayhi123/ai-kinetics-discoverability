"""E10 (post hoc, declared in EXPLORATORY_P2.md before running): the time resolution of the forcing behind
E6's deterministic misfit at Da >= 100.

Four cells (Pe ~94, L1; Langmuir and step; Da 100 and 1000) are re-solved with p2_generate.solve_cell,
unchanged except for 3,991 stored times (every 10th is one of the grid's 400; checked against data/p2).
On noise-free c, q, T at the 20 O1 probes, p2_e6_modelselect.select (unchanged; sigma = 1e-4 x range of q)
runs at 200, 400, 1,996 and 3,991 evenly spaced times. Fields go to a scratch directory (E10_DIR, default
scratch_e10/, not tracked), never to data/p2. Writes results/p2_e10_resolution.json.

    python p2_e10_resolution.py
"""
import json
import os
import sys

import numpy as np

import p2_generate
from p2.io_utils import write_atomic
from p2_e6_modelselect import select
from p2_observe import N_PROBE, load_cell, observe

OUT = "results/p2_e10_resolution.json"
SCRATCH = os.environ.get("E10_DIR", "scratch_e10")
CELLS = ("langmuir_L1_pe1_da100", "step_L1_pe1_da100", "langmuir_L1_pe1_da1e+03", "step_L1_pe1_da1e+03")
FINE = 3991                      # 399 * 10 + 1: the grid's 400 times are every 10th
RES = (200, 400, 1996, 3991)


def fine_field(name):
    path = os.path.join(SCRATCH, name + "_fine.npz")
    stored, man = load_cell(name)
    if not os.path.exists(path):
        p2_generate.N_SNAP = FINE
        rec, z, t, c, q, T = p2_generate.solve_cell(man["iso"], man["law"], man["pe_mult"], man["Da"])
        assert rec["horizon_t_stoich"] == man["horizon_t_stoich"], (rec["horizon_t_stoich"], man["horizon_t_stoich"])
        os.makedirs(SCRATCH, exist_ok=True)
        np.savez(path, z=z, t=t, c=c, q=q, T=T)
    f = dict(np.load(path))
    check = {}
    for ch in ("c", "q", "T"):
        a, b = f[ch][:, ::10].astype(np.float32), stored[ch]
        check[ch] = float(np.max(np.abs(a - b)) / (float(b.max() - b.min()) or 1.0))
    assert np.allclose(f["t"][::10], stored["t"], rtol=1e-5), "time grids differ"
    return f, man, check


def main():
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}, "checks": {}}
    for name in CELLS:
        f, man, check = fine_field(name)
        res["checks"][name] = check
        qstar = observe(name, 15, 0.0, 0.0, "O1")["qstar_meas"]
        iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
        # Added after the first rows (disclosed in EXPLORATORY_P2 E10 outcome): the declared 200 and 400 times are
        # evenly spaced on the fine grid and differ by up to half a grid interval from the grid's own times, so the
        # grid's exact 200 and 400 times (p2_observe's indices, x10) are run as well, for comparison with E6 and E9.
        grid = {"grid200": 10 * np.linspace(0, 399, 200).round().astype(int), "grid400": 10 * np.arange(400)}
        for n_t in RES + tuple(grid):
            key = f"{name}|{n_t}"
            if key in res["rows"]:
                continue
            it = grid[n_t] if n_t in grid else np.linspace(0, FINE - 1, n_t).round().astype(int)
            t = f["t"][it].astype(float)
            ch = {c: f[c][np.ix_(iz, it)].astype(float) for c in ("c", "q", "T")}
            sq = 1e-4 * float(np.ptp(ch["q"]))
            best, fits = select(t, list(ch["c"]), list(ch["q"]), qstar, sq, Ts=list(ch["T"]))
            top = fits[best]["ll"]
            res["rows"][key] = {"best": best, "k_ldf_over_k": fits["ldf"]["k_hat"] / man["k_LDF"],
                                "dll": {law: v["ll"] - top for law, v in fits.items()}, "fits": fits}
            write_atomic(res, OUT)
            print(key, best, {k: round(v, 1) for k, v in res["rows"][key]["dll"].items()},
                  round(res["rows"][key]["k_ldf_over_k"], 4), flush=True)
    write_atomic(res, OUT)
    print("checks", res["checks"])
    print("E10 done:", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    sys.exit(main())
