"""Paper 2, Figures 2-4 (display items 2-4 of paper2/ARTICLE_PLAN.md), drawn from results only.

Reads results/p2_verdicts.json (p2_analyze.py: boundaries, intervals, words), the Da levels of
data/p2/manifest.json, and results/p2_figdata.json (p2_figdata.py: the per-level fractions the
verdicts file does not store; see that file's docstring for what it reads). Nothing is
estimated here; the only computation is display binning of R in Fig 3a. Every threshold drawn
is imported from the analysis code (MDE from p2_analyze, the spread thresholds from
p2.analysis.r_collapse), never typed here. No titles inside panels: captions go in LaTeX.

  Fig 2  paper2/fig_p2_map       a, b  P(success) of the best method and P(identifiable) vs
                                       log10 Da, one isotherm each, at DISPLAY_NOISE, Pe x1,
                                       with Da*_disc, Da*_ident and their 95 % intervals
                                 c     Da*_disc against Da*_ident for every O1 slice, intervals,
                                       the +-MDE band, coloured by the H2b words
                                 d     the H2b words and gap for every slice (sigma, eps, iso, Pe)
  Fig 3  paper2/fig_p2_collapse  a     P(success) vs log10 R for every H2a condition
                                 b     R* per condition with its interval, half- and one-decade
                                 c     the spread of log10 R* with its interval vs the thresholds
  Fig 4  paper2/fig_p2_methods   a, b  P(success) by method vs log10 Da at DISPLAY_METHODS_NOISE
                                 c     each method's Da*_disc over the O1 slices
                                 d     the H2c EIV shift per slice with its interval, by eps

    python fig_p2_results.py                     # after p2_analyze.py and p2_figdata.py
    python fig_p2_results.py --out-dir somewhere
"""
import argparse
import inspect
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import figstyle  # noqa: E402
from p2.analysis import H2B_WORDS, r_collapse  # noqa: E402
from p2_analyze import MDE, WITHHELD  # noqa: E402

MM = 1 / 25.4
W1, W2 = 89 * MM, 183 * MM            # Nature single and double column widths
_RC = inspect.signature(r_collapse).parameters
SPREAD_OK, SPREAD_FAIL = _RC["spread_ok"].default, _RC["spread_fail"].default
FACTOR2 = float(np.log10(2.0))        # H2c's predicted factor 2 (p2.analysis.h2c_verdict)

DISPLAY_NOISE = ((0.005, 0.005), (0.02, 0.02), (0.05, 0.05))   # (sigma, eps) in Fig 2a, b
DISPLAY_PE = 1.0
DISPLAY_METHODS_NOISE = (0.02, 0.02)
R_BIN = 0.25                          # display bin of log10 R in Fig 3a (decade)

# Okabe-Ito (colour-blind safe)
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7", "black": "#000000", "grey": "#999999"}
WORD_COLOUR = dict(zip(H2B_WORDS, (OI["verm"], OI["blue"], OI["green"])))
WORD_SHORT = dict(zip(H2B_WORDS, ("fails before", "fails with", "outlives")))
NO_BOUNDARY, WITHHELD_FACE = "#dddddd", "#ffffff"
DISC_SHADES = ("#9ecae1", "#3b7fc4", "#08306b")    # discovery: light to dark = low to high noise
IDENT_SHADES = ("#fdd0a2", "#e6750a", "#7f2704")   # identifiability

METHOD_ORDER = ("stlsq|weak", "stlsq|strong", "ensemble|weak", "ensemble|strong", "best_subset|weak",
                "best_subset|strong", "eiv_best_subset|strong", "m7|strong", "slow_manifold|strong")
METHOD_LABEL = {"stlsq|weak": "M2 weak-form STLSQ", "stlsq|strong": "M2b strong-form STLSQ",
                "ensemble|weak": "M3 ensemble, weak", "ensemble|strong": "M3 ensemble, strong",
                "best_subset|weak": "M4 best subset, weak", "best_subset|strong": "M4 best subset, strong",
                "eiv_best_subset|strong": "M5 EIV best subset (oracle)", "m7|strong": "M7 PySR",
                "slow_manifold|strong": "M9 slow manifold (own target)"}
