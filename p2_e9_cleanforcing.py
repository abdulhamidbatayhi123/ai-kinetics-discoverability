"""E9 (post hoc, declared in EXPLORATORY_P2.md before running): E6 with noise-free forcing.

E6 (p2_e6_modelselect.select, unchanged) drives each candidate law with q*(t) computed from the observed
c and T. Here q*(t) is computed from the noise-free c and T at the same probes and times
(p2_observe.observe with sigma = 0, same replicate), while q is observed with noise exactly as in E6.
Subgrid: O1, both isotherms, Pe ~94, Da 31.6, 100, 316, 1000, sigma 0.5 and 2 %, eps 0, replicates
15..59 (720 rows). Writes results/p2_e9_cleanforcing.json (resumable row by row) and
results/p2_e9_summary.json.

    python p2_e9_cleanforcing.py
"""
import json
import os
import statistics
import sys

import numpy as np

from p2.io_utils import write_atomic
from p2_e6_modelselect import select

OUT = "results/p2_e9_cleanforcing.json"
SUMMARY = "results/p2_e9_summary.json"
E6 = "results/p2_e6_modelselect.json"
DAS = ("31.6", "100", "316", "1e+03")


def todo(cells):
    return [(n, s, r) for n, c in sorted(cells.items())
            if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0
            and not c.get("refined") and n.split("_da")[1] in DAS
            for s in (0.005, 0.02) for r in range(15, 60)]


def summarise(res):
    e6 = json.load(open(E6))["rows"]
    out = {}
    for key, row in res["rows"].items():
        name, s, r = key.split("|")
        cell = out.setdefault(f"{name}|{s}", {"n": 0, "ldf_clean": 0, "ldf_e6": 0, "errors": 0,
                                               "ll": {"ldf": [], "qdf": [], "pso": []}})
        cell["n"] += 1
        cell["ldf_e6"] += bool(e6[f"{name}|{s}|0.0|{r}"].get("success"))
        if "error" in row:
            cell["errors"] += 1
            continue
        cell["ldf_clean"] += row["best"] == "ldf"
        for law in cell["ll"]:
            cell["ll"][law].append(row["fits"][law]["ll"])
    for cell in out.values():
        cell["frac_clean"] = cell["ldf_clean"] / cell["n"]
        cell["frac_e6"] = cell["ldf_e6"] / cell["n"]
        cell["median_ll"] = {k: statistics.median(v) for k, v in cell.pop("ll").items() if v}
    return out


def main():
    from p2_observe import observe
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}
    jobs = todo(cells)
    assert len(jobs) == 720, len(jobs)
    for i, (name, s, r) in enumerate(jobs):
        key = f"{name}|{s}|{r}"
        if key in res["rows"]:
            continue
        try:
            obs = observe(name, r, s, 0.0, "O1")
            ch = obs["channels"]
            clean = observe(name, r, 0.0, 0.0, "O1")["channels"]
            sq = max(s, 1e-4) * float(np.ptp(ch["q"]))          # E6's noise SD rule, unchanged
            best, fits = select(obs["t"], list(clean["c"]), list(ch["q"]), obs["qstar_meas"], sq,
                                Ts=list(clean["T"]))
            k0 = cells[name]["k_LDF"]
            res["rows"][key] = {"best": best, "fits": fits, "success": best == "ldf",
                                "success_k": best == "ldf" and 0.5 * k0 <= fits["ldf"]["k_hat"] <= 2 * k0}
        except Exception as ex:          # recorded, never dropped
            res["rows"][key] = {"success": False, "success_k": False, "error": f"{type(ex).__name__}: {ex}"}
        if i % 45 == 44:
            write_atomic(res, OUT)
            print(f"{i + 1}/{len(jobs)} {name}", flush=True)
    write_atomic(res, OUT)
    write_atomic(summarise(res), SUMMARY)
    print("E9 done:", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    sys.exit(main())
