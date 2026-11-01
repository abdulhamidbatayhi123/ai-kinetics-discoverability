"""Diagnostic (not a result, no rule changed): the O1 identifiability call exactly as
p2_grid_extra.py makes it (observe(...,'O1'), all 20 probes, sigma = 0), with the summed
log-likelihood printed on the coarse grid and per probe at k_true and at the reported k.

    python p2_diag_step_profile.py [cell]
"""
import sys

import numpy as np

from p2.identifiability import loglik_o1, profile_interval_o1
from p2_observe import load_cell, observe

name = sys.argv[1] if len(sys.argv) > 1 else "step_L1_pe1_da0.1"
_, man = load_cell(name)
k0 = man["k_LDF"]
obs = observe(name, 0, 0.0, 0.0, "O1")
ch = obs["channels"]
sq = max(0.0, 1e-4) * float(np.ptp(ch["q"]))
lo, hi = profile_interval_o1(obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
print(name, "k_true", k0, "interval/k", lo / k0, hi / k0)
kg = np.logspace(-6, 0, 25)
ll = loglik_o1(kg, obs["t"], list(ch["c"]), list(ch["q"]), obs["qstar_meas"], sq, Ts=list(ch["T"]))
for kk, l in zip(kg[:8], ll[:8]):
    print(f"  coarse k {kk:.3e} (k/k_true {kk / k0:.3f}): ll {l:.6g}")
for kk in (k0, lo):
    per = [float(loglik_o1(np.array([kk]), obs["t"], [c], [q], obs["qstar_meas"], sq, Ts=[T])[0])
           for c, q, T in zip(ch["c"], ch["q"], ch["T"])]
    print(f"  per-probe ll at k/k_true {kk / k0:.3f}:", [f"{x:.3g}" for x in per])
print("  probe z (m):", [f"{z:.3f}" for z in obs["z"]])
print("  q at t[0] per probe:", [f"{q[0]:.3g}" for q in ch["q"]])