METHOD_SHORT = {"stlsq|weak": "M2", "stlsq|strong": "M2b", "ensemble|weak": "M3 w",
                "ensemble|strong": "M3 s", "best_subset|weak": "M4 w", "best_subset|strong": "M4 s",
                "eiv_best_subset|strong": "M5", "m7|strong": "M7", "slow_manifold|strong": "M9"}
SOLVER_COLOUR = {"stlsq": OI["blue"], "ensemble": OI["green"], "best_subset": OI["purple"],
                 "eiv_best_subset": OI["black"], "m7": OI["orange"], "slow_manifold": OI["grey"]}
ISO_LABEL = {"langmuir": "Langmuir", "step": "MOF-303-like step"}

# The code labels the dispersion levels by the D_L multiplier; the paper names them by the
# column Peclet number u L / D_L (Supplementary Table 1), so "x0.2" is the HIGHEST Pe.
PE_NUMBER = {0.2: 470, 1.0: 94, 5.0: 19}


def pe_label(pe):
    return f"Pe ≈ {PE_NUMBER[float(pe)]}"


ISO_MARKER = {"langmuir": "o", "step": "s"}
PE_MARKER = {0.2: "v", 1.0: "o", 5.0: "^"}
OBS_COLOUR = {"O1": OI["blue"], "O2": OI["verm"]}

LOG_DA = r"$\log_{10}$ Da (Da = $k\,t_{stoich}$, dimensionless)"
P_LAB = "probability\n(fraction of estimation replicates)"


# ---- small helpers ---------------------------------------------------------------------
def _key(s, e, iso, pe):
    """The H2b slice key exactly as p2_analyze.py line 212 writes it."""
    return f"sigma={float(s)}|eps={float(e)}|{iso}|pe={float(pe)}"


def _parse_slice(k):
    s, e, iso, pe = k.split("|")
    return float(s[6:]), float(e[4:]), iso, float(pe[3:])


def _parse_cond(k):
    obs, iso, pe, m, f = k.split("|")
    return obs, iso, float(pe[3:]), f"{m}|{f}"


def _pct(x):
    return f"{100 * x:g} %"


def _log(v):
    return None if v is None else float(np.log10(float(v)))


def _xerr(est, lo, hi):
    """Asymmetric log10 error bar, or None when the interval is undefined."""
    if est is None or lo is None or hi is None:
        return None
    return [[_log(est) - _log(lo)], [_log(hi) - _log(est)]]


def _frac(levels):
    a = np.asarray(levels, float)
    return np.log10(a[:, 0]), a[:, 1] / np.maximum(a[:, 2], 1)


def _curve(fit, x0, x1):
    x = np.linspace(x0, x1, 200)
    return x, 1.0 / (1.0 + np.exp(-(fit[0] * x + fit[1])))


def _letter(ax, s):
    ax.text(-0.14, 1.02, s, transform=ax.transAxes, fontsize=10, fontweight="bold",
            va="bottom", ha="left")


def _note(ax, text):
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="center", va="center", fontsize=7,
            color=figstyle.C["grey"], wrap=True)


def _save(fig, stem):
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".png", dpi=300)
    plt.close(fig)
    return [stem + ".pdf", stem + ".png"]


def _method_colour(m):
    return SOLVER_COLOUR.get(m.split("|")[0], OI["sky"])


def _method_style(m):
    if m.startswith("eiv_best_subset"):
        return ":"
    return "--" if m.endswith("|strong") and not m.startswith(("m7", "slow_manifold")) else "-"


def _order(methods):
    known = [m for m in METHOD_ORDER if m in methods]
    return known + sorted(m for m in methods if m not in METHOD_ORDER)


def _word_class(v):
    w = v.get("words")
    if w == WITHHELD:
        return "withheld"
    return w if w in H2B_WORDS else "none"


def da_levels_from_manifest(cells):
    """The main-grid Da levels of the L1 discovery cells (refined H2c cells left out)."""
    return sorted({c["Da"] for c in cells.values()
                   if c["law"] == "L1" and c["iso"] != "langmuir_iso" and not c.get("refined")})


