"""E12 (EXPLORATORY_P2, declared d33da20 before this script existed): a second physical system.

A reversible reaction A + B <-> C in a continuously stirred tank, rate r = k (A B - C / K(T)), with the equilibrium
constant K(T) as the imperfectly known constitutive input (the role the isotherm plays in the column). The same
question as the main study: where does discovery of the rate law fail, compared with practical identifiability of k,
on the same observations? Everything below follows the declaration in EXPLORATORY_P2.md (E12).

    python p2_e12_reaction.py --smoke      two rows, printed
    python p2_e12_reaction.py rows         all 2,160 rows -> results/p2_e12_rows.json (resumable, per cell)
    python p2_e12_reaction.py summary      -> results/p2_e12_summary.json
    add --variant-b for E12b (B_in = 2; results/p2_e12b_*.json)
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np
from scipy.integrate import solve_ivp

from p2 import methods
from p2.features import derivative
from p2.io_utils import write_atomic
from p2.weak import weak_system

TAU, A_IN, B_IN = 1.0, 1.0, 1.0
T0, T1, K0, DH, R = 300.0, 340.0, 5.0, -50e3, 8.314462618
HORIZON, N_T = 8.0 * TAU, 200
DAS = [10 ** (i / 2) for i in range(-2, 7)]          # 0.1 ... 1000, as the main study
SIGMAS, EPSS, N_REP, N_SEL = (0.005, 0.02), (0.0, 0.02), 60, 15
N_MODES = 4
KGRID_REL = np.logspace(-2, 2, 161)                  # k/100 ... 100 k
SOLVERS = {"best_subset": methods.best_subset, "stlsq": methods.stlsq, "ensemble": methods.ensemble}
ROWS, SUMMARY = "results/p2_e12_rows.json", "results/p2_e12_summary.json"
if "--variant-b" in sys.argv:            # E12b (declared fb2c438): unequal feeds so that A and B differ
    B_IN = 2.0
    ROWS, SUMMARY = "results/p2_e12b_rows.json", "results/p2_e12b_summary.json"
T_OBS = np.linspace(0.0, HORIZON, N_T)


def _rng(*keys):
    h = hashlib.sha256("|".join(map(str, keys)).encode()).hexdigest()
    return np.random.default_rng(int(h[:16], 16))


def temperature(t):
    return T0 + (T1 - T0) * np.asarray(t, float) / HORIZON


def K_true(T):
    return K0 * np.exp(-(DH / R) * (1.0 / np.asarray(T, float) - 1.0 / T0))


def K_error(da, rep, eps):
    """g on the normalised temperature, smooth, unit RMS, per (Da, replicate) -- the main study's form."""
    r = _rng("E12", da, rep, "K")
    a, ph = r.normal(size=N_MODES), r.uniform(0, 2 * np.pi, N_MODES)
    xs = np.linspace(0, 1, 2001)
    raw = sum(a[j] * np.sin((j + 1) * np.pi * xs + ph[j]) for j in range(N_MODES))
    scale = np.sqrt(np.mean(raw ** 2))

    def K_meas(T):
        x = np.clip((np.asarray(T, float) - T0) / (T1 - T0), 0.0, 1.0)
        g = sum(a[j] * np.sin((j + 1) * np.pi * x + ph[j]) for j in range(N_MODES)) / scale
        return K_true(T) * (1.0 + eps * g)
    return K_meas


def solve(k, K_fn):
    def rhs(t, y):
        A, B, C = y
        r = k * (A * B - C / K_fn(temperature(t)))
        return [(A_IN - A) / TAU - r, (B_IN - B) / TAU - r, -C / TAU + r]
    sol = solve_ivp(rhs, (0.0, HORIZON), [0.0, 0.0, 0.0], t_eval=T_OBS, method="BDF", rtol=1e-9, atol=1e-12)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y                                          # (3, N_T)


