"""E11 (post hoc, declared in EXPLORATORY_P2.md before running): the boundaries at about 2,000 samples per run.

As E8 (p2_e8_sampling.py) at about ten times the grid's sampling. O1, both isotherms, Pe ~94, L1, all nine Da,
sigma 0.5 and 2 %, eps 0, replicates 0..59. Each cell is re-solved with the unchanged solver and 3,991 stored
times (as E10; every 10th equals one of the grid's 400, checked against data/p2); observations use every second
stored time (1,996, which include the grid's 200), the same 20 probes, the same noise SD per sample and a noise
stream of its own. Per row:
  disc     the six sparse solvers in both forms, unchanged (windows in samples)
  disc_tm  the same twelve with windows matched in time to the grid's 200 samples (weak supports x 10 - 1,
           derivative window 209)
  ident    O1 identifiability (profile_interval_o1, the pre-registered criterion)
  select   for replicates 15..59, E6's choice among three laws
Summary: the best discovery method chosen on replicates 0..14 among the 24 candidates, logistic 50 % crossings on
replicates 15..59 (p2.analysis), and the same for (disc) and (disc_tm) separately.

    python p2_e11_fine.py rows <out_json> <cell>|<sigma> [...]    # one worker's groups (solves its cells)
    python p2_e11_fine.py summary <rows_json> [...]               # merge + boundaries
    python p2_e11_fine.py --smoke                                 # time one row, no file
Fields go to E11_DIR (default scratch_e11/, not tracked), never to data/p2.
"""
import json
import os
import sys
import time

import numpy as np

SIGMAS = (0.005, 0.02)
N_REP = 60
FINE = 3991
STEP = 2                                   # every second stored time: 1,996 observation times
SCRATCH = os.environ.get("E11_DIR", "scratch_e11")
ROWS = "results/p2_e11_fine.json"
SUMMARY = "results/p2_e11_summary.json"
TM_SUPPORTS = (309, 609, 1209)             # 31, 61, 121 samples at 200 times, matched in time at 1,996
TM_DERIV = 209                             # 21 samples at 200 times, matched in time


def fine_field(name):
    """The cell re-solved with FINE stored times (cached in SCRATCH) and its max deviation from data/p2."""
    import p2_generate
    from p2_observe import load_cell
    path = os.path.join(SCRATCH, name + "_fine.npz")
    stored, man = load_cell(name)
    if not os.path.exists(path):
        p2_generate.N_SNAP = FINE
        rec, z, t, c, q, T = p2_generate.solve_cell(man["iso"], man["law"], man["pe_mult"], man["Da"])
        assert rec["horizon_t_stoich"] == man["horizon_t_stoich"], (rec["horizon_t_stoich"], man["horizon_t_stoich"])
        os.makedirs(SCRATCH, exist_ok=True)
        np.savez(path + ".tmp.npz", z=z, t=t, c=c, q=q, T=T)
        os.replace(path + ".tmp.npz", path)
    f = dict(np.load(path))
    assert np.allclose(f["t"][::10], stored["t"], rtol=1e-5), "time grids differ"
    check = {ch: float(np.max(np.abs(f[ch][:, ::10].astype(np.float32) - stored[ch]))
                       / (float(stored[ch].max() - stored[ch].min()) or 1.0)) for ch in ("c", "q", "T")}
    return f, man, check


def observe_fine(name, f, rep, sigma):
    """O1 at every STEP-th fine time: p2_observe's probes, q*_meas and noise SD rule; its own noise stream."""
    from p2_observe import N_PROBE, _rng, observe
    base = observe(name, rep, sigma, 0.0, "O1")           # q*_meas (eps = 0), c_in, meta
    it = np.arange(0, FINE, STEP)
    iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
    r = _rng(name, rep, sigma, "O1", "noise", "E11")
    data = {}
    for ch in ("c", "q", "T"):
        true = f[ch][np.ix_(iz, it)].astype(float)
        rng_ch = float(f[ch].max() - f[ch].min())
        data[ch] = true + (r.normal(scale=sigma * rng_ch, size=true.shape) if sigma > 0 else 0.0)
    return {**base, "t": f["t"][it].astype(float), "channels": data}


def discover_all(obs, time_matched):
    import p2.features as feats
    import p2.run_o1 as ro
    from p2.metric import success_L1
    from p2_grid_o1 import FORMS
    saved = (ro.WEAK_SUPPORTS, feats.derivative.__defaults__)
    if time_matched:
        ro.WEAK_SUPPORTS = TM_SUPPORTS
        feats.derivative.__defaults__ = (TM_DERIV, saved[1][1])
    try:
        out = {}
        for solver in ro.SOLVERS:
            for form in FORMS:
                try:
                    out[f"{solver}|{form}"] = bool(success_L1(ro.discover_o1(obs, solver, form)))
                except Exception as ex:          # a failure, never dropped (A2)
                    out[f"{solver}|{form}"] = False
                    out[f"{solver}|{form}|error"] = f"{type(ex).__name__}: {ex}"
        return out
    finally:
        ro.WEAK_SUPPORTS = saved[0]
        feats.derivative.__defaults__ = saved[1]


