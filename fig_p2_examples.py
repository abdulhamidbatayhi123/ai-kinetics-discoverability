"""Paper 2, Figure 3: what the data look like where discovery works, where only identifiability
works, and where neither does (real observations, no schematic).

Langmuir sorbent, Pe ~94 (pe_mult 1.0), noise 2 %, exact isotherm, at Da = 0.316, 31.6 and 1000.
a-c, one interior probe (the 11th of 20, mid-column) as the methods see it (O1, replicate 15):
    observed uptake q (points, every 4th time shown), the true q (line) and the measured isotherm
    q*(c, T) evaluated on the observed c and T (dashed); the shaded band is the driving force
    q* - q that discovery has to resolve.
d-f, the outlet breakthrough c/c_in (O3 view of the same replicate) against t / t_stoich.
Each top panel states the slice's success counts over the 45 estimation replicates (from
results/p2_figdata.json) and the law the best method returned for replicate 15 (results/p2_o1.json).

    python fig_p2_examples.py   -> paper2/fig_p2_examples.{pdf,png,prov.json}
"""
import json

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import p2_figstyle as S  # noqa: E402
from p2_observe import load_cell, observe  # noqa: E402

SLICE = "sigma=0.02|eps=0.0|langmuir|pe=1.0"
DAS = (("0.316", "0.32"), ("31.6", "31.6"), ("1e+03", "1000"))
REP, PROBE, SIGMA = 15, 10, 0.02
TERM = {"1": "1", "c": "c", "q": "q", "T": "T", "c*q": "cq", "q^2": "q²", "c^2": "c²", "qstar": "q*"}


def law_text(row):
    sup = ", ".join(TERM.get(t, t) for t in row["support"])
    return f"{{{sup}}}", bool(row["success"])


def main():
    S.apply()
    fd = json.load(open("results/p2_figdata.json"))["h2b"][SLICE]
    o1 = json.load(open("results/p2_o1.json"))["rows"]
    best = fd["best_method"]
    count = lambda lv, da: next((a, n) for d, a, n in lv if abs(np.log10(d) - np.log10(da)) < 1e-6)
    fig, axs = plt.subplots(2, 3, figsize=(S.W2, 92 * S.MM), layout="constrained",
                            gridspec_kw={"height_ratios": [1.25, 1.0]})
    for j, (tag, lab) in enumerate(DAS):
        name = f"langmuir_L1_pe1_da{tag}"
        f, man = load_cell(name)
        ts = man["t_stoich_s"]
        obs = observe(name, REP, SIGMA, 0.0, "O1")
        t = obs["t"] / ts
        c, q, T = (obs["channels"][k][PROBE] for k in ("c", "q", "T"))
        it = np.linspace(0, len(f["t"]) - 1, len(obs["t"])).round().astype(int)
        iz = np.linspace(0, len(f["z"]) - 1, 20).round().astype(int)[PROBE]
        q_true = f["q"][iz, it]
        qs = obs["qstar_meas"](c, T)
        qm = man["q_max"]
        ax = axs[0, j]
        ax.fill_between(t, q_true / qm, qs / qm, color="#cfe2f3", lw=0, label="driving force q* − q")
        ax.plot(t, qs / qm, ls="--", color=S.OI["dark"], lw=0.8, label="measured isotherm q*(c, T)")
        ax.plot(t, q_true / qm, color=S.ROLE["disc"], lw=1.1, label="simulated (true)")
        ax.plot(t[::4], q[::4] / qm, "o", ms=1.6, color=S.OI["dark"], label="observed (2 % noise)")
        a_d, n_d = count(fd["disc"], man["Da"])
        a_i, n_i = count(fd["ident"], man["Da"])
        law, ok = law_text(o1[f"{name}|{SIGMA}|0.0|{REP}|{best}"])
        ax.set_title(f"Da = {lab}", loc="center", fontsize=7)
        ax.text(0.98, 0.04, f"discovered {a_d}/{n_d}, identifiable {a_i}/{n_i}\n"
                f"returned law: {law} ({'correct' if ok else 'wrong'})",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=5.6)
        ax.set_xlim(0, t.max())
        ax.set_ylim(0, 1.05 * max(qs.max(), q_true.max()) / qm)
        ax.set_xlabel(r"$t/t_{stoich}$", labelpad=1)
        if j == 0:
            ax.set_ylabel(r"uptake $q/q_{max}$ (mid-column probe)")
        o3 = observe(name, REP, SIGMA, 0.0, "O3")
        b = axs[1, j]
        b.plot(o3["t"] / ts, f["c"][-1, it] / man["c_in"], color=S.ROLE["disc"], lw=1.1, label="true outlet")
        b.plot(o3["t"][::4] / ts, o3["channels"]["c"][0][::4] / man["c_in"], "o", ms=1.6, color=S.OI["dark"],
               label="observed outlet")
        b.set_xlim(0, (o3["t"] / ts).max())
        b.set_ylim(-0.05, 1.1)
        b.set_xlabel(r"$t/t_{stoich}$", labelpad=1)
        if j == 0:
            b.set_ylabel(r"outlet $c/c_{in}$")
    for ax, l in zip(axs.flat, "abcdef"):
        S.letter(ax, l, x=-0.14)
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="outside lower center", ncol=4, fontsize=5.8, frameon=False)
    return fig


if __name__ == "__main__":
    fig = main()
    for p in S.save(fig, "paper2/fig_p2_examples",
                    inputs=("results/p2_figdata.json", "results/p2_o1.json", "data/p2/manifest.json")):
        print("wrote", p)
