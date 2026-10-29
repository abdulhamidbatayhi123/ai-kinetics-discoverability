"""Figures 2-4 (fig_p2_results.py) and their data helper (p2_figdata.py) on SYNTHETIC inputs.

Nothing here is a result: every number is made up inside this file, and nothing is written
outside pytest's temporary directory. Two routes:

1. A hand-built verdicts dict with the exact structure p2_analyze.main() writes to
   results/p2_verdicts.json (json.dump(..., default=str), line 440), derived from the code:
     positive_control[iso]       p2_analyze.py 189-193 (p2.analysis.positive_control 259-261)
     H2b[slice]                  p2_analyze.py 212 (key), 225-227, plus disc_vs_ident's
                                 gap_decades and words (p2/analysis.py 150-159); WITHHELD 223-224
     H2b_k_sensitivity[slice]    p2_analyze.py 228-229
     H2b_overall                 p2_analyze.py 231 (p2.analysis.aggregate_h2b 244-250)
     H2b_O2_descriptive[slice]   p2_analyze.py 243-244
     H2a                         p2_analyze.py 271-276 (p2.analysis.r_collapse 142-143; the
                                 rstar tuples become lists in JSON)
     H2c                         p2_analyze.py 301-304 (slice key iso|pe=|eps=), 311-317,
                                 per_eps entries 338-339 (float keys become strings in JSON)
     H2b_O2_O3_descriptive       p2_analyze.py 388-391
     H2d_descriptive             p2_analyze.py 439
2. The real p2_analyze.verdicts() and h2c() on a tiny planted grid (n_boot small), passed
   through JSON as main() does, with p2_figdata's helpers on the same synthetic rows.
"""
import json
import os

import numpy as np
import pytest

import fig_p2_results as F
import p2_figdata as FDm
from p2.analysis import H2B_WORDS
from p2_analyze import WITHHELD

DA = [float(x) for x in np.logspace(-1, 3, 9)]
SIG = EPS = (0.0, 0.005, 0.02, 0.05)
ISOS = ("langmuir", "step")
PES = (0.2, 1.0, 5.0)
METHODS = ("stlsq|weak", "stlsq|strong", "ensemble|weak", "ensemble|strong",
           "best_subset|weak", "best_subset|strong", "m7|strong")


def _ci(v, rng, w=0.15):
    return [v * 10 ** -abs(rng.normal(w, 0.03)), v * 10 ** abs(rng.normal(w, 0.03))]