def _da_axis(ax, da_levels):
    x = np.log10(da_levels)
    ax.set_xlim(x.min() - 0.25, x.max() + 0.25)
    ax.set_xticks(np.arange(np.floor(x.min()), np.ceil(x.max()) + 1))


# ---- Figure 2: the map -----------------------------------------------------------------
def _h2b_curve_panel(ax, V, FD, iso, pe, noise, da_levels):
    x0, x1 = np.log10(da_levels[0]), np.log10(da_levels[-1])
    have_fd = bool(FD and FD.get("h2b"))
    handles = []
    for i, (s, e) in enumerate(noise):
        k = _key(s, e, iso, pe)
        v = V["H2b"].get(k)
        if v is None:
            continue
        cd, ci = DISC_SHADES[i % 3], IDENT_SHADES[i % 3]
        fd = FD["h2b"].get(k, {}) if have_fd else {}
        if fd.get("disc"):
            x, p = _frac(fd["disc"])
            ax.plot(x, p, "o", color=cd, ms=3.2, zorder=3)
            if fd.get("disc_fit"):
                ax.plot(*_curve(fd["disc_fit"], x0, x1), "-", color=cd, lw=1.3)
            else:
                ax.plot(x, p, "-", color=cd, lw=0.8)
        if fd.get("ident"):
            x, p = _frac(fd["ident"])
            ax.plot(x, p, "s", mfc="white", mec=ci, ms=3.2, zorder=3)
            if fd.get("ident_fit"):
                ax.plot(*_curve(fd["ident_fit"], x0, x1), "--", color=ci, lw=1.3)
            else:
                ax.plot(x, p, "--", color=ci, lw=0.8)
        y = 0.5 + 0.035 * (i - 1)                              # small offset so bars do not overlap
        if v.get("da_disc") is not None:
            ax.errorbar(_log(v["da_disc"]), y, xerr=_xerr(v["da_disc"], *v["da_disc_ci"]), fmt="D",
                        color=cd, ms=4, capsize=2, lw=1, zorder=4)
        if v.get("da_ident") is not None:
            ax.errorbar(_log(v["da_ident"]), y, xerr=_xerr(v["da_ident"], *v["da_ident_ci"]), fmt="D",
                        mfc="white", mec=ci, ecolor=ci, ms=4, capsize=2, lw=1, zorder=4)
        wc = _word_class(v)
        word = WORD_SHORT.get(wc, "withheld" if wc == "withheld" else "no boundary for both")
        handles.append(Line2D([], [], color=figstyle.C["dark"], lw=0, marker="o",
                              mfc=DISC_SHADES[i % 3], mec=IDENT_SHADES[i % 3], mew=1.4, ms=5,
                              label=f"$\\sigma$ = {_pct(s)}, $\\varepsilon$ = {_pct(e)}: {word}"))
    ax.axhline(0.5, color=figstyle.C["grey"], lw=0.6, zorder=1)
    _da_axis(ax, da_levels)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel(LOG_DA)
    ax.set_ylabel(P_LAB)
    kind = [Line2D([], [], color=DISC_SHADES[1], marker="o", ms=3.2, label="discovery, best method"),
            Line2D([], [], color=IDENT_SHADES[1], ls="--", marker="s", mfc="white", ms=3.2,
                   label="$k$ identifiable"),
            Line2D([], [], color=figstyle.C["dark"], lw=0, marker="D", ms=4,
                   label="50 % crossing, 95 % interval")]
    leg = ax.legend(handles=kind, loc="upper right", fontsize=6.3, handlelength=1.8)
    ax.add_artist(leg)
    ax.legend(handles=handles, loc="lower left", fontsize=6.3, handlelength=0.8,
              title=f"{ISO_LABEL.get(iso, iso)}, {pe_label(pe)}", title_fontsize=6.6)
    if not have_fd:
        ax.text(0.02, 0.98, "per-level fractions not available\n(run p2_figdata.py)",
                transform=ax.transAxes, fontsize=6, va="top", color=figstyle.C["grey"])


