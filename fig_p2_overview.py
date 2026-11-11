"""Paper 2, Figure 1: the study as a map of the paper (schematic; no result is drawn here).

a, ground truth (with the two isotherms drawn from the study's own isotherm functions) -> design
   grid -> observation models (with a column sketch: probes and outlet) -> the same observations
   go to two questions, discovery of the law and identifiability of k -> the two boundaries and the
   analyses, each tagged confirmatory, exploratory or descriptive, with its Results subsection.
b, what H2b compares, with ILLUSTRATIVE curves (labelled so).

Every text in the canvas is registered with the box it must stay inside, and check() fails if a
text leaves its box or any two texts anywhere in the figure overlap (pattern of pinn-machining
revision_eaai/figures/fig_workflow.py). The facts in the boxes are the design's (PREREG_P2, the
manifest and the generator); none is a result.

    python fig_p2_overview.py      -> paper2/fig_p2_overview.{pdf,png,prov.json}
"""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402

import p2_figstyle as S  # noqa: E402

FS, FS_S, FS_T = 6.0, 5.4, 6.6           # body, small, box title (pt); within Nature's 5-7 pt
EDGE = S.OI["dark"]
TINT = {"truth": "#F2F2F2", "disc": "#E3EEF7", "ident": "#FBE6DA", "out": "#FFFFFF"}
TAG = {"confirmatory": ("confirmatory", EDGE, "white"),
       "exploratory": ("exploratory", "white", "#000000"),
       "descriptive": ("descriptive", "#CFCFCF", "#000000"),
       "post hoc": ("post hoc", "#EFEFEF", "#000000")}


class Canvas:
    """One axes in millimetres over the whole figure; every text is registered with its box."""

    def __init__(self, w_mm, h_mm):
        self.W, self.H = w_mm, h_mm
        self.fig = plt.figure(figsize=(w_mm * S.MM, h_mm * S.MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w_mm)
        self.ax.set_ylim(0, h_mm)
        self.ax.axis("off")
        self.fit = []

    def box(self, x, y, w, h, fc="white", ec=EDGE, lw=0.7, ls="-", r=1.4, z=1):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                         fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
        return (x, y, x + w, y + h)

    def text(self, x, y, s, box=None, fs=FS, ha="left", va="top", **kw):
        kw.setdefault("linespacing", 1.25)
        t = self.ax.text(x, y, s, fontsize=fs, ha=ha, va=va, zorder=5, **kw)
        if box is not None:
            self.fit.append((t, box))
        return t

    def titled(self, x, y, w, h, title, body, fc, n):
        b = self.box(x, y, w, h, fc=fc)
        self.text(x + 1.6, y + h - 1.3, f"{n}  {title}", box=b, fs=FS_T, fontweight="bold")
        self.text(x + 1.6, y + h - 5.2, body, box=b)
        return b

    def inset(self, x, y, w, h):
        """An axes placed in millimetres on the canvas."""
        return self.fig.add_axes([x / self.W, y / self.H, w / self.W, h / self.H])

    def tag(self, x, y, kind, box):
        label, fc, tc = TAG[kind]
        t = self.text(x, y, label, box=box, fs=FS_S, ha="left", va="center", color=tc)
        self.fig.canvas.draw()
        bb = t.get_window_extent(self.fig.canvas.get_renderer()).transformed(self.ax.transData.inverted())
        self.box(bb.x0 - 0.8, y - 1.5, bb.width + 1.6, 3.0, fc=fc, ec=EDGE, lw=0.5, r=0.7, z=4)

    def arrow(self, p0, p1, lw=0.8):
        self.ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=6, lw=lw,
                                          color=EDGE, shrinkA=0, shrinkB=0, zorder=3))

    def line(self, xs, ys, lw=0.8):
        self.ax.plot(xs, ys, color=EDGE, lw=lw, solid_capstyle="butt", zorder=3)

    def check(self, pad=0.3):
        """Registered texts inside their boxes; no two texts anywhere in the figure overlap."""
        self.fig.canvas.draw()
        r = self.fig.canvas.get_renderer()
        inv = self.ax.transData.inverted()
        bad = []
        for t, (x0, y0, x1, y1) in self.fit:
            bb = t.get_window_extent(renderer=r).transformed(inv)
            if bb.x0 < x0 + pad or bb.x1 > x1 - pad or bb.y0 < y0 + pad or bb.y1 > y1 - pad:
                bad.append(f"outside its box: {t.get_text()[:40]!r}")
        texts = [t for t in self.fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
        bbs = [t.get_window_extent(renderer=r) for t in texts]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = bbs[i], bbs[j]
                if a.x0 < b.x1 - 0.5 and b.x0 < a.x1 - 0.5 and a.y0 < b.y1 - 0.5 and b.y0 < a.y1 - 0.5:
                    bad.append(f"overlap: {texts[i].get_text()[:25]!r} / {texts[j].get_text()[:25]!r}")
        assert not bad, "Figure 1 layout:\n" + "\n".join(bad)


def isotherm_inset(ax):
    """The study's two isotherms at the feed temperature, loading over capacity against feed
    concentration over its feed value (from p2_generate.make_physics and isotherm.q_star_np)."""
    from isotherm import q_star_np
    from p2_generate import make_physics
    for iso, ls, lab, xy in (("langmuir", "-", "Langmuir", (0.06, 0.93)), ("step", "--", "step", (0.97, 0.06))):
        p, c_in = make_physics(iso)
        c = np.linspace(0, c_in, 300)
        q = q_star_np(c, np.full_like(c, p.T_in), p) / p.q_max
        ax.plot(c / c_in, q, color=EDGE, lw=0.9, ls=ls)
        ax.text(*xy, lab, fontsize=FS_S, ha="left" if xy[0] < 0.5 else "right",
                va="top" if xy[1] > 0.5 else "bottom")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(r"$c/c_{in}$", fontsize=FS_S, labelpad=0.5)
    ax.set_ylabel(r"q*/$q_{max}$", fontsize=FS_S, labelpad=0.5)


def column_sketch(c, x, y, w, h):
    """Packed column, flow left to right, 20 probes along it and the outlet sensor."""
    c.ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=EDGE, lw=0.7, zorder=4))
    for k in range(20):
        px = x + (k + 0.5) * w / 20
        c.line([px, px], [y + h, y + h + 1.6], lw=0.4)
        c.ax.plot(px, y + h + 1.9, "o", ms=1.4, color=EDGE, zorder=5)
    c.arrow((x - 4.0, y + h / 2), (x, y + h / 2))
    c.arrow((x + w, y + h / 2), (x + w + 4.0, y + h / 2))
    c.ax.plot(x + w + 2.0, y + h / 2, "s", ms=2.6, color=EDGE, zorder=6)


