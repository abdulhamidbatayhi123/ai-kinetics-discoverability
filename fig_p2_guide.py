"""Figure 5: what column data allow, by Damkohler number (a summary of results already reported).

Reads only results files: H2b boundaries (results/p2_verdicts.json), the choice among three laws (E6, post hoc,
results/p2_e6_modelselect.json), where published columns sit (results/p2_practical_da.json, Supplementary
Table 1) and the closest prior study (results/p2_s1_anchor.json). For each condition the bar runs from the bottom
of the grid to the boundary; the darker end segment spans the boundaries over the slices of that condition
(isotherms and Peclet numbers). Nothing is estimated here.

    python fig_p2_guide.py  ->  paper2/fig_p2_guide.{pdf,png,prov.json}
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import p2_figstyle as S  # noqa: E402

V = json.load(open("results/p2_verdicts.json"))["H2b"]
E6 = json.load(open("results/p2_e6_modelselect.json"))["rows"]
CELLS = json.load(open("data/p2/manifest.json"))["cells"]
PRAC = json.load(open("results/p2_practical_da.json"))["by_source"]
S1 = json.load(open("results/p2_s1_anchor.json"))
LO, HI, X0, X1 = 0.1, 1000.0, -1.25, 4.6
CONDS = (("0.005", "0.0", "noise 0.5 %"), ("0.02", "0.0", "noise 2 %"), ("0.05", "0.0", "noise 5 %"),
         ("0.005", "0.005", "noise 0.5 %, isotherm error 0.5 %"))


def ranges(s, e, key):
    xs = [v[key] for k, v in V.items() if k.startswith(f"sigma={float(s)}|eps={float(e)}|") and v[key]]
    return (min(xs), max(xs), len(xs)) if xs else None


def choice_top(s):
    """Highest Da up to which the LDF law was chosen in every replicate (E6, exact isotherm, Pe ~94)."""
    by = {}
    for key, r in E6.items():
        n, ss, e, _ = key.split("|")
        if float(ss) == float(s) and float(e) == 0.0:
            by.setdefault(CELLS[n]["Da"], []).append(r["success"])
    top = None
    for d in sorted(by):
        if all(by[d]):
            top = d
        else:
            break
    return top


def bar(ax, y, rng, col, h, label=None):
    lo_, hi_, _ = rng
    x = np.log10
    ax.barh(y, x(lo_) - x(LO), left=x(LO), height=h, color=col, alpha=0.45, lw=0)
    ax.barh(y, max(x(hi_) - x(lo_), 0.04), left=x(lo_), height=h, color=col, lw=0, label=label)


def main():
    S.apply()
    fig, ax = plt.subplots(figsize=(S.W2, 88 * S.MM), layout="constrained")
    ax.axvspan(X0, np.log10(LO), color="#f2f2f2", lw=0, zorder=0)
    ax.axvspan(np.log10(HI), X1, color="#f2f2f2", lw=0, zorder=0)
    ax.text(np.log10(HI) + 0.05, 5.0, "beyond the\ntested range", fontsize=6, va="center", color=S.C["dark"])
    yt, yl = [], []
    y = 7.0
    first = True
    for s, e, lab in CONDS:
        d, i = ranges(s, e, "da_disc"), ranges(s, e, "da_ident")
        if i:
            bar(ax, y + 0.18, i, S.ROLE["ident"], 0.3, "rate constant identifiable" if first else None)
            ax.text(np.log10(i[1]) + 0.06, y + 0.18, f"{i[2]}", fontsize=5.5, va="center", color=S.C["dark"])
        c = choice_top(s) if e == "0.0" else None
        if c:
            ax.plot([np.log10(LO), np.log10(c)], [y, y], color=S.OI["black"], lw=1.6, ls="-.",
                    label="law chosen among three candidates (post hoc)" if first else None)
        if d:
            bar(ax, y - 0.18, d, S.ROLE["disc"], 0.3, "law discovered (best method)" if first else None)
            ax.text(np.log10(d[1]) + 0.06, y - 0.18, f"{d[2]}", fontsize=5.5, va="center", color=S.C["dark"])
        yt.append(y)
        yl.append(lab)
        y -= 1.0
        first = False
    y -= 0.4
    ax.text(X0 + 0.05, y + 0.55, "published columns (Supplementary Table 1)", fontsize=6.3, fontweight="bold")
    for src, v in sorted(PRAC.items(), key=lambda kv: kv[1]["Da_low"]):
        ax.plot([np.log10(v["Da_low"]), np.log10(v["Da_high"])], [y, y], color=S.C["dark"], lw=3.0,
                solid_capstyle="butt")
        yt.append(y)
        yl.append(f"{src.replace(' et al.', ' et al.')}, {v['system'].split(' (')[0]}")
        y -= 0.62
    for da, lab, dy in ((S1["Da"], "Langmuir: fails", 0.13), (S1["sips_Da"], "Sips: succeeds", -0.13)):
        ax.plot(np.log10(da), y + dy, marker="D" if "Sips" in lab else "o", ms=4, color=S.C["dark"],
                mfc="white" if "Sips" in lab else S.C["dark"])
    ax.text(np.log10(S1["sips_Da"]) + 0.12, y, "one realisation each, under this study's rule", fontsize=5.8,
            va="center")
    yt.append(y)
    yl.append("Santana et al. 2023 (simulated; filled: Langmuir fails, open: Sips succeeds)")
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=6)
    ax.set_xlim(X0, X1)
    ax.set_ylim(y - 0.6, 7.75)
    ax.set_xticks(range(-1, 5))
    ax.set_xlabel(r"$\log_{10}$ Da (Da = $k\,t_{stoich}$)")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncol=3, fontsize=6, frameon=False)
    return fig


if __name__ == "__main__":
    fig = main()
    for p in S.save(fig, "paper2/fig_p2_guide",
                    inputs=("results/p2_verdicts.json", "results/p2_e6_modelselect.json", "data/p2/manifest.json",
                            "results/p2_practical_da.json", "results/p2_s1_anchor.json")):
        print("wrote", p)