def _h2b_scatter(ax, V, da_levels):
    lo, hi = np.log10(da_levels[0]) - 0.3, np.log10(da_levels[-1]) + 0.3
    xx = np.array([lo, hi])
    ax.fill_between(xx, xx - MDE, xx + MDE, color="#ececec", lw=0, zorder=0)
    ax.plot(xx, xx, color=figstyle.C["grey"], lw=0.8, zorder=1)
    n_missing = 0
    for k, v in sorted(V["H2b"].items()):
        _, _, iso, _ = _parse_slice(k)
        if v.get("da_disc") is None or v.get("da_ident") is None:
            n_missing += 1
            continue
        wc = _word_class(v)
        col = WORD_COLOUR.get(wc, figstyle.C["grey"])
        face = "white" if wc == "withheld" else col
        ax.errorbar(_log(v["da_ident"]), _log(v["da_disc"]),
                    xerr=_xerr(v["da_ident"], *v["da_ident_ci"]),
                    yerr=_xerr(v["da_disc"], *v["da_disc_ci"]),
                    fmt=ISO_MARKER.get(iso, "o"), mfc=face, mec=col, ecolor=col, ms=3.6,
                    elinewidth=0.6, capsize=0, alpha=0.9, zorder=3)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"$\log_{10} Da^{*}_{ident}$ (dimensionless)")
    ax.set_ylabel(r"$\log_{10} Da^{*}_{disc}$, best method (dimensionless)")
    ax.text(0.97, 0.03, f"{n_missing} of {len(V['H2b'])} slices lack\na boundary for one or both",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.3)
    ax.text(0.03, 0.97, f"band: $\\pm${MDE} decade (MDE)", transform=ax.transAxes, ha="left",
            va="top", fontsize=6.3, color=figstyle.C["dark"])
    isos = sorted({_parse_slice(k)[2] for k in V["H2b"]})
    ax.legend(handles=[Line2D([], [], lw=0, marker=ISO_MARKER.get(i, "o"), mfc="white",
                              mec=figstyle.C["dark"], ms=4, label=ISO_LABEL.get(i, i)) for i in isos],
              loc="lower right", bbox_to_anchor=(1.0, 0.12), fontsize=6.3)


def _h2b_wordmap(ax, V):
    keys = [_parse_slice(k) for k in V["H2b"]]
    rows = sorted({(s, e) for s, e, _, _ in keys})
    cols = sorted({(iso, pe) for _, _, iso, pe in keys})
    for k, v in V["H2b"].items():
        s, e, iso, pe = _parse_slice(k)
        r, c = rows.index((s, e)), cols.index((iso, pe))
        wc = _word_class(v)
        face = WORD_COLOUR.get(wc, WITHHELD_FACE if wc == "withheld" else NO_BOUNDARY)
        ax.add_patch(Rectangle((c, r), 1, 1, facecolor=face, lw=0.8,
                               edgecolor="#777777" if wc == "withheld" else "white",
                               hatch="////" if wc == "withheld" else None))
        g = v.get("gap_decades")
        txt = f"{g:+.2f}" if g is not None else "–"
        ax.text(c + 0.5, r + 0.5, txt, ha="center", va="center", fontsize=5.6,
                color="white" if wc in H2B_WORDS else figstyle.C["dark"])
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(rows), 0)
    ax.set_xticks(np.arange(len(cols)) + 0.5)
    ax.set_xticklabels([f"{ISO_LABEL.get(i, i).replace('MOF-303-like ', '')}\n{pe_label(p)}" for i, p in cols],
                       fontsize=6.3)
    ax.set_yticks(np.arange(len(rows)) + 0.5)
    ax.set_yticklabels([f"{_pct(s)}, {_pct(e)}" for s, e in rows], fontsize=6.0)
    ax.tick_params(length=0)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("isotherm, Péclet multiplier (dimensionless)")
    ax.set_ylabel(r"noise $\sigma$, isotherm error $\varepsilon$ (% of range)")
    patches = [Patch(facecolor=WORD_COLOUR[w], label=f"discovery {WORD_SHORT[w]} identifiability")
               for w in H2B_WORDS]
    patches += [Patch(facecolor=NO_BOUNDARY, label="no boundary for both"),
                Patch(facecolor=WITHHELD_FACE, edgecolor=figstyle.C["dark"], hatch="////",
                      label="withheld (positive control failed)")]
    ov = V.get("H2b_overall", {}).get("words")
    return patches, ("cell numbers: gap $\\log_{10}Da^{*}_{disc} - \\log_{10}Da^{*}_{ident}$ (decade)"
                     + (f";  overall (two-thirds rule): {ov}" if ov else ""))


