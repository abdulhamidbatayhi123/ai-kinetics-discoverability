"""Boundaries in units of k h, the rate constant times the interval between observations (descriptive, post hoc,
2026-11-11, prompted by a pre-submission review).

Every model samples N_T = 200 times evenly over the solved horizon, so h = horizon / 199 and
k h = Da (horizon / t_stoich) / 199. The horizon ratio is read from each stored field (data/p2/*.npz, t) and
checked to be constant per Da level across isotherms and Peclet numbers. Each H2b boundary Da* is converted
with the horizon ratio of the grid level at or below it (the horizon changes only between Da = 1 and 3.16,
where no boundary in this study lies on a level boundary).

    python p2_kh.py  ->  results/p2_kh.json
"""
import json
import os

import numpy as np

from p2.io_utils import write_atomic
from p2_observe import N_T


def main():
    man = json.load(open(os.path.join("data", "p2", "manifest.json")))["cells"]
    ratio = {}
    for n, v in man.items():
        if v["law"] != "L1" or v["iso"] not in ("langmuir", "step"):
            continue
        t = np.load(os.path.join("data", "p2", n + ".npz"))["t"]
        r = float((t[-1] - t[0]) / v["t_stoich_s"])
        ratio.setdefault(round(v["Da"], 6), set()).add(round(r, 6))
    assert all(len(s) == 1 for s in ratio.values()), ratio
    levels = sorted(ratio)
    rr = {d: next(iter(ratio[d])) for d in levels}

    def kh(da):
        lev = max([d for d in levels if d <= da * (1 + 1e-9)] or [levels[0]])
        return da * rr[lev] / (N_T - 1)

    ver = json.load(open("results/p2_verdicts.json"))["H2b"]
    both = [s for s in ver.values() if s.get("gap_decades") is not None]
    disc = [s["da_disc"] for s in both]
    ident = [s["da_ident"] for s in both]
    out = {"n_t": N_T, "horizon_over_t_stoich_by_Da": {str(d): rr[d] for d in levels},
           "kh_by_level": {str(d): d * rr[d] / (N_T - 1) for d in levels},
           "n_slices": len(disc),
           "kh_at_disc_min": min(map(kh, disc)), "kh_at_disc_max": max(map(kh, disc)),
           "kh_at_ident_min": min(map(kh, ident)), "kh_at_ident_max": max(map(kh, ident))}
    write_atomic(out, "results/p2_kh.json")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
