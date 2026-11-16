"""How the two symbolic methods fail at the lowest rates (post hoc, descriptive; 2026-11-16).

Symbolic regression (M7, results/p2_extra_m7.json) and parallel symbolic enumeration (E14,
results/p2_e14_rows.json) both fail at Da = 0.1 and 0.316 in every slice. No fit is rerun; this
script tallies the stored supports.

M7 rows store sorted(coefs): every library feature (T, c, c*q, c^2, q, q^2, qstar; zero coefficients
included) plus any monomial outside the library, which the strict bridge in p2/pysr_method.py records
under its own string and which makes the row fail. Only those extra monomials can be read from the
row; a numeric string is a constant term (the M7 library leaves out the constant feature "1").
E14 rows store the monomials of the returned expression, so a missing qstar can be read directly.

    python p2_lowda_diag.py   ->  results/p2_lowda_diag.json
"""
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = {"T", "c", "c*q", "c^2", "q", "q^2", "qstar"}
DA = re.compile(r"_da([^|]+)\|")
LOW = ("0.1", "0.316")


def isnum(t):
    try:
        float(t)
        return True
    except ValueError:
        return False


def load(name):
    with open(os.path.join(HERE, "results", name), encoding="utf-8") as f:
        return json.load(f)["rows"]


def main():
    by_da = defaultdict(lambda: {"n": 0, "n_success": 0, "n_constant": 0})
    for k, v in load("p2_extra_m7.json").items():
        b = by_da[DA.search(k).group(1)]
        b["n"] += 1
        b["n_success"] += bool(v["success"])
        b["n_constant"] += any(isnum(t) for t in set(v.get("support") or []) - LIB)
    low = [by_da[d] for d in LOW]
    same = [v for k, v in load("p2_extra_m7.json").items()
            if DA.search(k).group(1) in LOW and 15 <= int(k.split("|")[3]) <= 29]   # E14's replicates
    high = {d: b for d, b in by_da.items() if d not in LOW}
    pse = [v for k, v in load("p2_e14_rows.json").items() if DA.search(k).group(1) in LOW]
    out = {
        "description": "Stored supports of the two symbolic methods; M7 constant terms by Da and E14 fits "
                       "without qstar at Da 0.1 and 0.316 (post hoc, descriptive).",
        "m7_by_da": dict(sorted(by_da.items(), key=lambda kv: float(kv[0]))),
        "m7_low": {"n": sum(b["n"] for b in low), "n_success": sum(b["n_success"] for b in low),
                   "n_constant": sum(b["n_constant"] for b in low)},
        "m7_low_reps_15_29": {"n": len(same), "n_constant": sum(any(isnum(t) for t in set(v.get("support") or []) - LIB)
                                                                 for v in same)},
        "m7_higher_max_constant_fraction": max(b["n_constant"] / b["n"] for b in high.values()),
        "pse_low": {"n": len(pse), "n_success": sum(bool(v["success"]) for v in pse),
                    "n_without_qstar": sum(not any("qstar" in t for t in (v.get("support") or [])) for v in pse)},
    }
    with open(os.path.join(HERE, "results", "p2_lowda_diag.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
