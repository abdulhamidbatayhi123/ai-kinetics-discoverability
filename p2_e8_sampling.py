"""E8 (post-verdict, declared in EXPLORATORY_P2.md before running): sampling rate.

O1 observations of the confirmatory grid's L1 cells at Pe ~94 (both isotherms, all nine Da),
sigma 0.5 and 2 %, eps 0, replicates 0..59, at two sampling rates:
  N_T = 200  the grid's own sampling; observe_nt(..., 200) is identical to p2_observe.observe
  N_T = 400  every stored time of the ground-truth field, the same noise SD per sample
Per row: discovery by the six sparse solvers in both forms (p2.run_o1.discover_o1, success_L1),
O1 identifiability (profile_interval_o1, the pre-registered criterion) and, for replicates 15..59,
E6's choice among three laws (p2_e6_modelselect.select). Every method runs unchanged (windows in
samples). Boundaries as in E7: best discovery method on replicates 0..14, logistic 50 % crossings
on 15..59 (p2.analysis). Writes results/p2_e8_sampling.json (rows) and results/p2_e8_summary.json.

    python p2_e8_sampling.py rows <out_json> <cell>|<sigma>|<n_t> [...]   # one worker's groups
    python p2_e8_sampling.py summary <rows_json> [...]                   # merge + boundaries
    python p2_e8_sampling.py --smoke                                     # two rows, no file
"""
import json
import sys

import numpy as np

SIGMAS = (0.005, 0.02)
NTS = (200, 400)
N_REP = 60
SUMMARY = "results/p2_e8_summary.json"
ROWS = "results/p2_e8_sampling.json"


def observe_nt(name, rep, sigma, n_t):
    """p2_observe.observe(name, rep, sigma, 0.0, 'O1') with n_t sample times (same probes, same
    noise stream and SD rule; at n_t = N_T it returns exactly what observe returns)."""
    from p2_observe import N_PROBE, _rng, load_cell, observe
    f, _ = load_cell(name)
    base = observe(name, rep, sigma, 0.0, "O1")          # qstar_meas, c_in, meta: eps = 0
    it = np.linspace(0, len(f["t"]) - 1, n_t).round().astype(int)
    iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
    r = _rng(name, rep, sigma, "O1", "noise")
    data = {}
    for ch in ("c", "q", "T"):
        true = f[ch][np.ix_(iz, it)].astype(float)
        rng_ch = float(f[ch].max() - f[ch].min())
        data[ch] = true + (r.normal(scale=sigma * rng_ch, size=true.shape) if sigma > 0 else 0.0)
    return {**base, "t": f["t"][it].astype(float), "channels": data}


def one_row(name, rep, sigma, n_t, k_true):
    from p2.identifiability import identifiable, profile_interval_o1
    from p2.metric import success_L1
    from p2.run_o1 import SOLVERS, discover_o1
    from p2_e6_modelselect import select
    from p2_grid_o1 import FORMS
    obs = observe_nt(name, rep, sigma, n_t)
    disc = {}
    for solver in SOLVERS:
        for form in FORMS:
            try:
                disc[f"{solver}|{form}"] = bool(success_L1(discover_o1(obs, solver, form)))
            except Exception as ex:          # a failure, never dropped (A2)
                disc[f"{solver}|{form}"] = False
                disc[f"{solver}|{form}|error"] = f"{type(ex).__name__}: {ex}"
    ch = obs["channels"]
    sq = max(sigma, 1e-4) * float(np.ptp(ch["q"]))
    try:
        lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
        ident = {"lo": lo, "hi": hi, "success": bool(identifiable(lo, hi, k_true))}
    except Exception as ex:
        ident = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
    row = {"disc": disc, "ident": ident}
    if rep >= 15:
        try:
            best, fits = select(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
            row["select"] = {"best": best, "success": best == "ldf",
                             "ll": {n: v["ll"] for n, v in fits.items()}, "k_ldf": fits["ldf"]["k_hat"]}
        except Exception as ex:
            row["select"] = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
    return row


def run_groups(out, groups):
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    res = {"rows": {}}
    for g in groups:
        name, s, n_t = g.split("|")
        for rep in range(N_REP):
            res["rows"][f"{name}|{s}|{n_t}|{rep}"] = one_row(name, rep, float(s), int(n_t), cells[name]["k_LDF"])
        json.dump(res, open(out, "w"))
        print("group done", g, flush=True)


def summarise(rows):
    from p2.analysis import boundary, disc_vs_ident, select_best
    from p2_analyze import MDE
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    out = {}
    for iso in ("langmuir", "step"):
        for s in SIGMAS:
            for n_t in NTS:
                sel, est, idf, chs = {}, {}, {}, {}
                for key, r in rows.items():
                    name, ss, nn, rep = key.split("|")
                    if cells[name]["iso"] != iso or float(ss) != s or int(nn) != n_t:
                        continue
                    da, rep = cells[name]["Da"], int(rep)
                    for m, ok in r["disc"].items():
                        if not m.endswith("|error"):
                            (sel if rep < 15 else est).setdefault(m, {}).setdefault(da, []).append(float(ok))
                    if rep >= 15:
                        idf.setdefault(da, []).append(float(r["ident"]["success"]))
                        chs.setdefault(da, []).append(float(r["select"]["success"]))
                best = select_best(sel)
                d = boundary(est[best], n_boot=0)[0] if best else None
                i = boundary(idf, n_boot=0)[0] if idf else None
                c = boundary(chs, n_boot=0)[0] if chs else None
                out[f"{iso}|sigma={s}|n_t={n_t}"] = {
                    "best_method": best, "da_disc": d, "da_ident": i, "da_select": c, **disc_vs_ident(d, i, MDE),
                    "disc_by_da": {str(k): float(np.mean(x)) for k, x in sorted(est.get(best, {}).items())} if best else {},
                    "ident_by_da": {str(k): float(np.mean(x)) for k, x in sorted(idf.items())},
                    "select_by_da": {str(k): float(np.mean(x)) for k, x in sorted(chs.items())}}
    return out


def expected_keys():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    names = sorted(n for n, c in cells.items() if c["law"] == "L1" and c["iso"] in ("langmuir", "step")
                   and c["pe_mult"] == 1.0 and not c.get("refined"))
    return names, {f"{n}|{s}|{t}|{r}" for n in names for s in SIGMAS for t in NTS for r in range(N_REP)}


def main():
    if "--smoke" in sys.argv:
        cells = json.load(open("data/p2/manifest.json"))["cells"]
        for n_t in NTS:
            r = one_row("step_L1_pe1_da31.6", 20, 0.005, n_t, cells["step_L1_pe1_da31.6"]["k_LDF"])
            print(n_t, {k: v for k, v in r["disc"].items() if v}, r["ident"].get("success"), r["select"]["best"])
        return
    if sys.argv[1] == "rows":
        return run_groups(sys.argv[2], sys.argv[3:])
    if sys.argv[1] == "summary":
        from p2.io_utils import write_atomic
        rows, seen = {}, 0
        for p in sys.argv[2:]:
            part = json.load(open(p))["rows"]
            seen += len(part)
            rows.update(part)
        _, want = expected_keys()
        if seen != len(rows) or set(rows) != want:
            sys.exit(f"FAIL keys: {seen} read, {len(rows)} unique, {len(want)} expected")
        write_atomic({"rows": rows}, ROWS)
        write_atomic(summarise(rows), SUMMARY)
        print("E8 summary written:", SUMMARY)


if __name__ == "__main__":
    main()
