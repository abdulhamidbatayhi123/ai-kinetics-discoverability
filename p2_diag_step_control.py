"""Diagnostic (not a result, no rule changed): why does the O1 profile put k at 3.1 x the truth
for step_L1_pe1_da0.1 at zero noise, which failed the step positive control?

Recomputes the O1 profile on the noise-free ground truth with the grid's sampling (N_T = 200
times, 20 probes) and with denser time sampling, and with the isotherm evaluated at the TRUE
c(t), T(t) on the solver's own time grid. If the bias falls with denser sampling, the cause is
the sampling resolution of q*(c(t), T(t)) across the step, not the column.

    python p2_diag_step_control.py [cell]
"""
import sys

import numpy as np

from isotherm import q_star_np
from p2.identifiability import profile_interval_o1
from p2_observe import N_PROBE, load_cell, physics_for

name = sys.argv[1] if len(sys.argv) > 1 else "step_L1_pe1_da0.1"
f, man = load_cell(name)
p = physics_for(man)
k = man["k_LDF"]
qfun = lambda c, T: q_star_np(np.asarray(c, float), np.asarray(T, float), p)
iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
print(name, "Da", man["Da"], "k_true", k, "solver time points", len(f["t"]))
for n_t in sorted({200, min(800, len(f["t"])), len(f["t"])}):
    it = np.unique(np.linspace(0, len(f["t"]) - 1, n_t).round().astype(int))
    t = f["t"][it].astype(float)
    cs = [f["c"][j][it].astype(float) for j in iz]
    qs = [f["q"][j][it].astype(float) for j in iz]
    Ts = [f["T"][j][it].astype(float) for j in iz]
    sq = 1e-4 * float(np.ptp(np.array(qs)))
    lo, hi = profile_interval_o1(t, cs, qs, qfun, sq, Ts=Ts)
    # how sharp is q*(t) between samples? largest one-sample jump relative to q* range
    jump = max(np.max(np.abs(np.diff(qfun(c, T)))) / max(np.ptp(qfun(c, T)), 1e-30)
               for c, T in zip(cs, Ts))
    print(f"  N_T={n_t:5d}: interval/k = [{lo / k:.4f}, {hi / k:.4f}]   "
          f"largest one-step jump of q* = {jump:.2f} of its range")
