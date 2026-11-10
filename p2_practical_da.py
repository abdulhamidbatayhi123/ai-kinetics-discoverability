"""Where real columns sit on the Da map: Da = k * t_stoich from published inputs (Supplementary Table 2).

Inputs: data/practical_da_sources.csv, one row per source and condition, with the rate constant, its
basis and location in the paper, and either a stated time (t_stoich or t50) or the bed mass W, the
uptake q at the feed, and the feed flow from which t_stoich = W q / n_feed is computed. Where a paper
does not say whether its volumetric flow is at column conditions or at 273.15 K and 1 atm, both are
used and the range is reported. Values read off figures are marked in the CSV.

Sources were compiled by the Claude Science literature task T3 (AgentHub, 2026-11-10) and every input
used here was checked by the author against the papers (Crossref records checked 2026-11-10).

    python p2_practical_da.py      ->  results/p2_practical_da.json
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R = 8.314462618
P_NORMAL, T_NORMAL = 101325.0, 273.15


def fnum(s):
    return float(s) if s not in ("", None) else None


def t_stoich(row):
    """(low, high) stoichiometric time in s."""
    if row["t_stoich_given_s"]:
        t = float(row["t_stoich_given_s"])
        return t, t
    W, Q, y = float(row["W_kg"]), float(row["Q_m3_s"]), float(row["y_feed"])
    qs = (float(row["q_low"]), float(row["q_high"]))
    if row["Q_basis"].startswith("column or"):
        flows = [y * float(row["P_bar"]) * 1e5 * Q / (R * float(row["T_K"])),   # at column T, P
                 y * P_NORMAL * Q / (R * T_NORMAL)]                               # at 273.15 K, 1 atm
    else:
        flows = [y * float(row["P_bar"]) * 1e5 * Q / (R * float(row["T_K"]))]
    ts = [W * q / n for q in qs for n in flows]
    return min(ts), max(ts)


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "practical_da_sources.csv"), encoding="utf-8")))
    out_rows, by_source = [], {}
    for r in rows:
        t_lo, t_hi = t_stoich(r)
        k_lo, k_hi = float(r["k_low"]), float(r["k_high"])
        da_lo, da_hi = k_lo * t_lo, k_hi * t_hi
        out_rows.append({"source": r["source"], "doi": r["doi"], "system": r["system"], "case": r["case"],
                         "k_basis": r["k_basis"], "k_low": k_lo, "k_high": k_hi, "k_where": r["k_where"],
                         "t_stoich_low_s": t_lo, "t_stoich_high_s": t_hi,
                         "t_where": r["t_where"] or ("W q / feed flow; q: " + r["q_where"]),
                         "Da_low": da_lo, "Da_high": da_hi})
        s = by_source.setdefault(r["source"], {"system": r["system"], "doi": r["doi"], "k_basis": r["k_basis"],
                                               "Da_low": da_lo, "Da_high": da_hi, "n_rows": 0})
        s["Da_low"], s["Da_high"] = min(s["Da_low"], da_lo), max(s["Da_high"], da_hi)
        s["n_rows"] += 1
    phys = [v for k, v in by_source.items() if "amine" not in v["system"]]
    summary = {"physisorbent_Da_low": min(v["Da_low"] for v in phys),
               "physisorbent_Da_high": max(v["Da_high"] for v in phys),
               "chemisorbent_Da": [v for v in by_source.values() if "amine" in v["system"]][0]}
    res = {"description": __doc__.strip().splitlines()[0], "rows": out_rows, "by_source": by_source,
           "summary": summary,
           "not_used": {"Buechner and Pini 2026 (doi:10.1021/acs.langmuir.6c00250)":
                        "k computed from a macropore correlation; the LDF form that sets its loading basis is in the "
                        "SI, not checked; Da > 10^3 under either reading",
                        "Lassitter et al. 2024 coated tube":
                        "no k or t_stoich given; the paper states that its group k rho n* L/(v C0), which is Da, is "
                        "'always very large for the cases examined' (Sec. 3.6)"}}
    path = os.path.join(HERE, "results", "p2_practical_da.json")
    json.dump(res, open(path, "w", encoding="utf-8"), indent=1)
    for k, v in by_source.items():
        print(f"{k:28s} Da {v['Da_low']:9.1f} .. {v['Da_high']:9.1f}  ({v['n_rows']} rows, {v['k_basis']})")
    print("physisorbent range", round(summary["physisorbent_Da_low"]), round(summary["physisorbent_Da_high"]))


if __name__ == "__main__":
    main()
