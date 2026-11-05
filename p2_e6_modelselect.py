"""E6 (post-verdict, declared in EXPLORATORY_P2.md before running): choosing among a few candidate
rate laws, the comparator the Discussion recommends when open discovery fails.

On O1, each candidate law is fitted to all probes by the output-error likelihood the O1
identifiability profile uses (Gaussian on q, the same noise SD rule, the same PCHIP-upsampled
q*(t) path from the observed c and T), with k profiled on 10^-7..10 at 10 points per decade.
Candidates (one parameter each, so BIC picks the largest likelihood):
  ldf  dq/dt = k (q* - q)                 linear driving force (the truth under L1)
  qdf  dq/dt = k (q*^2 - q^2) / (2 q)     quadratic driving force
  pso  dq/dt = k (q* - q)^2               pseudo-second order
Each is integrated by implicit Euler on the upsampled grid (stable at any k; the quadratic steps
have closed-form roots), so all candidates share the same discretisation.

Subgrid: Pe ~94 (pe_mult 1.0); sigma 0.5 and 2 %; eps 0 and 2 %; all nine Da; both isotherms;
estimation replicates 15..59. Writes results/p2_e6_modelselect.json (resumable row by row).

    python p2_e6_modelselect.py
"""
import json
import os
import sys

import numpy as np

from p2.identifiability import UPSAMPLE, _qstar_path
from p2.io_utils import write_atomic

K_GRID = np.logspace(-7, 1, 81)
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
    """q on tf for every k (array): implicit Euler, shape (len(k), len(tf))."""
    k = np.atleast_1d(np.asarray(k, float))[:, None]
    h = np.diff(tf)
    q = np.full((k.shape[0], 1), float(q0))
    out = [q[:, 0].copy()]
    for i in range(len(h)):
        q = step(q, qsf[i + 1], k * h[i])
        out.append(q[:, 0].copy())
    return np.array(out).T


def loglik(step, t, cs, qs_obs, qstar_fn, sigma, Ts):
    ll = np.zeros(K_GRID.size)
    for c, q, T in zip(cs, qs_obs, Ts):
        tf, qsf = _qstar_path(t, np.asarray(c, float), qstar_fn, None if T is None else np.asarray(T, float))
        pred = integrate(step, K_GRID, tf, qsf, float(q[0]))[:, ::UPSAMPLE]
        ll += -0.5 * np.sum((pred - np.asarray(q, float)[None, :]) ** 2, axis=1) / sigma ** 2
    return ll


def select(t, cs, qs_obs, qstar_fn, sigma, Ts=None):
    Ts = [None] * len(cs) if Ts is None else Ts
    fits = {}
    for name, step in LAWS.items():
        ll = loglik(step, t, cs, qs_obs, qstar_fn, sigma, Ts)
        i = int(np.argmax(ll))
        fits[name] = {"ll": float(ll[i]), "k_hat": float(K_GRID[i]), "edge": i in (0, len(K_GRID) - 1)}
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
