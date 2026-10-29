"""Exploratory E3 (EXPLORATORY_P2.md): precision versus coverage, on synthetic rows."""
from p2_e3_coverage import classify, coverage

K = 1e-4
CELLS = {"c_da1": {"Da": 1.0, "k_LDF": K}}


def test_interval_inside_band_missing_k_is_identifiable_but_not_covering():
    # [1.2k, 1.5k] lies inside [k/2, 2k] but excludes k
    assert classify({"lo": 1.2 * K, "hi": 1.5 * K}, K) == (True, False)
    out = coverage(CELLS, {"O2": {"c_da1|0.02|0.0|0": {"lo": 1.2 * K, "hi": 1.5 * K,
                                                       "k": K, "identifiable": True}},
                           "O1": {"c_da1|0.02|0.0|0|profile|o1":
                                  {"interval": {"lo": 0.9 * K, "hi": 1.1 * K}, "success": True}}})
    o2 = out["per_model"]["O2"]
    assert (o2["identifiable"], o2["covers"], o2["identifiable_misses"]) == (1, 0, 1)
    assert o2["frac_identifiable_missing_k"] == 1.0
    o1 = out["per_model"]["O1"]
    assert (o1["identifiable_covers"], o1["frac_identifiable_missing_k"]) == (1, 0.0)
    assert out["stored_vs_recomputed_mismatches"] == []


def test_error_row_counts_as_neither():
    # even with an interval that would pass, the error makes it a failure
    row = {"error": "solver failed", "lo": 0.9 * K, "hi": 1.1 * K, "k": K}
    assert classify(row, K) == (False, False)
    t = coverage(CELLS, {"O3": {"c_da1|0.0|0.0|0": row}})["per_model"]["O3"]
    assert (t["n"], t["n_error"], t["identifiable"], t["covers"]) == (1, 1, 0, 0)
    assert t["not_identifiable_misses"] == 1 and t["frac_identifiable_missing_k"] is None


def test_wide_interval_covers_but_is_not_identifiable():
    assert classify({"interval": {"lo": 0.1 * K, "hi": 3 * K}}, K) == (False, True)