def panel_b(c, x, y, w, h):
    """What H2b compares; illustrative logistic curves, labelled as such."""
    ax = c.inset(x, y, w, h)
    xs = np.linspace(-1, 3, 200)
    ax.plot(xs, 1 / (1 + np.exp(3.2 * (xs - 0.3))), color=S.ROLE["disc"], lw=1.2)
    ax.plot(xs, 1 / (1 + np.exp(4.0 * (xs - 2.0))), color=S.ROLE["ident"], lw=1.2, ls="--")
    ax.axhline(0.5, color=S.ROLE["muted"], lw=0.5)
    for xc, col in ((0.3, S.ROLE["disc"]), (2.0, S.ROLE["ident"])):
        ax.plot([xc, xc], [0, 0.5], color=col, lw=0.6, ls=":")
    ax.annotate("", xy=(2.0, 0.07), xytext=(0.3, 0.07),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=EDGE))
    ax.text(1.15, 0.10, "gap", ha="center", va="bottom", fontsize=FS_S)
    ax.text(-0.95, 0.14, "discovery\nof the law", fontsize=FS_S, va="center", ha="left")
    ax.text(2.3, 0.90, "k\nidentifiable", fontsize=FS_S, va="center", ha="left")
    ax.text(0.22, 0.45, r"Da$^{*}_{disc}$", fontsize=FS_S, ha="right", va="top")
    ax.text(2.08, 0.56, r"Da$^{*}_{ident}$", fontsize=FS_S, ha="left", va="bottom")
    ax.set_xlim(-1, 3)
    ax.set_ylim(0, 1.05)
    ax.set_xticks([-1, 0, 1, 2, 3])
    ax.set_yticks([0, 0.5, 1])
    ax.set_xlabel(r"$\log_{10}$ Da", fontsize=FS, labelpad=1)
    ax.set_ylabel("probability", fontsize=FS, labelpad=1)
    ax.tick_params(labelsize=FS_S, pad=1.5)
    ax.set_title("illustrative curves", fontsize=FS_S, style="italic", loc="right", pad=1.5)
    return ax