def solve_many(ks, K_fn):
    """The same model for every k in ks at once (one stiff system, block-diagonal Jacobian): identical
    trajectories to solve() per k within solver tolerance (checked to 2e-9 at three grid points), far less Python overhead. Returns (len(ks), 3, N_T)."""
    from scipy.sparse import block_diag, csr_matrix
    ks = np.asarray(ks, float)
    m = len(ks)

    def rhs(t, y):
        A, B, C = y[0::3], y[1::3], y[2::3]
        r = ks * (A * B - C / K_fn(temperature(t)))
        out = np.empty_like(y)
        out[0::3], out[1::3], out[2::3] = (A_IN - A) / TAU - r, (B_IN - B) / TAU - r, -C / TAU + r
        return out
    sparsity = block_diag([csr_matrix(np.ones((3, 3)))] * m, format="csr")
    sol = solve_ivp(rhs, (0.0, HORIZON), np.zeros(3 * m), t_eval=T_OBS, method="BDF", rtol=1e-9, atol=1e-12,
                    jac_sparsity=sparsity)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.reshape(m, 3, N_T)


def observe(truth, da, sigma, rep):
    r = _rng("E12", da, sigma, rep, "noise")
    rng_ch = truth.max(axis=1) - truth.min(axis=1)
    return truth + r.normal(size=truth.shape) * (sigma * rng_ch)[:, None], sigma * rng_ch


def library(A, B, C, K_meas):
    T = temperature(T_OBS)
    return {"1": np.ones_like(A), "A": A, "B": B, "C": C, "A*B": A * B, "A^2": A ** 2, "T": T,
            "C/Kmeas": C / K_meas(T)}


def success(co):
    sel = {k for k, v in co.items() if v != 0.0}
    if sel != {"A*B", "C/Kmeas"} or co["A*B"] <= 0:
        return False
    return abs(co["C/Kmeas"] / co["A*B"] + 1.0) <= 0.10


def discover(obs, K_meas):
    A, B, C = obs
    F = library(A, B, C, K_meas)
    out = {}
    y_strong = derivative(C, T_OBS) + C / TAU
    Fw = dict(F)
    Fw["__flow"] = C / TAU
    G, b = weak_system(Fw, C, T_OBS, support=61)
    bw = b + G.pop("__flow")                          # -int phi' C + int phi C/tau = int phi r
    for name, fn in SOLVERS.items():
        for form, (FF, yy) in (("strong", (F, y_strong)), ("weak", (G, bw))):
            try:
                co = fn(FF, yy)
                out[f"{name}|{form}"] = bool(success(co))
            except Exception:                              # an error counts as a failure
                out[f"{name}|{form}"] = False
    return out


def identifiable(obs, sd, k_true, preds):
    """preds: solve_many(k_true * KGRID_REL, K_meas), shared by every observation made with the same K_meas."""
    ks = k_true * KGRID_REL
    ll = -0.5 * np.sum(((obs[None] - preds) / sd[None, :, None]) ** 2, axis=(1, 2))
    j = int(np.argmax(ll))
    inside = ks[2 * (ll.max() - ll) <= 3.84]
    ok = (0 < j < len(ks) - 1) and inside.min() >= k_true / 2 and inside.max() <= 2 * k_true
    return bool(ok), float(ks[j]), float(inside.min()), float(inside.max())


def one_cell_both_sigmas(da, eps):
    """Both noise levels of one (Da, eps): the likelihood predictions depend on K_meas only, so they are
    computed once per replicate (once per cell when eps = 0, where K_meas is the true K for every replicate)."""
    k = da / TAU
    truth = solve(k, K_true)
    rows = {}
    shared = solve_many(k * KGRID_REL, K_true) if eps == 0.0 else None
    for rep in range(N_REP):
        K_meas = K_error(da, rep, eps)
        preds = shared if shared is not None else solve_many(k * KGRID_REL, K_meas)
        for sigma in SIGMAS:
            obs, sd = observe(truth, da, sigma, rep)
            disc = discover(obs, K_meas)
            ok, khat, lo, hi = identifiable(obs, sd, k, preds)
            rows[f"{da:g}|{sigma}|{eps}|{rep}"] = {"disc": disc, "ident": ok, "k_hat": khat, "ci": [lo, hi]}
    return rows


