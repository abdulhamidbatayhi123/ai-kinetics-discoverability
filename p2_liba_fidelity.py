"""Lib-A held-out fidelity (PREREG_P2 s.3 "Lib-A (agnostic)" and s.4.3 "Lib-A fidelity").

The pre-registration declares Lib-A = Lib-B without the measured isotherm q*_meas. Under L1 the true
law is not representable in Lib-A, so Lib-A "is reported as held-out fidelity only": the relative RMS
error of the predicted dq/dt (strong form) on the held-out probes (every 5th), per cell
(p2/metric.py:heldout_fidelity). This metric was declared before the freeze but no driver computed it
before the verdicts; this script is written and committed before it is first run (ledger entry in
RETRACTIONS_P2.md / Supplementary Note 1, deviations). It enters no hypothesis.

Choices fixed here, before the first run (the pre-registration leaves them open):
- cells: every L1 main-grid cell (Langmuir and step, 9 Da x 3 Pe = 54 cells); observation O1;
- noise sigma in {0, 0.5, 2, 5} %; isotherm error does not apply to Lib-A (no q*), so eps = 0;
- replicates 0-19 (the 20 of PREREG s.4; the noise draw is the grid's, p2_observe.observe);
- solvers: the three sparse solvers of the grid (best_subset = M4, stlsq = M2b, ensemble = M3), strong form;
- training rows: probes j with j % 5 != 2; held-out probes j % 5 == 2 (p2/run_o1.py HOLDOUT_EVERY rule);
- target of the score: the Savitzky-Golay dq/dt of the OBSERVED q on the held-out probes (what a user
  has), and, as a second column, the same derivative of the noise-free q;
- comparator, reported beside it: the same fit with Lib-B (q*_meas included, eps = 0).

    python p2_liba_fidelity.py [--smoke]   ->  results/p2_liba_fidelity.json
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

from p2.features import derivative, lib_b
from p2.metric import heldout_fidelity
from p2.run_o1 import HOLDOUT_EVERY, SOLVERS
from p2_observe import load_cell, observe, N_T, N_PROBE
from p2.io_utils import write_atomic

SIGMAS = (0.0, 0.005, 0.02, 0.05)
N_REP = 20
OUT = "results/p2_liba_fidelity.json"


def lib_a(c, q, T, qstar):
    F = lib_b(c, q, T, qstar)
    F.pop("qstar")
    return F


def fit_predict(obs, true_q, lib, solver):
    t, ch = obs["t"], obs["channels"]
    n = ch["q"].shape[0]
    held = [j for j in range(n) if j % HOLDOUT_EVERY == HOLDOUT_EVERY // 2]
    tr = [j for j in range(n) if j not in held]

    def block(j):
        c, q, T = ch["c"][j], ch["q"][j], ch["T"][j]
        return lib(c, q, T, obs["qstar_meas"](c, T)), derivative(q, t)

    Btr = [block(j) for j in tr]
    F = {k: np.concatenate([B[0][k] for B in Btr]) for k in Btr[0][0]}
    co = SOLVERS[solver](F, np.concatenate([B[1] for B in Btr]))
    pred, y_obs, y_true = [], [], []
    for j in held:
        Fj, yj = block(j)
        pred.append(sum(co.get(k, 0.0) * Fj[k] for k in Fj))
        y_obs.append(yj)
        y_true.append(derivative(true_q[j], t))
    pred, y_obs, y_true = map(np.concatenate, (pred, y_obs, y_true))
    return heldout_fidelity(pred, y_obs), heldout_fidelity(pred, y_true), sorted(co)


def main():
    smoke = "--smoke" in sys.argv
    man = json.load(open(os.path.join("data", "p2", "manifest.json")))["cells"]
    names = sorted(n for n, m in man.items() if m["law"] == "L1" and m["iso"] in ("langmuir", "step"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    res = {"script": "p2_liba_fidelity.py", "commit_at_start": commit, "n_rep": N_REP, "rows": {}}
    if smoke:
        names = names[:1]
    t0 = time.process_time()
    for name in names:
        f, _ = load_cell(name)
        it = np.linspace(0, len(f["t"]) - 1, N_T).round().astype(int)
        iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
        true_q = f["q"][np.ix_(iz, it)].astype(float)
        for sigma in SIGMAS:
            for rep in range(2 if smoke else N_REP):
                obs = observe(name, rep, sigma, 0.0, "O1")
                for solver in SOLVERS:
                    for libname, lib in (("A", lib_a), ("B", lib_b)):
                        fo, ft, sup = fit_predict(obs, true_q, lib, solver)
                        res["rows"][f"{name}|{sigma}|{rep}|{solver}|{libname}"] = {
                            "fid_obs": fo, "fid_true": ft, "support": sup}
        print(name, f"{time.process_time() - t0:.0f} CPU s", flush=True)
        if not smoke:
            write_atomic(res, OUT)
    if smoke:
        for k, v in list(res["rows"].items())[:12]:
            print(k, v)
        return
    write_atomic(res, OUT)


if __name__ == "__main__":
    main()
