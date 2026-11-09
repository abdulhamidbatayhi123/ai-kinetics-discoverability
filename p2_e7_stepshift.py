"""E7 (post-verdict, declared in EXPLORATORY_P2.md before running): a systematic isotherm error for
the step isotherm. The measured isotherm is the true one shifted along relative humidity, so its
step sits s = -2, -1, +1, +2 % RH away from the true step:
    q*_meas(c, T) = q*(max(c - rh_to_conc(s, T), 0), T)
Everything else is the O1 observation of the confirmatory grid (p2_observe.observe with eps = 0:
same fields, probes, times and noise draws). For every step L1 cell at Pe ~94, sigma 0.5 and 2 %,
each shift and replicates 0..59: discovery by the six sparse solvers (p2.run_o1.discover_o1,
success_L1) and O1 identifiability (profile_interval_o1, the pre-registered criterion). Boundaries
use p2_analyze's own selection (replicates 0..14) and estimation (15..59) and p2.analysis.boundary.
Writes results/p2_e7_stepshift.json (rows, resumable) and results/p2_e7_summary.json.

    python p2_e7_stepshift.py            # all rows, then the summary
    python p2_e7_stepshift.py --smoke    # two rows, no file written
"""
import json
import os
import sys

import numpy as np

from fetch_real_mof_data import rh_to_conc
from isotherm import q_star_np
from p2.io_utils import write_atomic
from p2_observe import observe, physics_for, load_cell

OUT, SUMMARY = "results/p2_e7_stepshift.json", "results/p2_e7_summary.json"
SHIFTS = (-0.02, -0.01, 0.01, 0.02)
SIGMAS = (0.005, 0.02)


def shifted_obs(name, rep, sigma, shift):
    obs = observe(name, rep, sigma, 0.0, "O1")
    _, man = load_cell(name)
    p = physics_for(man)

    def qstar_meas(c, T):
        c, T = np.asarray(c, float), np.asarray(T, float)
        return q_star_np(np.maximum(c - rh_to_conc(shift, T), 0.0), T, p)
    obs["qstar_meas"] = qstar_meas
    return obs


def one_row(name, rep, sigma, shift, k_true):
    from p2.identifiability import identifiable, profile_interval_o1
    from p2.metric import success_L1
    from p2.run_o1 import SOLVERS, discover_o1
    from p2_grid_o1 import FORMS
    obs = shifted_obs(name, rep, sigma, shift)
    disc = {}
    for solver in SOLVERS:
        for form in FORMS:
            try:
                disc[f"{solver}|{form}"] = bool(success_L1(discover_o1(obs, solver, form)))
            except Exception as ex:          # recorded as a failure, never dropped (A2)
                disc[f"{solver}|{form}"] = False
                disc[f"{solver}|{form}|error"] = f"{type(ex).__name__}: {ex}"
    ch = obs["channels"]
    sq = max(sigma, 1e-4) * float(np.ptp(ch["q"]))
    try:
        lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
        ident = {"lo": lo, "hi": hi, "success": bool(identifiable(lo, hi, k_true))}
    except Exception as ex:
        ident = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
    return {"disc": disc, "ident": ident}


def summarise(cells, rows):
    from p2.analysis import boundary, disc_vs_ident, select_best
    from p2_analyze import MDE
    out = {}
    for s in SIGMAS:
        for sh in SHIFTS:
            sel, est, idf = {}, {}, {}
            for key, r in rows.items():
                name, ss, shs, rep = key.split("|")
                if float(ss) != s or float(shs) != sh:
                    continue
                da, rep = cells[name]["Da"], int(rep)
                for m, ok in r["disc"].items():
                    if m.endswith("|error"):
                        continue
                    (sel if rep < 15 else est).setdefault(m, {}).setdefault(da, []).append(float(ok))
                if rep >= 15:
                    idf.setdefault(da, []).append(float(r["ident"]["success"]))
            best = select_best(sel)
            d = boundary(est[best], n_boot=0)[0] if best else None
            i = boundary(idf, n_boot=0)[0] if idf else None
            v = disc_vs_ident(d, i, MDE)
            out[f"sigma={s}|shift={sh}"] = {
                "best_method": best, "da_disc": d, "da_ident": i, **v,
                "disc_by_da": {str(k): float(np.mean(x)) for k, x in sorted(est.get(best, {}).items())} if best else {},
                "ident_by_da": {str(k): float(np.mean(x)) for k, x in sorted(idf.items())}}
    return out


