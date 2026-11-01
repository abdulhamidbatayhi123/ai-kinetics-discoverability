"""RETRACTIONS_P2 B88: PREREG_P2 A4 says M1 keeps the best parameters seen. As run, a solver
failure (diffrax max_steps) during training propagated out of L-BFGS and the fit was recorded as
an error with nothing read out. The training loop must stop on such a failure and keep the best."""
import numpy as np
import pytest


def _objective(n_fail_at=None):
    calls = {"n": 0}

    def vg(x):
        calls["n"] += 1
        if n_fail_at is not None and calls["n"] >= n_fail_at:
            raise ValueError("INTERNAL: CpuCallback error: The maximum number of solver steps was reached.")
        from scipy.optimize import rosen, rosen_der
        x = np.asarray(x, float)
        return float(rosen(x)), rosen_der(x)
    return vg


def test_train_converges_without_failure():
    from p2_grid_extra import _train_lbfgs
    best, hist, stopped = _train_lbfgs(_objective(), np.zeros(3), maxiter=50, budget_s=60)
    assert stopped == "maxiter"
    assert best["f"] < 1e-6 and len(hist) >= 2


def test_solver_failure_keeps_best_parameters():
    from p2_grid_extra import _train_lbfgs
    best, hist, stopped = _train_lbfgs(_objective(n_fail_at=6), np.zeros(3), maxiter=50, budget_s=60)
    assert stopped == "solver"
    assert len(hist) == 5
    assert best["f"] == min(hist) < hist[0]
    assert "maximum number of solver steps" in best["error"]


def test_failure_on_first_evaluation_is_still_an_error():
    from p2_grid_extra import _train_lbfgs
    with pytest.raises(ValueError):
        _train_lbfgs(_objective(n_fail_at=1), np.zeros(3), maxiter=50, budget_s=60)
