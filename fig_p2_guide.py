"""Figure 5: what column data allow, by Damkohler number (a summary of results already reported).

Reads only results files: H2b boundaries (results/p2_verdicts.json), the 50 % boundary of the choice among three
laws (post hoc; E8's 200-time run, results/p2_e8_summary.json, whose discovery and identifiability boundaries equal
the H2b ones at Pe ~94), where published columns sit (results/p2_practical_da.json, Supplementary
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
E8 = json.load(open("results/p2_e8_summary.json"))
PRAC = json.load(open("results/p2_practical_da.json"))["by_source"]
S1 = json.load(open("results/p2_s1_anchor.json"))
LO, HI, X0, X1 = 0.1, 1000.0, -1.25, 4.6
CONDS = (("0.005", "0.0", "noise 0.5 %"), ("0.02", "0.0", "noise 2 %"), ("0.05", "0.0", "noise 5 %"),
         ("0.005", "0.005", "noise 0.5 %, isotherm error 0.5 %"))


def ranges(s, e, key):
    xs = [v[key] for k, v in V.items() if k.startswith(f"sigma={float(s)}|eps={float(e)}|") and v[key]]
    return (min(xs), max(xs), len(xs)) if xs else None


def choice_range(s):
    """50 % boundary of the likelihood choice among three laws (logistic crossing on replicates 15-59, the rule of
    the other bars), exact isotherm, Pe ~94, over the two isotherms: E8's 200-time run, the run behind the
    information-matched comparison in the text (results/p2_referee_checks.json). None where it was not run."""
    xs = [E8[f"{iso}|sigma={s}|n_t=200"]["da_select"] for iso in ("langmuir", "step")
          if f"{iso}|sigma={s}|n_t=200" in E8]
    xs = [x for x in xs if x]
    return (min(xs), max(xs), len(xs)) if xs else None


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
            bar(ax, y + 0.2, i, S.ROLE["ident"], 0.26, "rate constant identifiable" if first else None)
            ax.text(np.log10(i[1]) + 0.06, y + 0.2, f"{i[2]}", fontsize=5.5, va="center", color=S.C["dark"])
        c = choice_range(s) if e == "0.0" else None
        if c:                                       # thin to the lowest boundary, heavy over the boundaries
            ax.plot([np.log10(LO), np.log10(c[0])], [y, y], color=S.OI["black"], lw=1.1, ls="-.",
                    label="law chosen among three candidates (post hoc)" if first else None)
            ax.plot([np.log10(c[0]), max(np.log10(c[1]), np.log10(c[0]) + 0.04)], [y, y], color=S.OI["black"],
                    lw=2.2, solid_capstyle="butt")
        if d:
            bar(ax, y - 0.2, d, S.ROLE["disc"], 0.26, "law discovered (best method)" if first else None)
            ax.text(np.log10(d[1]) + 0.06, y - 0.2, f"{d[2]}", fontsize=5.5, va="center", color=S.C["dark"])
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
        yl.append(f"{src}, {v['system'].split(' (')[0]}".replace("CO2", "CO$_2$"))
        y -= 0.62
    for da, lab, dy in ((S1["Da"], "Langmuir: fails", 0.13), (S1["sips_Da"], "Sips: succeeds", -0.13)):
        ax.plot(np.log10(da), y + dy, marker="D" if "Sips" in lab else "o", ms=4, color=S.C["dark"],
                mfc="white" if "Sips" in lab else S.C["dark"])
    ax.text(np.log10(S1["sips_Da"]) + 0.12, y, "one realisation each, under this study's rule", fontsize=5.8,
            va="center")
    yt.append(y)
    yl.append("Santana et al. 2023 (simulated; filled: Langmuir fails, open: Sips succeeds)")
    # the Discussion's three steps at 2 % noise (exact isotherm), edges read from that row's plotted boundaries
    d2, c2, i2 = ranges("0.02", "0.0", "da_disc"), choice_range("0.02"), ranges("0.02", "0.0", "da_ident")
    edges = [LO, d2[1], c2[1], i2[1]]
    assert edges == sorted(edges), edges
    yb = 7.95
    for (a, b), lab, shade in zip(zip(edges[:-1], edges[1:]),
                                  ("discover", "choose a law", "assume it; estimate k"),
                                  ("#d9e6f2", "#e3e3e3", "#f6dfd2")):
        ax.add_patch(plt.Rectangle((np.log10(a), yb - 0.17), np.log10(b) - np.log10(a), 0.34, facecolor=shade,
                                   edgecolor=S.C["dark"], lw=0.5, zorder=2))
        ax.text((np.log10(a) + np.log10(b)) / 2, yb, lab, ha="center", va="center", fontsize=5.6, zorder=3)
    ax.text(np.log10(LO) - 0.05, yb, "at 2 % noise:", ha="right", va="center", fontsize=6)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=6)
    ax.set_xlim(X0, X1)
    ax.set_ylim(y - 0.6, 8.25)
    ax.set_xticks(range(-1, 5))
    ax.set_xlabel(r"$\log_{10}$ Da (Da = $k\,t_{stoich}$)")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncol=3, fontsize=6, frameon=False)
    return fig


if __name__ == "__main__":
    fig = main()
    for p in S.save(fig, "paper2/fig_p2_guide",
                    inputs=("results/p2_verdicts.json", "results/p2_e8_summary.json",
                            "results/p2_practical_da.json", "results/p2_s1_anchor.json")):
        print("wrote", p)
