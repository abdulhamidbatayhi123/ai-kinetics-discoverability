"""E6 (EXPLORATORY_P2): the small-candidate model selection must pick the law that generated the
data on a known-answer system (noise-free probes from each candidate law)."""
import numpy as np
import pytest


def _probes(law, k, n_probe=3, n_t=200):
    from p2_e6_modelselect import LAWS, integrate
    from p2.identifiability import UPSAMPLE, _qstar_path
    qstar = lambda c, T: 10.0 * np.asarray(c, float)
    t = np.linspace(0.0, 10.0 / k, n_t)
    cs, qs, Ts = [], [], []
    for j in range(n_probe):
        c = np.clip((t - j * 1.0 / k) * k / 2.0, 0.0, 1.0)
        T = np.full_like(t, 300.0)
        tf, qsf = _qstar_path(t, c, qstar, T)
        q = integrate(LAWS[law], np.array([k]), tf, qsf[None, :], np.array([0.0]))[0, 0, ::UPSAMPLE]
        cs.append(c), qs.append(q), Ts.append(T)
    return t, cs, qs, Ts, qstar


@pytest.mark.parametrize("law", ["ldf", "qdf", "pso"])
def test_selects_the_generating_law(law):
    from p2_e6_modelselect import select
    k = 2e-3 if law != "pso" else 2e-4
    t, cs, qs, Ts, qstar = _probes(law, k)
    best, fits = select(t, cs, qs, qstar, sigma=1e-3, Ts=Ts)
    assert best == law, fits


def test_k_refined_off_grid():
    """B91: the chosen law's k is refined between grid points, not read from the coarse grid."""
    from p2_e6_modelselect import select
    k = 1.37e-3                                   # between the grid points 1.26e-3 and 1.58e-3
    t, cs, qs, Ts, qstar = _probes("ldf", k)
    best, fits = select(t, cs, qs, qstar, sigma=1e-3, Ts=Ts)
    assert best == "ldf"
    assert abs(fits["ldf"]["k_hat"] / k - 1) < 1e-3, fits["ldf"]


def test_ldf_substeps_match_exact_update():
    """The substepped implicit Euler LDF agrees with the exact update for piecewise-linear q*."""
    from p2_e6_modelselect import LAWS, integrate
    from p2.identifiability import _ldf_exact
    tf = np.linspace(0.0, 1000.0, 801)
    qsf = 5.0 * np.clip((tf - 200.0) / 300.0, 0.0, 1.0)
    for k in (1e-3, 1e-2, 1e-1):
        a = integrate(LAWS["ldf"], np.array([k]), tf, qsf[None, :], np.array([0.0]))[0, 0]
        b = _ldf_exact(np.array([k]), tf, qsf, 0.0)[0]
        assert np.max(np.abs(a - b)) < 5e-3 * 5.0, (k, np.max(np.abs(a - b)))