def run_rows():
    res = json.load(open(ROWS)) if os.path.exists(ROWS) else {"rows": {}}
    res.setdefault("commit_at_start", subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                     text=True).stdout.strip())
    for da in DAS:
        for eps in EPSS:
            if all(f"{da:g}|{s}|{eps}|{N_REP - 1}" in res["rows"] for s in SIGMAS):
                continue
            t0 = time.process_time()
            res["rows"].update(one_cell_both_sigmas(da, eps))
            write_atomic(res, ROWS)
            print(f"Da {da:g} eps {eps}: {time.process_time() - t0:.0f} CPU s", flush=True)
    print("E12_ROWS_DONE", flush=True)


def summarise():
    from p2.analysis import boundary, disc_vs_ident, select_best
    from p2_analyze import MDE
    rows = json.load(open(ROWS))["rows"]
    assert len(rows) == len(DAS) * len(SIGMAS) * len(EPSS) * N_REP, len(rows)
    out = {}
    for sigma in SIGMAS:
        for eps in EPSS:
            sel, est, idf = {}, {}, {}
            for key, r in rows.items():
                d, s, e, rep = key.split("|")
                if float(s) != sigma or float(e) != eps:
                    continue
                da, rep = float(d), int(rep)
                for m, ok in r["disc"].items():
                    (sel if rep < N_SEL else est).setdefault(m, {}).setdefault(da, []).append(float(ok))
                if rep >= N_SEL:
                    idf.setdefault(da, []).append(float(r["ident"]))
            best = select_best(sel)
            dd = boundary(est[best], n_boot=2000) if best else (None, None, None)
            ii = boundary(idf, n_boot=2000)
            gap = (np.log10(ii[0] / dd[0]) if dd[0] and ii[0] else None)
            out[f"sigma={sigma}|eps={eps}"] = {
                "best_method": best, "da_disc": dd[0], "da_disc_ci": [dd[1], dd[2]], "da_ident": ii[0],
                "da_ident_ci": [ii[1], ii[2]], "gap_decades": gap, **disc_vs_ident(dd[0], ii[0], MDE),
                "disc_by_da": {str(k): float(np.mean(v)) for k, v in sorted(est[best].items())} if best else {},
                "ident_by_da": {str(k): float(np.mean(v)) for k, v in sorted(idf.items())}}
    pc_d = out["sigma=0.005|eps=0.0"]["disc_by_da"].get(str(0.1))
    pc_i = out["sigma=0.005|eps=0.0"]["ident_by_da"].get(str(0.1))
    out["positive_control"] = {"discovery": pc_d, "identifiable": pc_i,
                               "passed": bool(pc_d is not None and pc_i is not None and pc_d >= 0.9 and pc_i >= 0.9)}
    write_atomic(out, SUMMARY)
    print(json.dumps(out, indent=1))


def main():
    if "--smoke" in sys.argv:
        for da in (0.1, 1000.0):
            k = da / TAU
            truth = solve(k, K_true)
            K_meas = K_error(da, 0, 0.0)
            obs, sd = observe(truth, da, 0.005, 0)
            t0 = time.time()
            preds = solve_many(k * KGRID_REL, K_meas)
            # equivalence check of the batched solve against one-k solves at three grid points
            for i in (0, 80, 160):
                one = solve(k * KGRID_REL[i], K_meas)
                print("  max rel diff at grid", i, float(np.max(np.abs(one - preds[i])) / np.max(np.abs(one))))
            print(da, discover(obs, K_meas), identifiable(obs, sd, k, preds), f"{time.time() - t0:.1f} s")
        return
    if "rows" in sys.argv:
        return run_rows()
    if "summary" in sys.argv:
        return summarise()


if __name__ == "__main__":
    main()
