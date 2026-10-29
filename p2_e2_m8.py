"""Paper 2 exploratory E2: M8 (KAN symbolic extraction) on its declared subgrid, local CPU.

EXPLORATORY, declared in EXPLORATORY_P2.md (section E2) before this runs; that file's
commit time is the record. M8 enters NO confirmatory pool: PREREG_P2 s.3 gated M8's grid
run on cost (1144 s per fit against 300 s, results/p2_cost_gates.json) and it stays
NOT RUN in the confirmatory results. This driver runs, after the confirmatory chain has
finished, exactly the configuration PREREG_P2 s.3 declared for that run:

  p2.methods.kan_symbolic (pykan 0.2.8), raw variables V = {c, q, T, qstar}, lamb = 1e-3,
  its default steps; all Da x sigma in {0.5 %, 2 %} x eps in {0, 2 %} x both isotherms
  (langmuir, step; L1 law; not langmuir_iso, not refined cells) x Pe x1 x O1,
  3 replicates = 216 fits; success = p2.metric.success_L1.

The inputs V, y are built exactly as p2_grid_extra.py's m8 branch builds them, and the
row key, the row fields and the error handling follow p2_grid_extra.run. One job at a
time; resumable row by row (results/p2_e2_m8.json is rewritten atomically after every
fit); an exception is recorded as a failure with an "error" field, never dropped.

Refuses to run unless results/.p2_grid_done/analyze exists (the confirmatory chain,
run_p2_grid.sh, has finished). --smoke runs ONE fit on one cell to check the wiring and
writes results/tmp_e2_smoke.json instead (no chain check).

    python p2_e2_m8.py           # the 216 fits
    python p2_e2_m8.py --smoke   # one fit, wiring check
"""
import itertools
import json
import os
import subprocess
import sys
import time

import numpy as np

from p2 import methods
from p2.features import derivative
from p2.metric import success_L1
from p2_grid_extra import SUB_EPSS, SUB_REP, SUB_SIGMAS
from p2_grid_o1 import frozen
from p2_observe import observe
from p2.io_utils import write_atomic

OUT = "results/p2_e2_m8.json"
SMOKE_OUT = "results/tmp_e2_smoke.json"
CHAIN_DONE = "results/.p2_grid_done/analyze"     # run_p2_grid.sh's last done-marker
N_FITS = 216                                     # EXPLORATORY_P2.md E2; PREREG_P2 s.3 M8
SOLVER, FORM = "m8", "strong"                    # the key fields p2_grid_extra.py uses for M8


def cells(man):
    """The declared subgrid's cells: L1, langmuir or step, Pe x1, not refined
    (the filter of p2_grid_extra.run's m8 branch, with refined cells excluded)."""
    return [(n, r) for n, r in sorted(man.items())
            if r["iso"] in ("langmuir", "step") and r["law"] == "L1"
            and r["pe_mult"] == 1.0 and not r.get("refined")]


def plan(man):
    return [(name, rec, sigma, eps, rep) for name, rec in cells(man)
            for sigma, eps, rep in itertools.product(SUB_SIGMAS, SUB_EPSS, range(SUB_REP))]


def fit_m8(obs, rep):
    """M8 exactly as p2_grid_extra.py's m8 branch: raw variables stacked over the probes,
    target the Savitzky-Golay dq/dt per probe, kan_symbolic with its declared defaults."""
    V = {"c": np.concatenate(obs["channels"]["c"]), "q": np.concatenate(obs["channels"]["q"]),
         "T": np.concatenate(obs["channels"]["T"]),
         "qstar": np.concatenate([obs["qstar_meas"](c, T) for c, T in
                                  zip(obs["channels"]["c"], obs["channels"]["T"])])}
    y = np.concatenate([derivative(q, obs["t"]) for q in obs["channels"]["q"]])
    co = methods.kan_symbolic(V, y, seed=rep)
    return co, success_L1(co)


def _commit_of(path):
    return subprocess.run(["git", "log", "-1", "--format=%H", "--", path],
                          capture_output=True, text=True).stdout.strip()


def run(jobs, out):
    res = (json.load(open(out)) if os.path.exists(out) else
           {"_what": "EXPLORATORY E2 (EXPLORATORY_P2.md): M8 on its declared subgrid; "
                     "enters no confirmatory pool",
            "freeze_commit": frozen()[1], "exploratory_commit": _commit_of("EXPLORATORY_P2.md"),
            "rows": {}})
    for i, (name, rec, sigma, eps, rep) in enumerate(jobs):
        key = f"{name}|{sigma}|{eps}|{rep}|{SOLVER}|{FORM}"
        if key in res["rows"]:
            continue
        t1 = time.time()
        try:
            obs = observe(name, rep, sigma, eps, "O1")
            co, ok = fit_m8(obs, rep)
            res["rows"][key] = {"success": bool(ok), "sec": time.time() - t1,
                                "support": sorted(co),
                                "k_hat": float(-co.get("q", 0.0)),
                                "coefs": {k: float(v) for k, v in co.items()}}
        except Exception as e:   # recorded, never dropped
            res["rows"][key] = {"success": False, "sec": time.time() - t1,
                                "error": f"{type(e).__name__}: {e}"}
        write_atomic(res, out)
        r = res["rows"][key]
        print(f"m8 [{i + 1}/{len(jobs)}] {key} success={r['success']} "
              f"support={r.get('support', r.get('error'))} [{r['sec']:.0f}s]", flush=True)
    done = sum(f"{n}|{s}|{e}|{p}|{SOLVER}|{FORM}" in res["rows"] for n, _, s, e, p in jobs)
    print(f"m8 E2: {done}/{len(jobs)} rows in {out}", flush=True)


def main():
    man = json.load(open("data/p2/manifest.json"))["cells"]
    jobs = plan(man)
    assert len(jobs) == N_FITS, f"planned {len(jobs)} fits, E2 declares {N_FITS}"
    if "--smoke" in sys.argv[1:]:
        # one fit on one cell: Langmuir, Da nearest 1, sigma 2 %, eps 2 %, replicate 0
        name = min((n for n, r in cells(man) if r["iso"] == "langmuir"),
                   key=lambda n: abs(np.log(man[n]["Da"])))
        run([(name, man[name], 0.02, 0.02, 0)], SMOKE_OUT)
        return
    if not os.path.exists(CHAIN_DONE):
        sys.exit(f"REFUSED: {CHAIN_DONE} missing -- E2 runs only after the confirmatory "
                 "chain (run_p2_grid.sh) has finished, one job at a time.")
    run(jobs, OUT)


if __name__ == "__main__":
    main()
