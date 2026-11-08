"""E6 (post-verdict, declared in EXPLORATORY_P2.md before running): choosing among a few candidate
rate laws, the comparator the Discussion recommends when open discovery fails.

On O1, each candidate law is fitted to all probes by the output-error likelihood the O1
identifiability profile uses (Gaussian on q, the same noise SD rule, the same PCHIP-upsampled
q*(t) path from the observed c and T), with k profiled on 10^-7..10 at 10 points per decade.
Candidates (one parameter each, so BIC picks the largest likelihood):
  ldf  dq/dt = k (q* - q)                 linear driving force (the truth under L1)
  qdf  dq/dt = k (q*^2 - q^2) / (2 q)     quadratic driving force
  pso  dq/dt = k (q* - q)^2               pseudo-second order
Each is integrated by implicit Euler on the upsampled grid with NSUB substeps per interval along
the linearly interpolated q*(t) (stable at any k; the quadratic steps have closed-form roots), so all
candidates share the same discretisation; with NSUB = 4 the LDF result differs from the exact update
by at most 0.03 log-likelihood units per probe at the true k (Da 31.6 to 1000).
B91: the first version took each law's best k from the coarse grid only (10 points per decade). At
0.5 % noise a k 10 % from the optimum costs ~1e5 log-likelihood units, so the choice of law followed
which law had a grid point nearest its optimum. Each law's k is now refined by bounded Brent search
on log10 k between the grid neighbours of the coarse maximum (xatol 1e-6 decade).

Subgrid: Pe ~94 (pe_mult 1.0); sigma 0.5 and 2 %; eps 0 and 2 %; all nine Da; both isotherms;
estimation replicates 15..59. Writes results/p2_e6_modelselect.json (resumable row by row).

    python p2_e6_modelselect.py
"""
import json
import os
import sys

import numpy as np

from p2.identifiability import UPSAMPLE, _qstar_path
from scipy.optimize import minimize_scalar

from p2.io_utils import write_atomic

K_GRID = np.logspace(-7, 1, 81)
NSUB = 4
OUT = "results/p2_e6_modelselect.json"


def _step_ldf(q, qs, a):          # q1 = q + a (qs - q1), a = k h
    return (q + a * qs) / (1.0 + a)


def _step_qdf(q, qs, a):          # q1 = q + (a/2)(qs^2 / q1 - q1)  ->  (1 + a/2) q1^2 - q q1 - (a/2) qs^2 = 0
    b = 1.0 + 0.5 * a
    return (q + np.sqrt(q * q + 4.0 * b * 0.5 * a * qs * qs)) / (2.0 * b)


def _step_pso(q, qs, a):          # q1 = q + a (qs - q1)^2; with u = qs - q1: a u^2 + u - (qs - q) = 0
    d = qs - q
    u = np.where(a > 0, (-1.0 + np.sqrt(1.0 + 4.0 * a * np.abs(d))) / (2.0 * np.maximum(a, 1e-300)), d)
    return qs - np.sign(d) * u


LAWS = {"ldf": _step_ldf, "qdf": _step_qdf, "pso": _step_pso}


def integrate(step, k, tf, qsf, q0):
    """q on tf for every k (array) and every probe at once: implicit Euler with NSUB substeps per
    interval along linearly interpolated q*. qsf (n_probe, n_tf), q0 (n_probe,); returns
    (len(k), n_probe, n_tf)."""
    k = np.atleast_1d(np.asarray(k, float))[:, None]
    qsf = np.atleast_2d(np.asarray(qsf, float))
    q = np.broadcast_to(np.asarray(q0, float)[None, :], (k.shape[0], qsf.shape[0])).copy()
    out = [q.copy()]
    for i in range(qsf.shape[1] - 1):
        h = (tf[i + 1] - tf[i]) / NSUB
        for j in range(1, NSUB + 1):
            q = step(q, qsf[None, :, i] + (qsf[None, :, i + 1] - qsf[None, :, i]) * (j / NSUB), k * h)
        out.append(q.copy())
    return np.stack(out, axis=2)


def _paths(t, cs, qstar_fn, Ts):
    tf = None
    qsf = []
    for c, T in zip(cs, Ts):
        tf, qs = _qstar_path(t, np.asarray(c, float), qstar_fn, None if T is None else np.asarray(T, float))
        qsf.append(qs)
    return tf, np.array(qsf)


def loglik(step, ks, tf, qsf, q_obs, sigma):
    pred = integrate(step, ks, tf, qsf, q_obs[:, 0])[:, :, ::UPSAMPLE]
    return -0.5 * np.sum((pred - q_obs[None]) ** 2, axis=(1, 2)) / sigma ** 2


def select(t, cs, qs_obs, qstar_fn, sigma, Ts=None):
    Ts = [None] * len(cs) if Ts is None else Ts
    tf, qsf = _paths(t, cs, qstar_fn, Ts)
    q_obs = np.array([np.asarray(q, float) for q in qs_obs])
    fits = {}
    for name, step in LAWS.items():
        ll = loglik(step, K_GRID, tf, qsf, q_obs, sigma)
        i = int(np.argmax(ll))
        lo, hi = np.log10(K_GRID[max(i - 1, 0)]), np.log10(K_GRID[min(i + 1, len(K_GRID) - 1)])
        r = minimize_scalar(lambda x: -loglik(step, [10.0 ** x], tf, qsf, q_obs, sigma)[0],
                            bounds=(lo, hi), method="bounded", options={"xatol": 1e-6})
        llr, kr = (-float(r.fun), 10.0 ** float(r.x)) if -r.fun >= ll[i] else (float(ll[i]), float(K_GRID[i]))
        fits[name] = {"ll": llr, "k_hat": kr, "ll_grid": float(ll[i]), "k_grid": float(K_GRID[i]),
                      "edge": i in (0, len(K_GRID) - 1)}
    best = max(fits, key=lambda n: fits[n]["ll"])
    return best, fits


def main():
    from p2_observe import observe
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}
    todo = [(n, s, e, r) for n, c in sorted(cells.items())
            if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined")
            for s in (0.005, 0.02) for e in (0.0, 0.02) for r in range(15, 60)]
    for i, (name, s, e, r) in enumerate(todo):
        key = f"{name}|{s}|{e}|{r}"
        if key in res["rows"]:
            continue
        try:
            obs = observe(name, r, s, e, "O1")
            ch = obs["channels"]
            sq = max(s, 1e-4) * float(np.ptp(ch["q"]))
            best, fits = select(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
            k0 = cells[name]["k_LDF"]
            res["rows"][key] = {"best": best, "fits": fits, "success": best == "ldf",
                                "success_k": best == "ldf" and 0.5 * k0 <= fits["ldf"]["k_hat"] <= 2 * k0}
        except Exception as ex:          # recorded, never dropped
            res["rows"][key] = {"success": False, "success_k": False, "error": f"{type(ex).__name__}: {ex}"}
        if i % 45 == 44:
            write_atomic(res, OUT)
            print(f"{i + 1}/{len(todo)} {name}", flush=True)
    write_atomic(res, OUT)
    print("E6 done:", len(res["rows"]), "rows", flush=True)


if __name__ == "__main__":
    sys.exit(main())
