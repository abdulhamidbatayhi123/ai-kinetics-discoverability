"""Diagnostic (not a result, no rule changed): do the stored ground-truth fields obey
dq/dt = k (q*(c, T) - q) with the isotherm the O1 profile uses? Prints, per probe, the k that
the finite-difference dq/dt implies, k_impl = (dq/dt) / (q* - q), where the driving force is
not tiny.

    python p2_diag_step_ldf.py [cell]
"""
import sys

import numpy as np

from isotherm import q_star_np
from p2_observe import N_PROBE, load_cell, physics_for

name = sys.argv[1] if len(sys.argv) > 1 else "step_L1_pe1_da0.1"
f, man = load_cell(name)
p = physics_for(man)
k = man["k_LDF"]
t = f["t"].astype(float)
iz = np.linspace(0, len(f["z"]) - 1, N_PROBE).round().astype(int)
print(name, "k_true", k, "q_max", man.get("q_max"))
for j in iz[::4]:
    c, q, T = (f[ch][j].astype(float) for ch in ("c", "q", "T"))
    qs = q_star_np(c, T, p)
    tm = 0.5 * (t[1:] + t[:-1])
    dq = np.diff(q) / np.diff(t)
    drive = 0.5 * ((qs - q)[1:] + (qs - q)[:-1])
    ok = np.abs(drive) > 0.05 * np.ptp(qs)
    ki = dq[ok] / drive[ok]
    print(f"  probe z={f['z'][j]:.3f}: q* range [{qs.min():.3g}, {qs.max():.3g}], q range "
          f"[{q.min():.3g}, {q.max():.3g}]; k_impl/k median {np.median(ki) / k:.3f} "
          f"(IQR {np.percentile(ki, 25) / k:.3f}-{np.percentile(ki, 75) / k:.3f}, n={ok.sum()})")
