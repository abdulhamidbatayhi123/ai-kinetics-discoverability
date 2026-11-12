"""Source Data for the main data figures (Figs. 2-4), one Excel file per figure, one sheet per panel.

Every value is read from the files the figure scripts read (results/p2_figdata.json, results/p2_verdicts.json,
results/p2_o1.json, results/p2_e6_modelselect.json, data/p2/manifest.json and the ground-truth fields); nothing is
recomputed except the plotted series of Fig. 2, which use exactly the calls of fig_p2_examples.py.

    python p2_source_data.py  ->  paper2/source_data/Source_Data_Fig{2,3,4}.xlsx
"""
import json
import os

import numpy as np
import pandas as pd

from p2_observe import load_cell, observe

OUT = os.path.join("paper2", "source_data")
FD = json.load(open("results/p2_figdata.json"))
V = json.load(open("results/p2_verdicts.json"))
CELLS = json.load(open("data/p2/manifest.json"))["cells"]
PE = {"0.2": 470, "1.0": 94, "5.0": 19}


def levels_df(levels, what):
    return pd.DataFrame([{"Da": d, f"{what}_successes": a, "replicates": n, f"{what}_fraction": a / n}
                         for d, a, n in levels])


def fig2(w):
    import fig_p2_examples as E
    fd = FD["h2b"][E.SLICE]
    for tag, lab in E.DAS:
        name = f"langmuir_L1_pe1_da{tag}"
        f, man = load_cell(name)
        ts, qm = man["t_stoich_s"], man["q_max"]
        obs = observe(name, E.REP, E.SIGMA, 0.0, "O1")
        c, q, T = (obs["channels"][k][E.PROBE] for k in ("c", "q", "T"))
        it = np.linspace(0, len(f["t"]) - 1, len(obs["t"])).round().astype(int)
        iz = np.linspace(0, len(f["z"]) - 1, 20).round().astype(int)[E.PROBE]
        o3 = observe(name, E.REP, E.SIGMA, 0.0, "O3")
        pd.DataFrame({"t_over_tstoich": obs["t"] / ts, "q_true_over_qmax": f["q"][iz, it] / qm,
                      "q_observed_over_qmax": q / qm, "qstar_measured_over_qmax": obs["qstar_meas"](c, T) / qm,
                      "outlet_c_true_over_cin": f["c"][-1, it] / man["c_in"],
                      "outlet_c_observed_over_cin": o3["channels"]["c"][0] / man["c_in"]}
                     ).to_excel(w, sheet_name=f"Da={lab}", index=False)
    rows = []
    for tag, lab in E.DAS:
        da = CELLS[f"langmuir_L1_pe1_da{tag}"]["Da"]
        a_d, n_d = next((a, n) for d, a, n in fd["disc"] if abs(np.log10(d) - np.log10(da)) < 1e-6)
        a_i, n_i = next((a, n) for d, a, n in fd["ident"] if abs(np.log10(d) - np.log10(da)) < 1e-6)
        rows.append({"Da": da, "discovered": a_d, "identifiable": a_i, "replicates": n_d})
    pd.DataFrame(rows).to_excel(w, sheet_name="counts", index=False)


def fig3(w):
    for iso, sheet in (("langmuir", "a_Langmuir"), ("step", "b_step")):
        parts = []
        for s in (0.005, 0.02, 0.05):
            k = f"sigma={s}|eps=0.0|{iso}|pe=1.0"
            d = levels_df(FD["h2b"][k]["disc"], "discovery").merge(
                levels_df(FD["h2b"][k]["ident"], "identifiable").drop(columns="replicates"), on="Da")
            d.insert(0, "noise_sigma", s)
            v = V["H2b"][k]
            d["Da_disc"], d["Da_ident"] = v["da_disc"], v["da_ident"]
            parts.append(d)
        pd.concat(parts).to_excel(w, sheet_name=sheet, index=False)
    rows = []
    for k, v in V["H2b"].items():
        s, e, iso, pe = k.split("|")
        rows.append({"noise_sigma": float(s[6:]), "isotherm_error_eps": float(e[4:]), "isotherm": iso,
                     "Peclet_approx": PE[pe[3:]], "Da_disc": v["da_disc"], "Da_disc_ci_low": v["da_disc_ci"][0],
                     "Da_disc_ci_high": v["da_disc_ci"][1], "Da_ident": v["da_ident"],
                     "Da_ident_ci_low": v["da_ident_ci"][0], "Da_ident_ci_high": v["da_ident_ci"][1],
                     "gap_decades": v["gap_decades"], "verdict": v["words"], "best_method": v["best_method"]})
    df = pd.DataFrame(rows)
    df[df.gap_decades.notna()].to_excel(w, sheet_name="c_boundaries", index=False)
    df.to_excel(w, sheet_name="d_all_slices", index=False)


def fig4(w):
    for iso, sheet in (("langmuir", "a_Langmuir"), ("step", "b_step")):
        k = f"sigma=0.02|eps=0.02|{iso}|pe=1.0"
        parts = []
        for m, lv in FD["methods"][k].items():
            d = levels_df(lv, "discovery")
            d.insert(0, "method", m)
            parts.append(d)
        pd.concat(parts).to_excel(w, sheet_name=sheet, index=False)
    rows = []
    for k, v in V["H2b"].items():
        for m, d in (v.get("da_disc_by_method") or {}).items():
            rows.append({"slice": k, "method": m, "Da_disc": d})
    pd.DataFrame(rows).to_excel(w, sheet_name="c_per_method", index=False)
    e6 = json.load(open("results/p2_e6_modelselect.json"))["rows"]
    agg = {}
    for key, r in e6.items():
        n, s, e, rep = key.split("|")
        c = CELLS[n]
        if float(s) == 0.02 and float(e) == 0.02:
            agg.setdefault((c["iso"], c["Da"]), []).append(float(r["success"]))
    rows = [{"isotherm": i, "Da": d, "LDF_chosen_fraction": float(np.mean(x)), "replicates": len(x)}
            for (i, d), x in sorted(agg.items())]
    pd.DataFrame(rows).to_excel(w, sheet_name="d_choice_among_laws", index=False)
    parts = []
    for iso in ("langmuir", "step"):
        k = f"sigma=0.02|eps=0.02|{iso}|pe=1.0"
        d = levels_df(FD["h2b"][k]["disc"], "discovery").merge(
            levels_df(FD["h2b"][k]["ident"], "identifiable").drop(columns="replicates"), on="Da")
        d.insert(0, "isotherm", iso)
        parts.append(d)
    pd.concat(parts).to_excel(w, sheet_name="d_discovery_identifiable", index=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    for n, fn in ((2, fig2), (3, fig3), (4, fig4)):
        p = os.path.join(OUT, f"Source_Data_Fig{n}.xlsx")
        with pd.ExcelWriter(p) as w:
            fn(w)
        print("wrote", p)


if __name__ == "__main__":
    main()
