"""PREREG_P2 amendment A6 (B87): the O1 profile must search a k range that contains every k of
the design, and must fail loudly, never silently, when the likelihood peaks on the edge of its
search range. The frozen range 1e-5..10 excluded the step cells at Da = 0.1 (k = 3.2e-6)."""
import numpy as np
import pytest


def _probes(k, n_probe=4, n_t=200):
    """Noise-free O1 probes obeying dq/dt = k (q* - q) exactly, q* = 10 c, c a ramp per probe."""
    from p2.identifiability import UPSAMPLE, _ldf_exact, _qstar_path
    qstar = lambda c, T: 10.0 * np.asarray(c, float)
    t = np.linspace(0.0, 8.0 / k, n_t)
    cs, qs, Ts = [], [], []
    for j in range(n_probe):
        c = np.clip((t - j * 0.5 / k) * k, 0.0, 1.0)
        T = np.full_like(t, 300.0)
        tf, qsf = _qstar_path(t, c, qstar, T)
        cs.append(c)
        Ts.append(T)
        qs.append(_ldf_exact(np.array([k]), tf, qsf, 0.0)[0, ::UPSAMPLE])
    return t, cs, qs, Ts, qstar


@pytest.mark.parametrize("k", [3.220569086049949e-06, 1.3888e-05, 0.13888])
def test_o1_profile_brackets_every_design_k(k):
    from p2.identifiability import profile_interval_o1
    t, cs, qs, Ts, qstar = _probes(k)
    lo, hi = profile_interval_o1(t, cs, qs, qstar, 1e-3, Ts=Ts)
    assert lo <= k <= hi, (lo / k, hi / k)


def test_o1_profile_refuses_a_peak_on_the_grid_edge():
    from p2.identifiability import profile_interval_o1
    k = 1e-6
    t, cs, qs, Ts, qstar = _probes(k)
    with pytest.raises(ValueError, match="edge"):
        profile_interval_o1(t, cs, qs, qstar, 1e-3, Ts=Ts, k_grid=np.logspace(-5, 1, 61))
