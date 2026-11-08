"""RETRACTIONS_P2 B90: _ldf_exact must be the exact solution of dq/dt = k (q*(t) - q) for q*
piecewise linear, at EVERY k h (the original check covered small k h only, where the wrong
coefficient agreed to second order). Reference: scipy solve_ivp at tight tolerance."""
import numpy as np
import pytest
from scipy.integrate import solve_ivp


@pytest.mark.parametrize("kh", [1e-4, 1e-2, 0.1, 1.0, 3.0, 10.0, 100.0])
def test_one_interval_matches_ode(kh):
    from p2.identifiability import _ldf_exact
    qs0, qs1, q0, h = 0.3, 2.4, 0.1, 1.0
    k = kh / h
    code = _ldf_exact(np.array([k]), np.array([0.0, h]), np.array([qs0, qs1]), q0)[0, -1]
    ref = solve_ivp(lambda t, q: k * (qs0 + (qs1 - qs0) * t / h - q), (0, h), [q0],
                    method="Radau", rtol=1e-12, atol=1e-14).y[0, -1]
    assert abs(code - ref) < 1e-8 * max(1.0, abs(ref)), (kh, code, ref)


def test_many_intervals_match_ode():
    from p2.identifiability import _ldf_exact
    tf = np.linspace(0.0, 50.0, 201)
    qs = 2.0 / (1.0 + np.exp(-(tf - 20.0) / 3.0))
    for k in (0.01, 0.5, 5.0):
        code = _ldf_exact(np.array([k]), tf, qs, 0.0)[0]
        f = lambda t, q: k * (np.interp(t, tf, qs) - q)
        ref = solve_ivp(f, (tf[0], tf[-1]), [0.0], t_eval=tf, method="Radau", rtol=1e-10, atol=1e-12,
                        max_step=tf[1] - tf[0]).y[0]
        assert np.max(np.abs(code - ref)) < 1e-6, (k, np.max(np.abs(code - ref)))
