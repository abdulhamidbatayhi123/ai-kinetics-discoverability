"""B90: merge the six Kaggle parts into results/p2_extra_o1ident.json and validate them.

Checks (any failure exits 1 and writes nothing):
  - the parts hold exactly the 51,840 expected keys (54 L1 main-grid cells x 4 sigma x 4 eps x 60 reps),
    each once;
  - a random sample of rows (default 24, fixed seed) recomputed locally with the same code
    (p2_observe.observe + p2.identifiability.profile_interval_o1) agrees: same success, and lo, hi equal
    to a relative 1e-6 (or the same error text).
The merged file carries the freeze commit the local drivers would write (p2_grid_o1.frozen()).

    python p2_b90_merge.py [n_check]
"""
import json
import os
import random
import sys

import numpy as np

from p2.io_utils import write_atomic

PARTS = [f"kaggle_b90/out/k{p}/o1ident_part{p}.json" for p in range(6)]
OUT = "results/p2_extra_o1ident.json"


def expected_keys(cells):
    from p2_grid_o1 import EPSS, N_REP, SIGMAS
    names = sorted(n for n, c in cells.items() if c["law"] == "L1" and c["iso"] != "langmuir_iso" and not c.get("refined"))
    return {f"{n}|{s}|{e}|{r}|profile|o1" for n in names for s in SIGMAS for e in EPSS for r in range(N_REP)}


def recompute(key, cells):
    from p2.identifiability import identifiable, profile_interval_o1
    from p2_observe import observe
    name, s, e, rep, _, _ = key.split("|")
    s, e, rep = float(s), float(e), int(rep)
    obs = observe(name, rep, s, e, "O1")
    ch = obs["channels"]
    sq = max(s, 1e-4) * float(np.ptp(ch["q"]))
    try:
        lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
        return {"success": bool(identifiable(lo, hi, cells[name]["k_LDF"])), "interval": {"lo": lo, "hi": hi}}
    except Exception as ex:
        return {"success": False, "error": f"{type(ex).__name__}: {ex}"}


def main():
    n_check = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    rows, seen = {}, 0
    for p in PARTS:
        part = json.load(open(p))["rows"]
        seen += len(part)
        rows.update(part)
    want = expected_keys(cells)
    if seen != len(rows) or set(rows) != want:
        sys.exit(f"FAIL keys: {seen} rows read, {len(rows)} unique, {len(want)} expected, "
                 f"missing {len(want - set(rows))}, extra {len(set(rows) - want)}")
    random.seed(90)
    bad = []
    for key in random.sample(sorted(rows), n_check):
        loc, kag = recompute(key, cells), rows[key]
        if "error" in loc or "error" in kag:
            ok = loc.get("error") == kag.get("error")
        else:
            ok = (loc["success"] == kag["success"] and
                  all(abs(loc["interval"][x] - kag["interval"][x]) <= 1e-6 * abs(loc["interval"][x]) for x in ("lo", "hi")))
        print(("ok   " if ok else "DIFF ") + key, flush=True)
        if not ok:
            bad.append((key, loc, kag))
    if bad:
        sys.exit(f"FAIL validation: {len(bad)} of {n_check} sampled rows differ, e.g. {bad[0]}")
    from p2_grid_o1 import frozen
    write_atomic({"freeze_commit": frozen()[1], "source": "Kaggle B90 rerun (kaggle_b90/), validated locally",
                  "rows": rows}, OUT)
    n_err = sum("error" in r for r in rows.values())
    print(f"MERGED {len(rows)} rows ({n_err} error rows), {n_check} sampled rows match -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
