"""PREREG_P2 amendment A5: the per-solve wall cap of the O2/O3 profile likelihood.

A solve that runs past the cap is a failed solve (log-likelihood -inf, exactly as a solver
RuntimeError already is), and the profile records which k values were capped. Without a cap,
the result is unchanged."""
import time

import numpy as np


def _column(k_true=2e-4):
    from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data
    p = AdsorptionPhysicsConfig()
    p.k_LDF = k_true
    ts = p.stoichiometric_time(1.0, p.T_in)
    _, t, y = generate_breakthrough_data(p, N_z=40, t_final=4 * ts, n_snapshots=60, verbose=False)
    return p, t, y[39], y[119]


def test_capped_solve_scores_minus_inf_and_is_recorded():
    from isotherm import q_star_np
    from p2.identifiability import _loglik_outlet
    p, t, c_obs, T_obs = _column()

    def slow_qstar(c, T):            # every RHS call sleeps: the solve cannot finish in 0.5 s
        time.sleep(0.02)
        return q_star_np(c, T, p)
    p.qstar_fn = slow_qstar
    stats = {"capped": []}
    t0 = time.time()
    ll = _loglik_outlet(3e-4, p, 1.0, t, c_obs, T_obs, 0.005, 0.005, 40, cap_s=0.5, stats=stats)
    assert ll == -np.inf
    assert stats["capped"] == [3e-4]
    assert time.time() - t0 < 5.0
    assert p.qstar_fn is slow_qstar      # the caller's physics is not modified


def test_cap_leaves_an_uncapped_solve_unchanged():
    from p2.identifiability import _loglik_outlet
    p, t, c_obs, T_obs = _column()
    stats = {"capped": []}
    a = _loglik_outlet(3e-4, p, 1.0, t, c_obs, T_obs, 0.005, 0.005, 40)
    b = _loglik_outlet(3e-4, p, 1.0, t, c_obs, T_obs, 0.005, 0.005, 40, cap_s=600, stats=stats)
    assert a == b and stats["capped"] == []


def test_profile_passes_the_cap_through():
    from p2.identifiability import profile_interval_outlet
    p, t, c_obs, T_obs = _column()
    stats = {"capped": []}
    lo, hi = profile_interval_outlet(p, 1.0, t, c_obs, T_obs, sigma_c=0.005, sigma_T=0.005,
                                     n_z=40, cap_s=600, stats=stats)
    assert lo < 2e-4 < hi and stats["capped"] == []