def synthetic_verdicts(seed=0):
    rng = np.random.default_rng(seed)
    V = {"positive_control": {iso: {"passed": True, "best_method": "best_subset|weak",
                                    "success_fraction": 1.0, "identifiable_fraction": 1.0,
                                    "n_success": 45, "n_ident": 45, "need": 0.9} for iso in ISOS},
         "H2b": {}, "H2b_k_sensitivity": {}, "H2b_O2_descriptive": {}}
    for s in SIG:
        for e in EPS:
            for iso in ISOS:
                for pe in PES:
                    key = f"sigma={s}|eps={e}|{iso}|pe={pe}"
                    disc = 10 ** rng.uniform(0.3, 2.2) if rng.uniform() > 0.1 else None
                    ident = 10 ** rng.uniform(0.5, 2.5) if rng.uniform() > 0.05 else None
                    if disc is None or ident is None:
                        gw = {"gap_decades": None, "words": "no boundary on the grid for one of the "
                                                            "two; reported as the range tested"}
                    else:
                        g = float(np.log10(disc) - np.log10(ident))
                        w = H2B_WORDS[0] if g <= -0.25 else H2B_WORDS[2] if g >= 0.25 else H2B_WORDS[1]
                        gw = {"gap_decades": g, "words": w}
                    if iso == "step" and pe == 5.0 and s == 0.05:
                        gw = {**gw, "words": WITHHELD}              # exercise the hatched cell
                    V["H2b"][key] = {
                        "best_method": "best_subset|weak", "da_disc": disc,
                        "da_disc_ci": _ci(disc, rng) if disc else [None, None],
                        "da_ident": ident, "da_ident_ci": _ci(ident, rng) if ident else [None, None],
                        "da_disc_by_method": {m: (10 ** rng.uniform(0, 2.5) if rng.uniform() > 0.2 else None)
                                              for m in METHODS[:6]}, **gw}
                    V["H2b_k_sensitivity"][key] = {"best_method": "best_subset|weak", "da_disc_k": disc,
                                                   "da_disc_k_ci": [None, None], **gw}
                    V["H2b_O2_descriptive"][key] = {"best_method": "stlsq|weak", "da_disc": None,
                                                    "da_disc_ci": [None, None]}
    V["H2b_overall"] = {"words": "mixed: the position of discovery relative to identifiability depends on the slice",
                        "counts": {w: 1 for w in H2B_WORDS}, "counts_by_axis": {}, "n_with_verdict": 3,
                        "no_verdict": [], "isotherms_withheld": []}
    V["H2b_k_sensitivity_overall"] = dict(V["H2b_overall"])
    rstar = {}
    for obs in ("O1", "O2"):
        for iso in ISOS:
            for pe in PES:
                r = 10 ** rng.uniform(0.8, 1.3)
                rstar[f"{obs}|{iso}|pe={pe}|best_subset|weak"] = [r, r / 1.5, r * 1.5]
    nc = rstar.pop("O2|step|pe=5.0|best_subset|weak")
    del nc
    logs = [np.log10(v[0]) for v in rstar.values()]
    sp = float(max(logs) - min(logs))
    V["H2a"] = {"rstar": rstar, "no_crossing": ["O2|step|pe=5.0|best_subset|weak"],
                "spread_decades": sp, "spread_ci": [sp * 0.7, sp * 1.4],
                "words": f"inconclusive: R narrows the boundary to a spread of {sp:.2f} decades"}
    slices, per_eps = {}, {}
    for iso in ISOS:
        for pe in PES:
            for e in (0.005, 0.02, 0.05):
                sh = float(rng.normal(0.3, 0.1)) if not (iso == "step" and pe == 0.2 and e == 0.05) else None
                slices[f"{iso}|pe={pe}|eps={e}"] = {
                    "best_strong_method": "best_subset|strong", "shift": sh,
                    "shift_ci": [sh - 0.12, sh + 0.12] if sh is not None else [None, None],
                    "best_any_form_method": "best_subset|weak", "shift_vs_best_any_form": sh,
                    "words": "EIV moves the boundary by 2.00x"}
    for e in ("0.005", "0.02", "0.05"):
        vals = [v["shift"] for k, v in slices.items() if k.endswith(f"eps={e}") and v["shift"] is not None]
        per_eps[e] = {"n_slices_with_verdict": len(vals), "n_detectable": sum(v >= 0.25 for v in vals),
                      "holds": True, "median_shift": float(np.median(vals)), "words": "x"}
    V["H2c"] = {"slices": slices, "per_eps": per_eps, "h2c_holds": True, "h2c_falsified": False,
                "isotherms_withheld": []}
    V["H2b_O2_O3_descriptive"] = {}
    V["H2d_descriptive"] = {}
    return json.loads(json.dumps(V, default=str))               # as main() writes it


def _levels(center, rng, n=45, rising=False, xs=DA):
    out = []
    for x in xs:
        z = np.log10(x) - np.log10(center)
        p = 1 / (1 + np.exp(4 * z if not rising else -4 * z))
        out.append([x, int(rng.binomial(n, p)), n])
    return out


def synthetic_figdata(V, seed=1):
    rng = np.random.default_rng(seed)
    h2b, methods = {}, {}
    for k, v in V["H2b"].items():
        d = _levels(v["da_disc"] or 30.0, rng)
        i = _levels(v["da_ident"] or 100.0, rng)
        h2b[k] = {"best_method": v["best_method"], "disc": d, "disc_fit": FDm.logistic_fit(d),
                  "ident": i, "ident_fit": FDm.logistic_fit(i)}
        if "pe=1.0" in k and k.startswith("sigma=0.02|eps=0.02"):
            methods[k] = {m: _levels(10 ** rng.uniform(0.5, 2), rng)
                          for m in METHODS + ("eiv_best_subset|strong", "slow_manifold|strong")}
    h2a = {}
    for c in list(V["H2a"]["rstar"]) + V["H2a"]["no_crossing"]:
        lv = _levels(10.0, rng, rising=True, xs=[float(x) for x in np.logspace(-0.5, 2.5, 40)])
        h2a[c] = {"levels": lv, "fit": FDm.logistic_fit(lv, rising=True)}
    return {"h2b": h2b, "h2a": h2a, "methods": methods}


def _check(paths):
    assert len(paths) == 6
    for p in paths:
        assert os.path.getsize(p) > 1000, p
        with open(p, "rb") as f:
            head = f.read(8)
        assert head.startswith(b"%PDF") if p.endswith(".pdf") else head.startswith(b"\x89PNG"), p