def fig2(V, FD, da_levels, stem, noise=DISPLAY_NOISE, pe=DISPLAY_PE):
    figstyle.apply()
    fig = plt.figure(figsize=(W2, 175 * MM), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25])
    isos = sorted({_parse_slice(k)[2] for k in V.get("H2b", {})})
    for j, letter in enumerate("ab"):
        ax = fig.add_subplot(gs[0, j])
        if j < len(isos):
            _h2b_curve_panel(ax, V, FD, isos[j], pe, noise, da_levels)
        else:
            _note(ax, "no slice for a second isotherm")
        _letter(ax, letter)
    axc, axd = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    if V.get("H2b"):
        _h2b_scatter(axc, V, da_levels)
        patches, title = _h2b_wordmap(axd, V)
        fig.legend(handles=patches, loc="outside lower center", ncol=3, fontsize=6.5,
                   title=title, title_fontsize=6.5)
    else:
        _note(axc, "no H2b slices")
        _note(axd, "no H2b slices")
    _letter(axc, "c")
    _letter(axd, "d")
    return _save(fig, stem)


# ---- Figure 3: H2a collapse ------------------------------------------------------------
def _cond_label(cond):
    obs, iso, pe, m = _parse_cond(cond)
    return f"{obs}, {ISO_LABEL.get(iso, iso).replace('MOF-303-like ', '')}, {pe_label(pe)}, {METHOD_SHORT.get(m, m)}"


def _cond_style(cond):
    obs, iso, pe, _ = _parse_cond(cond)
    return dict(color=OBS_COLOUR.get(obs, OI["grey"]), ls="-" if iso == "langmuir" else "--",
                marker=PE_MARKER.get(pe, "o"))


def _binned(levels, width=R_BIN):
    a = np.asarray(levels, float)
    lx = np.log10(a[:, 0])
    b = np.floor(lx / width)
    xs, ps = [], []
    for v in np.unique(b):
        m = b == v
        xs.append(np.average(lx[m], weights=a[m, 2]))
        ps.append(a[m, 1].sum() / max(a[m, 2].sum(), 1))
    return np.array(xs), np.array(ps)


