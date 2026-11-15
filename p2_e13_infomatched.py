"""E13 (post hoc, declared in EXPLORATORY_P2.md before running): information-matched sampling.

E8's unchanged code (p2_e8_sampling.py) at the grid's 200 observation times with the noise SD per sample divided
by sqrt(10), run on Kaggle (kaggle_e13/). At fixed noise per sample the information about a parameter grows with
n / sigma^2, so these runs carry about the information of E11's 1,996 times at the original noise, at the grid's
coarse resolution. Boundaries as in E8 and E11: best discovery method chosen on replicates 0..14, logistic 50 %
crossings on replicates 15..59 (p2.analysis). The comparison with E11 (pool "both") and with E8's 200-time run is
read by the rule fixed in EXPLORATORY_P2.md E13.

    python p2_e13_infomatched.py summary kaggle_e13/out/k*/e13_part*.json
        -> results/p2_e13_rows.json, results/p2_e13_summary.json
"""
import json
import math
import sys

import p2_e8_sampling as E8

SIGMAS = (0.005 / math.sqrt(10), 0.02 / math.sqrt(10))
ORIG = (0.005, 0.02)
N_T = 200
ROWS = "results/p2_e13_rows.json"
SUMMARY = "results/p2_e13_summary.json"
TOL = 0.25                                    # the pre-registered verdict threshold, in decades


def expected_keys():
    names, _ = E8.expected_keys()
    return {f"{n}|{s!r}|{N_T}|{r}" for n in names for s in SIGMAS for r in range(E8.N_REP)}


def _dex(a, b):
    return math.log10(a / b) if a and b else None


def compare(summ, e11, e8):
    """The reading fixed in advance: E13 against E11 (information matched, 10x resolution) and E8 (same
    resolution, 10x less information), per (isotherm, sigma) pair."""
    pairs, disc_class, ident_class = {}, [], []
    for iso in ("langmuir", "step"):
        for so, sr in zip(ORIG, SIGMAS):
            a = summ[f"{iso}|sigma={sr}|n_t={N_T}"]
            b = e11[f"{iso}|sigma={so}|both"]
            c = e8[f"{iso}|sigma={so}|n_t={N_T}"]
            d_disc = _dex(a["da_disc"], b["da_disc"])
            if d_disc is None:
                cls_d = "no boundary in one of the two"
            elif abs(d_disc) <= TOL:
                cls_d = "information"
            elif d_disc < -TOL:
                cls_d = "resolution"
            else:
                cls_d = "coarse sampling better"
            disc_class.append(cls_d)
            if a["da_ident"] and b["da_ident"]:
                d_id = _dex(a["da_ident"], b["da_ident"])
                cls_i = "information" if abs(d_id) <= TOL else ("resolution" if d_id < -TOL else "coarse sampling better")
            else:
                d_id = None
                cls_i = ("censored: E11 beyond the grid, E13 on it" if a["da_ident"] and not b["da_ident"] else
                         "censored: E13 beyond the grid, E11 on it" if b["da_ident"] and not a["da_ident"] else
                         "both beyond the grid")
            ident_class.append(cls_i)
            gap = _dex(a["da_ident"], a["da_disc"])
            pairs[f"{iso}|sigma={so}"] = {
                "e13": {k: a[k] for k in ("best_method", "da_disc", "da_ident", "da_select")},
                "e11_both": {k: b[k] for k in ("best_method", "da_disc", "da_ident", "da_select")},
                "e8_200": {k: c[k] for k in ("best_method", "da_disc", "da_ident", "da_select")},
                "disc_e13_minus_e11_decades": d_disc, "disc_class": cls_d,
                "disc_e13_minus_e8_decades": _dex(a["da_disc"], c["da_disc"]),
                "ident_e13_minus_e11_decades": d_id, "ident_class": cls_i,
                "ident_e13_minus_e8_decades": _dex(a["da_ident"], c["da_ident"]),
                "select_e13_minus_e11_decades": _dex(a["da_select"], b["da_select"]),
                "gap_e13_decades": gap,
                "fails_first_by_threshold": (gap is not None and gap >= TOL)}
    words = ("information" if all(x == "information" for x in disc_class) else
             "resolution" if all(x == "resolution" for x in disc_class) else "mixed")
    return {"pairs": pairs, "discovery_reading": words, "disc_classes": disc_class, "ident_classes": ident_class}


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "summary":
        sys.exit(__doc__)
    from p2.io_utils import write_atomic
    rows, seen = {}, 0
    for p in sys.argv[2:]:
        part = json.load(open(p))["rows"]
        seen += len(part)
        rows.update(part)
    want = expected_keys()
    if seen != len(rows) or set(rows) != want:
        sys.exit(f"FAIL keys: {seen} read, {len(rows)} unique, {len(want)} expected, "
                 f"{len(set(rows) - want)} unexpected, {len(want - set(rows))} missing")
    errors = sum(1 for r in rows.values() for k in r["disc"] if k.endswith("|error")) + \
        sum(1 for r in rows.values() if "error" in r["ident"]) + \
        sum(1 for r in rows.values() if "select" in r and "error" in r["select"])
    E8.SIGMAS, E8.NTS = SIGMAS, (N_T,)
    summ = E8.summarise(rows)
    out = {"design": {"sigmas": list(SIGMAS), "original_sigmas": list(ORIG), "n_t": N_T, "rows": len(rows),
                      "errors_counted_as_failures": errors},
           "boundaries": summ,
           "reading": compare(summ, json.load(open("results/p2_e11_summary.json")),
                              json.load(open("results/p2_e8_summary.json")))}
    write_atomic({"rows": rows}, ROWS)
    write_atomic(out, SUMMARY)
    print(json.dumps(out["reading"], indent=1))


if __name__ == "__main__":
    main()