def test_figures_from_handbuilt_verdicts(tmp_path):
    V = synthetic_verdicts()
    FD = synthetic_figdata(V)
    _check(F.make_all(V, FD, DA, str(tmp_path / "full")))
    _check(F.make_all(V, None, DA, str(tmp_path / "no_figdata")))   # degraded: boundaries only


def test_figures_handle_withheld_and_empty_verdicts(tmp_path):
    V = synthetic_verdicts(seed=3)
    V["H2a"] = {"words": WITHHELD}
    V["H2c"] = {"slices": {}, "per_eps": {}, "h2c_holds": None, "h2c_falsified": None,
                "isotherms_withheld": list(ISOS), "words": WITHHELD}
    _check(F.make_all(V, None, DA, str(tmp_path)))


def _planted(rng, n_rep):
    """Two isotherms, Pe x1, sigma = eps = 2 %; A (Da* 10), B (Da* 30), M5 (Da* 90),
    identifiability (Da* 300); delta = 1 / Da so success rises with R."""
    cells = {}
    for iso in ISOS:
        for d in DA:
            cells[f"{iso}_{d:.3g}"] = {"iso": iso, "law": "L1", "pe_mult": 1.0, "Da": d, "k_LDF": d / 7200.0}
    P = lambda d, b: 1.0 / (1.0 + np.exp(4.0 * (np.log10(d) - np.log10(b))))
    o1, m5, ident = {}, {}, {}
    for nm, c in cells.items():
        for rep in range(n_rep):
            u = rng.uniform(size=4)
            o1[f"{nm}|0.02|0.02|{rep}|stlsq|weak"] = {"success": bool(u[0] < P(c["Da"], 10))}
            o1[f"{nm}|0.02|0.02|{rep}|best_subset|weak"] = (
                {"success": False, "error": "synthetic"} if rep == 20 else {"success": bool(u[1] < P(c["Da"], 30))})
            m5[f"{nm}|0.02|0.02|{rep}|eiv_best_subset|strong"] = {"success": bool(u[2] < P(c["Da"], 90))}
            ident[f"{nm}|0.02|0.02|{rep}|profile|o1"] = {"success": bool(u[3] < P(c["Da"], 300))}
    rstats = {nm: {"delta": 1.0 / c["Da"], "eps_rec": 0.0} for nm, c in cells.items()}
    return cells, o1, m5, ident, rstats


def test_figures_from_the_real_analysis_on_a_planted_grid(tmp_path):
    from p2_analyze import N_SEL, h2c, verdicts
    from p2_grid_o1 import N_REP
    cells, o1, m5, ident, rstats = _planted(np.random.default_rng(7), N_REP)
    out = verdicts(cells, o1, {}, ident, rstats, n_boot=20)
    out["H2c"] = h2c(cells, o1, m5, n_boot=20)
    V = json.loads(json.dumps(out, default=str))
    # the helper reads the best method from the verdicts and counts estimation replicates only
    o1c = FDm.level_counts(o1, cells)
    idc = FDm.level_counts(ident, cells)
    h2b = FDm.h2b_curves(V, cells, o1c, idc)
    k = "sigma=0.02|eps=0.02|langmuir|pe=1.0"
    assert h2b[k]["best_method"] == V["H2b"][k]["best_method"] == "best_subset|weak"
    assert [n for _, _, n in h2b[k]["disc"]] == [N_REP - N_SEL] * len(DA)
    assert h2b[k]["disc"][0][1] <= N_REP - N_SEL - 1          # the error row at rep 20 is a failure
    conds = FDm.h2a_conditions(V)
    assert conds and all(c.startswith("O1|") for c in conds)
    h2a = FDm.h2a_levels(o1, cells, rstats, conds, "O1")
    assert set(h2a) == set(conds) and all(d["fit"] for d in h2a.values())
    allc = {**o1c, **FDm.level_counts(m5, cells)}
    meth = FDm.methods_by_slice(allc, cells, sorted(V["H2b"]))
    assert "eiv_best_subset|strong" in meth[k]
    FD = json.loads(json.dumps({"h2b": h2b, "h2a": h2a, "methods": meth}))
    _check(F.make_all(V, FD, DA, str(tmp_path)))


def test_slice_key_round_trips():
    assert F._key(0.02, 0.005, "step", 1) == "sigma=0.02|eps=0.005|step|pe=1.0"
    assert F._parse_slice("sigma=0.0|eps=0.05|langmuir|pe=0.2") == (0.0, 0.05, "langmuir", 0.2)
    assert FDm.parse_condition("O2|step|pe=5.0|best_subset|weak") == ("O2", "step", 5.0, "best_subset|weak")


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