def main():
    S.apply()
    W, H = 183.0, 99.0
    c = Canvas(W, H)
    S.letter(c.ax, "a", x=0.6 / W, y=(H - 4.2) / H)
    L, R = 4.0, 179.0

    # tier 1: what was simulated, varied and observed
    y1, h1 = H - 30.0, 25.5
    gt = c.titled(L, y1, 57, h1, "Ground truth", "Verified non-isothermal\ncolumn model\n"
                  "(companion study)\nRate law: LDF (L1) or\nloading-dependent k(q) (L2)", TINT["truth"], "1")
    isotherm_inset(c.inset(L + 37.5, y1 + 3.5, 17.5, 15.5))
    dg = c.titled(67, y1, 50, h1, "Design grid", "Damköhler number Da: 0.1 to 1000,\nnine levels\n"
                  "Péclet number: about 470, 94, 19\nNoise σ and isotherm error ε:\n"
                  "0, 0.5, 2 and 5 % each\n60 replicates (15 select, 45 estimate)", TINT["truth"], "2")
    ob = c.titled(123, y1, R - 123, h1, "Observation models", "O1  probes of c, q, T\n"
                  "O2  probes of c, T (q rebuilt)\nO3  outlet c(t), T(t) only", TINT["truth"], "3")
    column_sketch(c, 131.0, y1 + 5.6, 34.0, 4.0)
    c.text(131.0 + 34.0 + 4.6, y1 + 5.6 + 2.0, "O3", box=ob, fs=FS_S, ha="left", va="center")
    c.text(123 + 1.6, y1 + 1.2, "methods get a measured isotherm", box=ob, fs=FS_S, va="bottom")
    c.arrow((gt[2], y1 + h1 / 2), (dg[0], y1 + h1 / 2))
    c.arrow((dg[2], y1 + h1 / 2), (ob[0], y1 + h1 / 2))

    # the same observations feed both questions
    y2, h2 = 36.5, 24.5
    bus = y1 - 2.6
    xo, xd, xi = 151.0, 47.0, 137.5
    c.line([xo, xo], [y1, bus])
    c.line([xd, xo], [bus, bus])
    c.arrow((xd, bus), (xd, y2 + h2))
    c.arrow((xi, bus), (xi, y2 + h2))
    c.titled(L, y2, 86, h2, "Can the rate law be discovered?",
             "Sparse regression (thresholding, ensemble, exact best\nsubset), weak and strong forms; errors-in-variables\n"
             "(oracle); symbolic regression; neural network in the\ncolumn model (demonstration); slow manifold;\n"
             "implicit regression without an isotherm (isothermal)\n"
             "Success: exactly the true terms, signs, and q* : q = −1 ± 10 %", TINT["disc"], "4")
    c.titled(96, y2, R - 96, h2, "Is the rate constant identifiable?",
             "The true law is given; only k is fitted, on the same\nobservations with the same measured isotherm\n"
             "Profile likelihood of k (O1 exact; O2 and O3 by\nfull column solves)\n"
             "Identifiable: 95 % interval inside [k/2, 2k]", TINT["ident"], "5")

    # tier 3: boundaries and the analyses that use them, each tagged; panel b
    y3, h3 = 3.0, 29.0
    c.arrow((xd, y2), (xd, y3 + h3))
    c.arrow((110.0, y2), (110.0, y3 + h3))
    res = c.box(L, y3, 120, h3, fc=TINT["out"])
    c.text(L + 1.6, y3 + h3 - 1.3, "6  Boundaries and the analyses that use them",
           box=res, fs=FS_T, fontweight="bold")
    rows = [("H2b", "discovery against identifiability boundary, 96 slices", "confirmatory"),
            ("H2a", "does one error ratio place the boundary?", "confirmatory"),
            ("H2c", "does errors-in-variables fitting move it?", "confirmatory"),
            ("", "which methods discover the law, and where", "descriptive"),
            ("", "choice among three candidate laws by likelihood", "post hoc"),
            ("", "O2 and O3: probes without uptake, outlet only", "descriptive"),
            ("H2d", "loading-dependent rate, step isotherm", "exploratory")]
    for i, (h, txt, kind) in enumerate(rows):
        yy = y3 + h3 - 7.0 - i * 3.25
        c.text(L + 1.6, yy, h, box=res, fs=FS, va="center", fontweight="bold")
        c.text(L + 10.5, yy, txt, box=res, fs=FS, va="center")
        c.tag(L + 93.0, yy, kind, res)
    S.letter(c.ax, "b", x=129.0 / W, y=(y3 + h3 - 3.0) / H)
    panel_b(c, 140.0, y3 + 5.5, 38.0, h3 - 9.0)
    c.check()
    return c.fig


if __name__ == "__main__":
    fig = main()
    for p in S.save(fig, "paper2/fig_p2_overview",
                    inputs=("PREREG_P2_discoverability.md", "data/p2/manifest.json",
                            "p2_generate.py", "isotherm.py")):
        print("wrote", p)
