"""Extended Data Fig. 6: the second system (E12b, reversible reaction in a stirred tank; exploratory).

Reads results/p2_e12b_summary.json (best discovery method and identifiability fractions per Da, replicates 15-59)
and results/p2_e12_noisefree.json (discovery on exact data). Nothing is estimated here.

    python fig_p2_ed6_reaction.py  ->  paper2/fig_ed6_reaction.{pdf,png,prov.json}
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import p2_figstyle as S  # noqa: E402

SUM = json.load(open("results/p2_e12b_summary.json"))
NF = json.load(open("results/p2_e12_noisefree.json"))["E12b"]["by_da"]
SLICES = (("sigma=0.005|eps=0.0", "noise 0.5 %, exact K"), ("sigma=0.005|eps=0.02", "noise 0.5 %, K error 2 %"),
          ("sigma=0.02|eps=0.0", "noise 2 %, exact K"), ("sigma=0.02|eps=0.02", "noise 2 %, K error 2 %"))


def main():
    S.apply()
    fig, axs = plt.subplots(1, 4, figsize=(S.W2, 58 * S.MM), layout="constrained", sharey=True)
    for ax, (key, title), let in zip(axs, SLICES, "abcd"):
        v = SUM[key]
        x = np.log10([float(d) for d in v["disc_by_da"]])
        ax.plot(x, list(v["disc_by_da"].values()), "-o", color=S.ROLE["disc"], ms=2.8, lw=1.0)
        xi = np.log10([float(d) for d in v["ident_by_da"]])
        ax.plot(xi, list(v["ident_by_da"].values()), "--s", color=S.ROLE["ident"], mfc="white", ms=2.8, lw=1.0)
        best = v["best_method"]                     # this slice's selected method, on exact data
        for d, r in NF.items():
            ok = r[best]
            ax.plot(np.log10(float(d)), 1.04 if ok else -0.04, lw=0, marker="v", ms=3, color=S.C["dark"],
                    mfc=S.C["dark"] if ok else "white")
        ax.text(0.47, 0.62, best.replace("_", " ").replace("|", ", "), transform=ax.transAxes, ha="center",
                fontsize=5.5, color=S.C["dark"])
        ax.axhline(0.5, color=S.C["grey"], lw=0.5)
        ax.set_title(title, fontsize=6.5)
        ax.set_xticks(range(-1, 4))
        ax.set_ylim(-0.08, 1.1)
        ax.set_xlabel(r"$\log_{10}$ Da (Da = $k\,\tau$)")
        S.letter(ax, let)
    axs[0].set_ylabel("fraction of estimation replicates")
    hd = [Line2D([], [], color=S.ROLE["disc"], marker="o", ms=2.8, label="law discovered (best method)"),
          Line2D([], [], color=S.ROLE["ident"], ls="--", marker="s", mfc="white", ms=2.8, label="k identifiable"),
          Line2D([], [], color=S.C["dark"], lw=0, marker="v", ms=3, label="same method on exact data: succeeds (post hoc)"),
          Line2D([], [], color=S.C["dark"], lw=0, marker="v", mfc="white", ms=3, label="fails")]
    fig.legend(handles=hd, loc="outside lower center", ncol=4, fontsize=6, frameon=False)
    return fig


if __name__ == "__main__":
    fig = main()
    for p in S.save(fig, "paper2/fig_ed6_reaction",
                    inputs=("results/p2_e12b_summary.json", "results/p2_e12_noisefree.json")):
        print("wrote", p)
