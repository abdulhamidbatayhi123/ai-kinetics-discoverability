"""Diagnostic (not a result, no rule changed): evaluate the O1 log-likelihood of one probe of
step_L1_pe1_da0.1 (noise-free) at several k by the exact LDF update (loglik_o1, what the grid
used) and by the ODE solver (_loglik, the reference it was tested against).

    python p2_diag_step_ll.py [cell]
"""
import sys

import numpy as np

from isotherm import q_star_np
from p2.identifiability import _loglik, _qstar_path, _ldf_exact, loglik_o1, UPSAMPLE
from p2_observe import N_PROBE, N_T, load_cell, physics_for

name = sys.argv[1] if len(sys.argv) > 1 else "step_L1_pe1_da0.1"
f, man = load_cell(name)
p = physics_for(man)
k0 = man["k_LDF"]
it = np.linspace(0, len(f["t"]) - 1, N_T).round().astype(int)
iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
j = iz[5]
t = f["t"][it].astype(float)
c, q, T = (f[ch][j][it].astype(float) for ch in ("c", "q", "T"))
qfun = lambda cc, TT: q_star_np(np.asarray(cc, float), np.asarray(TT, float), p)
sig = 1e-4 * float(np.ptp(q))
ks = k0 * np.array([0.5, 0.9, 1.0, 1.1, 2.0, 3.105, 5.0])
ll_exact = loglik_o1(ks, t, [c], [q], qfun, sig, Ts=[T])
print(name, "k_true", k0, "UPSAMPLE", UPSAMPLE)
for kk, le in zip(ks, ll_exact):
    lo = _loglik(kk, t, c, q, qfun, sig, T=T)
    print(f"  k/k_true {kk / k0:6.3f}: exact-update ll {le:.6g}   ODE ll {lo:.6g}")
tf, qs = _qstar_path(t, c, qfun, T)
qm = _ldf_exact(np.array([k0]), tf, qs, q[0])[0, ::UPSAMPLE]
print("  max |q_model(k_true) - q_obs| / q range:", float(np.max(np.abs(qm - q)) / np.ptp(q)))
i = int(np.argmax(np.abs(qm - q)))
print("  at sample", i, "t", t[i], "q_obs", q[i], "q_model", qm[i], "c/c_in", c[i] / man["c_in"])
