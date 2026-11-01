"""Diagnostic (not a result, no rule changed): regenerate one cell exactly as p2_generate.py does,
but with 10 x more stored snapshots, and recompute the noise-free O1 profile at 400 and 4000
time points. Separates sampling resolution from a mismatch between the profile's model and the
column.

    python p2_diag_step_dense.py [cell]
"""
import json
import sys

import numpy as np

import p2_generate as g
from isotherm import q_star_np
from p2.identifiability import profile_interval_o1
from p2_observe import N_PROBE
from solver_fd import generate_breakthrough_data

name = sys.argv[1] if len(sys.argv) > 1 else "step_L1_pe1_da0.1"
rec = json.load(open("data/p2/manifest.json"))["cells"][name]
p, c_in = g.make_physics(rec["iso"])
t_st = float(p.stoichiometric_time(c_in, p.T_in))
p.k_LDF = rec["Da"] / t_st
p.D_L = p.D_L * rec["pe_mult"]
assert abs(p.k_LDF / rec["k_LDF"] - 1) < 1e-9, "physics differs from the manifest"
print(name, "horizon", rec["horizon_t_stoich"], "exit_final", rec["exit_final"], "N_SNAP", g.N_SNAP)
z, t, y = generate_breakthrough_data(p, N_z=g.N_Z, t_final=rec["horizon_t_stoich"] * t_st, c_in=c_in,
                                     n_snapshots=10 * g.N_SNAP, verbose=False)
c, q, T = y[:g.N_Z], y[g.N_Z:2 * g.N_Z], y[2 * g.N_Z:]
iz = np.linspace(0, g.N_Z - 1, N_PROBE).round().astype(int)
qfun = lambda cc, TT: q_star_np(np.asarray(cc, float), np.asarray(TT, float), p)
for n_t in (g.N_SNAP, 10 * g.N_SNAP):
    it = np.unique(np.linspace(0, len(t) - 1, n_t).round().astype(int))
    qs = [q[j][it] for j in iz]
    lo, hi = profile_interval_o1(t[it], [c[j][it] for j in iz], qs, qfun,
                                 1e-4 * float(np.ptp(np.array(qs))), Ts=[T[j][it] for j in iz])
    print(f"  N_T={len(it):5d}: interval/k = [{lo / p.k_LDF:.4f}, {hi / p.k_LDF:.4f}]", flush=True)
