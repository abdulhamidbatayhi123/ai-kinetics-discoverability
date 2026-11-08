"""E6 (EXPLORATORY_P2; corrected after B91) on Kaggle: model selection among three rate laws.

Runs p2_e6_modelselect.select exactly as p2_e6_modelselect.main does, for the assigned
(cell, sigma, eps) groups, estimation replicates 15..59; rows keyed "<cell>|<sigma>|<eps>|<rep>"
with {"best", "fits", "success", "success_k"} or {"success": False, "success_k": False, "error"}.
Groups run in parallel (four processes).

    python e6_runner.py <kit_dir> <out_json> <cell>|<sigma>|<eps> [...]
"""
import json
import os
import sys
from multiprocessing import Pool


def run_group(args):
    kit, group = args
    os.chdir(kit)
    sys.path.insert(0, kit)
    import numpy as np
    from p2_e6_modelselect import select
    from p2_observe import observe
    name, s, e = group.split("|")
    s, e = float(s), float(e)
    k0 = json.load(open("data/p2/manifest.json"))["cells"][name]["k_LDF"]
    rows = {}
    for r in range(15, 60):
        key = f"{name}|{s}|{e}|{r}"
        try:
            obs = observe(name, r, s, e, "O1")
            ch = obs["channels"]
            sq = max(s, 1e-4) * float(np.ptp(ch["q"]))
            best, fits = select(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
            rows[key] = {"best": best, "fits": fits, "success": best == "ldf",
                         "success_k": best == "ldf" and 0.5 * k0 <= fits["ldf"]["k_hat"] <= 2 * k0}
        except Exception as ex:          # recorded, never dropped
            rows[key] = {"success": False, "success_k": False, "error": f"{type(ex).__name__}: {ex}"}
    print("group done", group, flush=True)
    return group, rows


def main():
    kit, out, groups = sys.argv[1], sys.argv[2], sys.argv[3:]
    res = {"rows": {}, "groups": [], "note": "E6 after B91 (k refined, NSUB substeps)"}
    with Pool(4) as pool:
        for g, rows in pool.imap_unordered(run_group, [(kit, g) for g in groups]):
            res["rows"].update(rows)
            res["groups"].append(g)
            json.dump(res, open(out, "w"))
    print("DONE", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    main()