def fig3(V, FD, stem):
    figstyle.apply()
    h = V.get("H2a", {})
    fig = plt.figure(figsize=(W2, 80 * MM), layout="constrained")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.42])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))
    rstar = h.get("rstar", {})
    conds = sorted(set(rstar) | set(h.get("no_crossing", [])))
    # a: the curves
    fda = (FD or {}).get("h2a", {})
    if conds and fda:
        for cond in conds:
            d = fda.get(cond)
            if not d or not d.get("levels"):
                continue
            st = _cond_style(cond)
            x, p = _binned(d["levels"])
            a.plot(x, p, lw=0, marker=st["marker"], ms=2.6, color=st["color"], alpha=0.7)
            if d.get("fit"):
                lx = np.log10(np.asarray(d["levels"], float)[:, 0])
                a.plot(*_curve(d["fit"], lx.min(), lx.max()), ls=st["ls"], color=st["color"], lw=1.1)
        a.axhline(0.5, color=figstyle.C["grey"], lw=0.6)
        a.set_ylim(-0.03, 1.03)
    else:
        _note(a, "per-level fractions not available (run p2_figdata.py)" if conds else h.get("words", "no H2a data"))
    a.set_xlabel(r"$\log_{10} R$, $R = \delta/\varepsilon_{eff}$ (dimensionless)")
    a.set_ylabel("P(success), best method\n(fraction of estimation replicates)")
    hd = [Line2D([], [], color=OBS_COLOUR[o], label=o) for o in ("O1", "O2")]
    hd += [Line2D([], [], color=figstyle.C["dark"], ls=ls, label=ISO_LABEL[i])
           for i, ls in (("langmuir", "-"), ("step", "--"))]
    hd += [Line2D([], [], color=figstyle.C["dark"], lw=0, marker=m, ms=3.5, label=f"{pe_label(p)}")
           for p, m in PE_MARKER.items()]
    a.legend(handles=hd, loc="upper left", fontsize=6.0, handlelength=1.6)
    # b: R* per condition
    if rstar:
        order = sorted(rstar, key=lambda k: rstar[k][0])
        lr = [_log(rstar[k][0]) for k in order]
        mn = min(lr)
        b.axvspan(mn, mn + SPREAD_OK, color="#e5f2ec", lw=0, zorder=0)
        b.axvline(mn + SPREAD_FAIL, color=OI["verm"], lw=0.9, ls="--", zorder=1)
        b.text(mn + SPREAD_OK, 1.0, f" {SPREAD_OK:g} decade", transform=b.get_xaxis_transform(),
               fontsize=6, va="bottom", ha="right", color=OI["green"])
        b.text(mn + SPREAD_FAIL, 1.0, f"{SPREAD_FAIL:g} decade", transform=b.get_xaxis_transform(),
               fontsize=6, va="bottom", ha="left", color=OI["verm"])
        for i, k in enumerate(order):
            st = _cond_style(k)
            b.errorbar(lr[i], i, xerr=_xerr(*rstar[k]), fmt=st["marker"], color=st["color"], ms=3.5,
                       capsize=1.5, lw=0.9)
        labels = [_cond_label(k) for k in order]
        nc = h.get("no_crossing", [])
        for j, k in enumerate(nc):
            b.text(mn, len(order) + j, "  no crossing on the grid", va="center", fontsize=6,
                   color=figstyle.C["grey"])
        labels += [_cond_label(k) for k in nc]
        b.set_yticks(range(len(labels)))
        b.set_yticklabels(labels, fontsize=5.8)
        b.set_ylim(len(labels) - 0.5, -0.5)
        b.grid(axis="y", visible=False)
    else:
        _note(b, h.get("words", "no R* on the grid"))
    b.set_xlabel(r"$\log_{10} R^{*}$, 50 % crossing (dimensionless)")
    # c: the spread against the thresholds
    sp, ci = h.get("spread_decades"), h.get("spread_ci") or [None, None]
    top = max(SPREAD_FAIL * 1.5, (ci[1] or 0) * 1.15, (sp or 0) * 1.15)
    c.axhspan(0, SPREAD_OK, color="#e5f2ec", lw=0)
    c.axhspan(SPREAD_OK, SPREAD_FAIL, color="#f4f4f4", lw=0)
    c.axhspan(SPREAD_FAIL, top, color="#fbe7dc", lw=0)
    for y, t in ((SPREAD_OK / 2, "collapses"), ((SPREAD_OK + SPREAD_FAIL) / 2, "inconclusive"),
                 ((SPREAD_FAIL + top) / 2, "does not\ncollapse")):
        c.text(0.97, y, t, transform=c.get_yaxis_transform(), ha="right", va="center", fontsize=6,
               color=figstyle.C["dark"])
    if sp is not None:
        err = None if ci[0] is None else [[sp - ci[0]], [ci[1] - sp]]
        c.errorbar(0.3, sp, yerr=err, fmt="o", color=figstyle.C["dark"], ms=4.5, capsize=2.5)
    else:
        c.text(0.5, 0.5 * top, "no spread\n(< 2 crossings)", ha="center", fontsize=6)
    c.set_xlim(0, 1)
    c.set_ylim(0, top)
    c.set_xticks([])
    c.grid(False)
    c.set_ylabel(r"spread of $\log_{10} R^{*}$ (decade)")
    for ax, letter in zip((a, b, c), "abc"):
        _letter(ax, letter)
    return _save(fig, stem)