def one_row(name, f, rep, sigma, k_true):
    from p2.identifiability import identifiable, profile_interval_o1
    from p2_e6_modelselect import select
    obs = observe_fine(name, f, rep, sigma)
    row = {"disc": discover_all(obs, False), "disc_tm": discover_all(obs, True)}
    ch = obs["channels"]
    sq = max(sigma, 1e-4) * float(np.ptp(ch["q"]))
    try:
        lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
        row["ident"] = {"lo": lo, "hi": hi, "success": bool(identifiable(lo, hi, k_true))}
    except Exception as ex:
        row["ident"] = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
    if rep >= 15:
        try:
            best, fits = select(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
            row["select"] = {"best": best, "success": best == "ldf",
                             "ll": {n: v["ll"] for n, v in fits.items()}, "k_ldf": fits["ldf"]["k_hat"]}
        except Exception as ex:
            row["select"] = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
    return row


def run_groups(out, groups):
    res = json.load(open(out)) if os.path.exists(out) else {"rows": {}, "checks": {}}
    for g in groups:
        name, s = g.split("|")
        f, man, check = fine_field(name)
        res["checks"][name] = check
        for rep in range(N_REP):
            key = f"{name}|{s}|{rep}"
            if key not in res["rows"]:
                res["rows"][key] = one_row(name, f, rep, float(s), man["k_LDF"])
                json.dump(res, open(out + ".tmp", "w"))
                os.replace(out + ".tmp", out)
        print("group done", g, time.strftime("%H:%M:%S"), flush=True)


def summarise(rows):
    from p2.analysis import boundary, disc_vs_ident, select_best
    from p2_analyze import MDE
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    out = {}
    for iso in ("langmuir", "step"):
        for s in SIGMAS:
            sel = {"both": {}, "disc": {}, "disc_tm": {}}
            est = {"both": {}, "disc": {}, "disc_tm": {}}
            idf, chs = {}, {}
            for key, r in rows.items():
                name, ss, rep = key.split("|")
                if cells[name]["iso"] != iso or float(ss) != s:
                    continue
                da, rep = cells[name]["Da"], int(rep)
                for var in ("disc", "disc_tm"):
                    for m, ok in r[var].items():
                        if m.endswith("|error"):
                            continue
                        for pool, mk in ((var, m), ("both", f"{var}:{m}")):
                            (sel if rep < 15 else est)[pool].setdefault(mk, {}).setdefault(da, []).append(float(ok))
                if rep >= 15:
                    idf.setdefault(da, []).append(float(r["ident"]["success"]))
                    chs.setdefault(da, []).append(float(r["select"]["success"]))
            i = boundary(idf, n_boot=0)[0] if idf else None
            c = boundary(chs, n_boot=0)[0] if chs else None
            for pool in ("both", "disc", "disc_tm"):
                best = select_best(sel[pool])
                d = boundary(est[pool][best], n_boot=0)[0] if best else None
                out[f"{iso}|sigma={s}|{pool}"] = {
                    "best_method": best, "da_disc": d, "da_ident": i, "da_select": c, **disc_vs_ident(d, i, MDE),
                    "disc_by_da": {str(k): float(np.mean(x)) for k, x in sorted(est[pool].get(best, {}).items())} if best else {},
                    "ident_by_da": {str(k): float(np.mean(x)) for k, x in sorted(idf.items())},
                    "select_by_da": {str(k): float(np.mean(x)) for k, x in sorted(chs.items())}}
    return out


def expected_keys():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    names = sorted(n for n, c in cells.items() if c["law"] == "L1" and c["iso"] in ("langmuir", "step")
                   and c["pe_mult"] == 1.0 and not c.get("refined"))
    return names, {f"{n}|{s}|{r}" for n in names for s in SIGMAS for r in range(N_REP)}


def main():
    if "--smoke" in sys.argv:
        name = sys.argv[sys.argv.index("--smoke") + 1] if len(sys.argv) > 2 else "step_L1_pe1_da31.6"
        t0 = time.time()
        f, man, check = fine_field(name)
        t1 = time.time()
        r = one_row(name, f, 20, 0.005, man["k_LDF"])
        t2 = time.time()
        print("check", check, f"solve {t1 - t0:.0f} s, row {t2 - t1:.0f} s")
        print({k: v for k, v in r["disc"].items() if v is True}, {k: v for k, v in r["disc_tm"].items() if v is True},
              r["ident"], r["select"].get("best"))
        return
    if sys.argv[1] == "rows":
        return run_groups(sys.argv[2], sys.argv[3:])
    if sys.argv[1] == "summary":
        from p2.io_utils import write_atomic
        rows, checks = {}, {}
        for p in sys.argv[2:]:
            part = json.load(open(p))
            rows.update(part["rows"])
            checks.update(part.get("checks", {}))
        _, want = expected_keys()
        if set(rows) != want:
            sys.exit(f"FAIL keys: {len(rows)} read, {len(want)} expected, missing {len(want - set(rows))}")
        write_atomic({"rows": rows, "checks": checks}, ROWS)
        write_atomic(summarise(rows), SUMMARY)
        print("E11 summary written:", SUMMARY)


if __name__ == "__main__":
    main()