def main():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    names = sorted(n for n, c in cells.items() if c["iso"] == "step" and c["law"] == "L1"
                   and c["pe_mult"] == 1.0 and not c.get("refined"))
    if "--merge-parts" in sys.argv:     # B90 parallel parts: rows recomputed in --part files replace OUT's rows
        res = json.load(open(OUT))
        for p in sys.argv[sys.argv.index("--merge-parts") + 1:]:
            part = json.load(open(p))["rows"]
            if not all(r["ident"].get("b90") for r in part.values()) or not set(part) <= set(res["rows"]):
                sys.exit(f"FAIL: {p} has rows without the B90 flag or unknown keys")
            res["rows"].update(part)
        left = sum(not r["ident"].get("b90") for r in res["rows"].values())
        if left:
            sys.exit(f"FAIL: {left} rows still without the B90 identifiability")
        write_atomic(res, OUT)
        write_atomic(summarise(cells, res["rows"]), SUMMARY)
        print("E7 ident-only done (merged parts)", flush=True)
        return
    if "--ident-only" in sys.argv:      # B90: recompute only the identifiability part of every row
        from p2.identifiability import identifiable, profile_interval_o1
        res = json.load(open(OUT))
        part_i = part_n = None
        if "--part" in sys.argv:        # --part i n PATH: every n-th pending row from i, written to PATH only
            j = sys.argv.index("--part")
            part_i, part_n, part_out = int(sys.argv[j + 1]), int(sys.argv[j + 2]), sys.argv[j + 3]
            done = json.load(open(part_out))["rows"] if os.path.exists(part_out) else {}   # resumable
        for i, (key, r) in enumerate(sorted(res["rows"].items())):
            if r["ident"].get("b90") or (part_n and key in done):
                continue
            if part_n and i % part_n != part_i:
                continue
            n, s, sh, rep = key.split("|")
            obs = shifted_obs(n, int(rep), float(s), float(sh))
            ch = obs["channels"]
            sq = max(float(s), 1e-4) * float(np.ptp(ch["q"]))
            try:
                lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq,
                                             Ts=list(ch["T"]))
                r["ident"] = {"lo": lo, "hi": hi, "success": bool(identifiable(lo, hi, cells[n]["k_LDF"])), "b90": True}
            except Exception as ex:
                r["ident"] = {"success": False, "error": f"{type(ex).__name__}: {ex}", "b90": True}
            if part_n:
                done[key] = r
                if len(done) % 60 == 0:
                    write_atomic({"rows": done}, part_out)
                    print(f"part {part_i}: {len(done)} rows", flush=True)
                continue
            if i % 120 == 119:
                write_atomic(res, OUT)
                print(f"ident {i + 1}/{len(res['rows'])}", flush=True)
        if part_n:
            write_atomic({"rows": done}, part_out)
            print(f"part {part_i} done: {len(done)} rows", flush=True)
            return
        write_atomic(res, OUT)
        write_atomic(summarise(cells, res["rows"]), SUMMARY)
        print("E7 ident-only done", flush=True)
        return
    if "--smoke" in sys.argv:
        for n in names[:2]:
            print(n, one_row(n, 15, 0.02, 0.01, cells[n]["k_LDF"]))
        return
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}
    todo = [(n, s, sh, r) for n in names for s in SIGMAS for sh in SHIFTS for r in range(60)]
    for i, (n, s, sh, r) in enumerate(todo):
        key = f"{n}|{s}|{sh}|{r}"
        if key in res["rows"]:
            continue
        res["rows"][key] = one_row(n, r, s, sh, cells[n]["k_LDF"])
        if i % 60 == 59:
            write_atomic(res, OUT)
            print(f"{i + 1}/{len(todo)} {n}", flush=True)
    write_atomic(res, OUT)
    write_atomic(summarise(cells, res["rows"]), SUMMARY)
    print("E7 done:", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    main()
