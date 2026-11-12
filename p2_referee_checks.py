"""Checks prompted by a simulated pre-submission referee round (post hoc, descriptive, 2026-11-12). Reads results only.

1. kh at each boundary, the rate constant times the interval between observations, at 200 times (E8's own 200-time
   run) and at about 2,000 (E11), for discovery, the likelihood choice among three laws and identifiability, on the
   Pe ~94 slices both runs share. h = horizon / (n_t - 1); the horizon over t_stoich is read per Da level from
   results/p2_kh.json (horizon_over_t_stoich_by_Da) using the level at or below the boundary.
2. Information-matched comparison: the gap between the likelihood choice among three candidate laws (which uses the
   same likelihood as identifiability) and identifiability, at 200 and 2,000 times.
3. Peak observed success of the best method in each of the 37 verdict slices (estimation replicates), and how many
   peak below 0.7.
4. Independent ground-truth families behind the 37 verdict slices: distinct (isotherm, Peclet) pairs.

    python p2_referee_checks.py  ->  results/p2_referee_checks.json
"""
import json
import math

from p2.io_utils import write_atomic

KH = json.load(open("results/p2_kh.json"))
RATIO = {float(k): v for k, v in KH["horizon_over_t_stoich_by_Da"].items()}


def kh(da, n_t):
    if da is None:
        return None
    lev = max([d for d in RATIO if d <= da * (1 + 1e-9)] or [min(RATIO)])
    return da * RATIO[lev] / (n_t - 1)


def main():
    e8 = json.load(open("results/p2_e8_summary.json"))
    e11 = json.load(open("results/p2_e11_summary.json"))
    V = json.load(open("results/p2_verdicts.json"))["H2b"]
    FD = json.load(open("results/p2_figdata.json"))["h2b"]
    out = {"kh": {}, "choice_vs_ident": {}}
    for iso in ("langmuir", "step"):
        for sg in ("0.005", "0.02"):
            a, b = e8[f"{iso}|sigma={sg}|n_t=200"], e11[f"{iso}|sigma={sg}|both"]
            key = f"{iso}|sigma={sg}"
            out["kh"][key] = {f"{q}_{n}": kh(r[f"da_{q}"], nt) for q in ("disc", "select", "ident")
                              for n, r, nt in (("200", a, 200), ("2000", b, 1996))}
            g = lambda r: (math.log10(r["da_ident"] / r["da_select"]) if r["da_ident"] and r["da_select"] else None)
            out["choice_vs_ident"][key] = {"gap_200": g(a), "gap_2000": g(b),
                                           "ident_beyond_grid_2000": b["da_ident"] is None}
    peaks, fam = {}, set()
    for k, v in V.items():
        if v["gap_decades"] is None:
            continue
        lv = FD[k]["disc"]
        peaks[k] = max(a / n for _, a, n in lv)
        _, _, iso, pe = k.split("|")
        fam.add((iso, pe))
    out["peak_success"] = {"n_slices": len(peaks), "min": min(peaks.values()), "max": max(peaks.values()),
                           "n_below_0.7": sum(p < 0.7 for p in peaks.values()),
                           "n_below_0.5": sum(p < 0.5 for p in peaks.values()), "per_slice": peaks}
    out["independent_families"] = sorted("|".join(f) for f in fam)
    cv = [x for d in out["choice_vs_ident"].values() for x in (d["gap_200"], d["gap_2000"]) if x is not None]
    out["choice_vs_ident_range"] = [min(cv), max(cv)]
    write_atomic(out, "results/p2_referee_checks.json")
    print(json.dumps({k: v for k, v in out.items() if k != "peak_success"}, indent=1))
    print({k: v for k, v in out["peak_success"].items() if k != "per_slice"})


if __name__ == "__main__":
    main()