# ---- Figure 4: methods and H2c ---------------------------------------------------------
def _methods_panel(ax, FD, iso, s, e, pe, da_levels):
    k = _key(s, e, iso, pe)
    d = ((FD or {}).get("methods") or {}).get(k)
    if not d:
        _note(ax, "per-level fractions not available\n(run p2_figdata.py)")
    else:
        for m in _order(d):
            x, p = _frac(d[m])
            ax.plot(x, p, ls=_method_style(m), color=_method_colour(m), marker="o", ms=2.4,
                    lw=1.6 if m.startswith("eiv") else 1.1, label=METHOD_LABEL.get(m, m))
        ax.text(0.98, 0.98, f"{ISO_LABEL.get(iso, iso)}, {pe_label(pe)}\n$\\sigma$ = {_pct(s)}, "
                f"$\\varepsilon$ = {_pct(e)}", transform=ax.transAxes, ha="right", va="top", fontsize=6.5)
    _da_axis(ax, da_levels)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel(LOG_DA)
    ax.set_ylabel("P(success)\n(fraction of estimation replicates)")


def _by_method_strip(ax, V, da_levels):
    per = {}
    for k, v in V.get("H2b", {}).items():
        for m, d in (v.get("da_disc_by_method") or {}).items():
            per.setdefault(m, []).append((d, _parse_slice(k)[2]))
    if not per:
        _note(ax, "no per-method boundaries")
        return
    ms = _order(per)
    rng = np.random.default_rng(0)                       # display jitter only
    lo = np.log10(da_levels[0]) - 0.3
    for i, m in enumerate(ms):
        vals = [(d, iso) for d, iso in per[m] if d is not None]
        for d, iso in vals:
            ax.plot(i + rng.uniform(-0.22, 0.22), _log(d), ISO_MARKER.get(iso, "o"), ms=2.6,
                    mfc="white" if iso == "step" else _method_colour(m), mec=_method_colour(m),
                    mew=0.7, alpha=0.85)
        if vals:
            ax.plot([i - 0.3, i + 0.3], [np.median([_log(d) for d, _ in vals])] * 2,
                    color=figstyle.C["dark"], lw=1.4)
        ax.text(i, lo + 0.05, f"{len(per[m]) - len(vals)}", ha="center", va="bottom", fontsize=5.8,
                color=figstyle.C["grey"])
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels([METHOD_SHORT.get(m, m) for m in ms], fontsize=6.5)
    ax.set_xlim(-0.6, len(ms) - 0.4)
    ax.set_ylim(lo, np.log10(da_levels[-1]) + 1.0)          # head room for the legend
    ax.set_xlabel("method (grey numbers: O1 slices without a crossing)")
    ax.set_ylabel(r"$\log_{10} Da^{*}_{disc}$ per slice (dimensionless)")
    isos = sorted({iso for v in per.values() for _, iso in v})
    ax.legend(handles=[Line2D([], [], lw=0, marker=ISO_MARKER.get(i, "o"), ms=3.5, mec=figstyle.C["dark"],
                              mfc="white" if i == "step" else figstyle.C["dark"], label=ISO_LABEL.get(i, i))
                       for i in isos] + [Line2D([], [], color=figstyle.C["dark"], lw=1.4, label="median")],
              loc="upper center", fontsize=6.0, ncol=3)


