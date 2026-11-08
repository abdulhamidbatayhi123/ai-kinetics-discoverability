"""E6 after B91: merge the five Kaggle parts into results/p2_e6_modelselect.json and validate them.

Checks (any failure exits 1 and writes nothing): exactly the 3,240 expected keys of the E6 subgrid,
each once; a fixed-seed sample of rows (default 6) recomputed locally with p2_e6_modelselect.select
agrees on the chosen law and on every law's log-likelihood to a relative 1e-6.

    python p2_e6_merge.py [n_check]
"""
import json
import random
import sys

import numpy as np

from p2.io_utils import write_atomic

PARTS = [f"kaggle_e6/out/k{p}/e6_part{p}.json" for p in range(5)]
OUT = "results/p2_e6_modelselect.json"


def main():
    n_check = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    names = sorted(n for n, c in cells.items()
                   if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined"))
    want = {f"{n}|{s}|{e}|{r}" for n in names for s in (0.005, 0.02) for e in (0.0, 0.02) for r in range(15, 60)}
    rows, seen = {}, 0
    for p in PARTS:
        part = json.load(open(p))["rows"]
        seen += len(part)
        rows.update(part)
    if seen != len(rows) or set(rows) != want:
        sys.exit(f"FAIL keys: {seen} read, {len(rows)} unique, {len(want)} expected")
    from p2_e6_modelselect import select
    from p2_observe import observe
    random.seed(91)
    bad = []
    for key in random.sample(sorted(rows), n_check):
        name, s, e, r = key.split("|")
        obs = observe(name, int(r), float(s), float(e), "O1")
        ch = obs["channels"]
        best, fits = select(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"],
                            max(float(s), 1e-4) * float(np.ptp(ch["q"])), Ts=list(ch["T"]))
        kag = rows[key]
        ok = "error" not in kag and best == kag["best"] and all(
            abs(fits[n]["ll"] - kag["fits"][n]["ll"]) <= 1e-6 * abs(fits[n]["ll"]) for n in fits)
        print(("ok   " if ok else "DIFF ") + key, best, kag.get("best"), flush=True)
        if not ok:
            bad.append(key)
    if bad:
        sys.exit(f"FAIL validation: {bad}")
    write_atomic({"source": "Kaggle E6 rerun after B91 (kaggle_e6/), validated locally", "rows": rows}, OUT)
    print(f"MERGED {len(rows)} rows ({sum('error' in v for v in rows.values())} error rows) -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
