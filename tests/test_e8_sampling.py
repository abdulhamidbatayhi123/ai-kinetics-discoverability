"""E8: the 200-sample observation is the grid's own (p2_observe.observe), and 400 samples keep the
probes and the noise SD rule."""
import numpy as np


def test_nt200_is_observe():
    from p2_e8_sampling import observe_nt
    from p2_observe import observe
    for name, rep, s in (("step_L1_pe1_da31.6", 3, 0.02), ("langmuir_L1_pe1_da1", 17, 0.005)):
        a, b = observe_nt(name, rep, s, 200), observe(name, rep, s, 0.0, "O1")
        assert np.array_equal(a["t"], b["t"])
        for ch in ("c", "q", "T"):
            assert np.array_equal(a["channels"][ch], b["channels"][ch])


def test_nt400_every_stored_time_same_noise_sd():
    from p2_e8_sampling import observe_nt
    from p2_observe import load_cell
    name = "step_L1_pe1_da31.6"
    f, _ = load_cell(name)
    a = observe_nt(name, 3, 0.02, 400)
    assert np.array_equal(a["t"], f["t"])
    iz = np.linspace(0, len(f["z"]) - 1, 20).round().astype(int)
    resid = a["channels"]["c"] - f["c"][iz]
    assert abs(np.std(resid) / (0.02 * float(f["c"].max() - f["c"].min())) - 1) < 0.05