def _h2c_panel(ax, V):
    h = V.get("H2c", {})
    sl = h.get("slices", {})
    if not sl:
        _note(ax, h.get("words", "no H2c slices"))
        return
    eps = sorted({float(k.split("|")[2][4:]) for k in sl})
    keys = sorted(sl)
    sub = sorted({"|".join(k.split("|")[:2]) for k in keys})        # iso|pe
    ax.axhline(0, color=figstyle.C["grey"], lw=0.7)
    ax.axhline(MDE, color=figstyle.C["dark"], lw=0.8, ls="--")
    ax.axhline(FACTOR2, color=OI["verm"], lw=0.8, ls=":")
    tr = ax.get_yaxis_transform()
    ax.text(1.0, MDE, f" MDE {MDE}", transform=tr, fontsize=6, va="top", ha="right")
    ax.text(1.0, FACTOR2, " factor 2", transform=tr, fontsize=6, va="bottom", ha="right", color=OI["verm"])
    n_none = 0
    for k in keys:
        iso, pe, e = k.split("|")
        e, pe_v = float(e[4:]), float(pe[3:])
        v = sl[k]
        j = sub.index(f"{iso}|{pe}")
        x = eps.index(e) + (j - (len(sub) - 1) / 2) * 0.12
        if v.get("shift") is None:
            n_none += 1
            continue
        lo, hi = (v.get("shift_ci") or [None, None])
        err = None if lo is None or hi is None else [[v["shift"] - lo], [hi - v["shift"]]]
        col = OI["blue"] if iso == "langmuir" else OI["orange"]
        ax.errorbar(x, v["shift"], yerr=err, fmt=PE_MARKER.get(pe_v, "o"), color=col, ms=3.5,
                    capsize=1.5, lw=0.9)
    for i, e in enumerate(eps):
        pe_ = (h.get("per_eps") or {}).get(str(e)) or (h.get("per_eps") or {}).get(e) or {}
        if pe_.get("median_shift") is not None:
            ax.plot([i - 0.4, i + 0.4], [pe_["median_shift"]] * 2, color=figstyle.C["dark"], lw=1.6)
    ax.set_xticks(range(len(eps)))
    ax.set_xticklabels([_pct(e) for e in eps])
    ax.set_xlim(-0.6, len(eps) - 0.4)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel(r"isotherm error $\varepsilon$ (% of $q^{*}$), $\sigma$ = 2 %")
    ax.set_ylabel(r"EIV shift, $\Delta\log_{10} Da^{*}_{disc}$" + "\n(M5 minus best non-EIV, decade)")
    hd = [Line2D([], [], lw=0, marker="o", color=OI["blue"], label="Langmuir"),
          Line2D([], [], lw=0, marker="o", color=OI["orange"], label="MOF-303-like step")]
    hd += [Line2D([], [], lw=0, marker=m, color=figstyle.C["dark"], ms=3.5, label=f"{pe_label(p)}")
           for p, m in PE_MARKER.items()]
    hd += [Line2D([], [], color=figstyle.C["dark"], lw=1.6, label="median over slices")]
    if n_none:
        hd += [Line2D([], [], lw=0, label=f"{n_none} slice(s) without a shift")]
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, hi + 0.5 * (hi - lo))                    # head room for the legend
    ax.legend(handles=hd, loc="upper left", fontsize=5.9, ncol=3)


def fig4(V, FD, da_levels, stem, noise=DISPLAY_METHODS_NOISE, pe=DISPLAY_PE):
    figstyle.apply()
    fig = plt.figure(figsize=(W2, 150 * MM), layout="constrained")
    gs = fig.add_gridspec(2, 2)
    isos = sorted({_parse_slice(k)[2] for k in V.get("H2b", {})})
    for j, letter in enumerate("ab"):
        ax = fig.add_subplot(gs[0, j])
        if j < len(isos):
            _methods_panel(ax, FD, isos[j], noise[0], noise[1], pe, da_levels)
        else:
            _note(ax, "no slice for a second isotherm")
        _letter(ax, letter)
        if j == 0:
            h, lab = ax.get_legend_handles_labels()
    if h:
        fig.legend(h, lab, loc="outside upper center", ncol=5, fontsize=6.3, handlelength=2.2)
    axc, axd = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    _by_method_strip(axc, V, da_levels)
    _h2c_panel(axd, V)
    _letter(axc, "c")
    _letter(axd, "d")
    return _save(fig, stem)


def make_all(V, FD, da_levels, out_dir="paper2"):
    return (fig2(V, FD, da_levels, os.path.join(out_dir, "fig_p2_map"))
            + fig3(V, FD, os.path.join(out_dir, "fig_p2_collapse"))
            + fig4(V, FD, da_levels, os.path.join(out_dir, "fig_p2_methods")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", default="results/p2_verdicts.json")
    ap.add_argument("--figdata", default="results/p2_figdata.json")
    ap.add_argument("--manifest", default="data/p2/manifest.json")
    ap.add_argument("--out-dir", default="paper2")
    a = ap.parse_args()
    V = json.load(open(a.verdicts))
    FD = json.load(open(a.figdata)) if os.path.exists(a.figdata) else None
    if FD is None:
        print(f"note: {a.figdata} not found; panels needing per-level fractions say so")
    da = da_levels_from_manifest(json.load(open(a.manifest))["cells"])
    for p in make_all(V, FD, da, a.out_dir):
        print("wrote", p)


if __name__ == "__main__":
    main()
