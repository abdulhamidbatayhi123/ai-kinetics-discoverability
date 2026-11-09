"""Paper 2, Extended Data figures ED1-ED7, drawn from results files only (nothing is estimated).

Conventions (labels, colours, slice keys, the rule that a logistic is drawn only where the
verdict file has a crossing) are imported from fig_p2_results.py so the two scripts agree.
Estimation replicates are rep >= 15 (reps 0-14 select the best method); every success
fraction below that is computed here from row files uses rep >= 15 unless a panel says
otherwise (M8 and M1 were run only at reps 0-2 and rep 0, and their panel says so).

  ED1 paper2/fig_ed1_h2b_langmuir   all 48 Langmuir H2b slices: P(discovery), P(identifiable)
  ED2 paper2/fig_ed2_h2b_step       all 48 step H2b slices
  ED3 paper2/fig_ed3_ident          identifiability estimator accuracy and robustness of H2b
  ED4 paper2/fig_ed4_coverage       E3: identifiable vs interval contains k
  ED5 paper2/fig_ed5_methods        every method against Da, plus M9, M8 and M1
  ED6 paper2/fig_ed6_h2d            H2d (exploratory): best success, loading-dependent rate
  ED7 paper2/fig_ed7_asrun          as-run and intermediate (pre-B90) against corrected verdicts

    python fig_p2_extended.py            # from the repo root; loads one large JSON at a time
"""
import gc
import json
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.ticker  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import p2_figstyle as S  # noqa: E402
from fig_p2_results import (H2B_WORDS, ISO_LABEL, ISO_MARKER, LOG_DA, MDE, METHOD_LABEL, METHOD_SHORT,  # noqa: E402
                            PE_MARKER, WORD_SHORT, _curve, _frac, _key, _method_colour,
                            _method_style, _order, _parse_slice, _pct, da_levels_from_manifest,
                            pe_label)

MM = S.MM
OUT = "paper2"
F_V, F_FD = "results/p2_verdicts.json", "results/p2_figdata.json"
F_ROB, F_COV = "results/p2_ident_robustness.json", "results/p2_e3_coverage.json"
F_ASRUN, F_M1 = "results/p2_verdicts_asrun.json", "results/p2_extra_m1.json"
F_PRE = "results/p2_verdicts_preB90.json"   # after A6 and B89, before B90
F_M9, F_M8, F_MAN = "results/p2_extra_m9.json", "results/p2_e2_m8.json", "data/p2/manifest.json"
EST_REP = 15
PES = (0.2, 1.0, 5.0)
ISOS = ("langmuir", "step")
DARK = S.C["dark"]
GREY = S.C["grey"]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _cell_da(name):
    """'langmuir_L1_pe1_da1e+03' -> 1000.0"""
    return float(name.rsplit("_da", 1)[1])


def _cell_iso(name):
    return name.split("_L")[0]


def _cell_pe(name):
    return float(name.split("_pe")[1].split("_")[0])


def _word_face(v):
    w = v.get("words")
    return S.WORD[w] if w in H2B_WORDS else S.NO_VERDICT


def _da_ticks(ax, da):
    x = np.log10(da)
    ax.set_xlim(x.min() - 0.25, x.max() + 0.25)
    ax.set_xticks(np.arange(np.floor(x.min()), np.ceil(x.max()) + 1))


# ---- ED1 / ED2: all H2b slices ---------------------------------------------------------
def fig_h2b_slices(V, FD, iso, da, stem):
    """Small multiples of P(discovery, best method) and P(identifiable) vs log10 Da for every
    (sigma, eps) row and Pe column of one isotherm, verdict word marked by a coloured square."""
    S.apply()
    rows = sorted({_parse_slice(k)[:2] for k in V["H2b"]})
    fig, axs = plt.subplots(len(rows), len(PES), figsize=(S.W2, 168 * MM), sharex=True, sharey=True,
                            gridspec_kw=dict(left=0.13, right=0.90, top=0.935, bottom=0.115,
                                             hspace=0.28, wspace=0.24))
    x0, x1 = np.log10(da[0]), np.log10(da[-1])
    for r, (s, e) in enumerate(rows):
        for c, pe in enumerate(PES):
            ax = axs[r, c]
            k = _key(s, e, iso, pe)
            v, fd = V["H2b"][k], FD["h2b"][k]
            ax.axhline(0.5, color=GREY, lw=0.4, zorder=1)
            xd, pd_ = _frac(fd["disc"])
            xi, pi = _frac(fd["ident"])
            if fd.get("ident_fit") and v.get("da_ident") is not None:
                ax.plot(*_curve(fd["ident_fit"], x0, x1), "--", color=S.ROLE["ident"], lw=0.8)
            else:
                ax.plot(xi, pi, "--", color=S.ROLE["ident"], lw=0.6)
            ax.plot(xi, pi, "s", mfc="white", mec=S.ROLE["ident"], mew=0.5, ms=2.2, zorder=5)
            if fd.get("disc_fit") and v.get("da_disc") is not None:
                ax.plot(*_curve(fd["disc_fit"], x0, x1), "-", color=S.ROLE["disc"], lw=0.8)
            else:
                ax.plot(xd, pd_, "-", color=S.ROLE["disc"], lw=0.6)
            ax.plot(xd, pd_, "o", color=S.ROLE["disc"], ms=1.7, zorder=4)
            ax.set_ylim(-0.08, 1.08)
            ax.set_yticks([0, 1])
            _da_ticks(ax, da)
            ax.tick_params(labelsize=5, length=1.6, pad=1)
            # verdict square just right of the panel, the gap printed beside it in black
            ax.add_patch(Rectangle((1.025, 0.30), 0.045, 0.40, transform=ax.transAxes,
                                   facecolor=_word_face(v), edgecolor="none", clip_on=False))
            g = v.get("gap_decades")
            if g is not None:
                ax.text(1.085, 0.5, f"{g:+.1f}", transform=ax.transAxes, fontsize=5, va="center",
                        ha="left")
            if r == 0:
                ax.set_title(pe_label(pe), fontsize=6, loc="center", pad=3)
        axs[r, 0].text(-0.20, 0.5, f"σ {_pct(s)}\nε {_pct(e)}", transform=axs[r, 0].transAxes,
                       fontsize=5, ha="right", va="center", linespacing=1.0)
    fig.text(0.5, 0.07, LOG_DA, ha="center", fontsize=6)
    fig.text(0.015, 0.52, "noise σ, isotherm error ε (rows);  P (fraction of estimation replicates, 0 to 1)",
             rotation=90, ha="left", va="center", fontsize=6)
    # No title inside the artwork (Nature style): the isotherm, the curve rule and the meaning of
    # the number beside each square are stated in the Extended Data legend.
    hd = [Line2D([], [], color=S.ROLE["disc"], marker="o", ms=2.5, label="discovery, best method"),
          Line2D([], [], color=S.ROLE["ident"], ls="--", marker="s", mfc="white", ms=2.5,
                 label="k identifiable"),
          Line2D([], [], color=GREY, lw=0.6, label="P = 0.5")]
    hd += [Patch(facecolor=S.WORD[w], label=f"discovery {WORD_SHORT[w]} identifiability")
           for w in H2B_WORDS]
    hd += [Patch(facecolor=S.NO_VERDICT, label="no verdict (no boundary for one of the two)")]
    fig.legend(handles=hd, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=5.5,
               handlelength=1.8, columnspacing=1.2)
    return S.save(fig, stem, inputs=[F_V, F_FD, F_MAN])


# ---- ED3: identifiability estimator and robustness -------------------------------------
def fig_ident(R, V, da, stem):
    """Accuracy of the k estimate with exact data, and how the H2b gaps change without the two
    highest Da levels."""
    S.apply()
    fig = plt.figure(figsize=(S.W2, 78 * MM), layout="constrained")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0])
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    acc = R["accuracy_median_khat_over_k_sigma0_eps0"]
    a.axhspan(0.5, 2.0, color="#f3f3f3", lw=0, zorder=0)
    a.axhspan(0.9, 1.1, color="#d9d9d9", lw=0, zorder=0)
    a.axhline(1.0, color=GREY, lw=0.5, zorder=1)
    for iso, ls in (("langmuir", "-"), ("step", "--")):
        for i, pe in enumerate(PES):
            pts = sorted((_cell_da(n), y) for n, y in acc.items()
                         if _cell_iso(n) == iso and _cell_pe(n) == pe)
            x, y = np.log10([p[0] for p in pts]), [p[1] for p in pts]
            a.plot(x, y, ls=ls, marker=PE_MARKER[pe], color=S.IDENT_SHADES[i], ms=3,
                   mfc="white" if iso == "step" else S.IDENT_SHADES[i], mew=0.8, lw=0.9)
    a.set_yscale("log")
    a.set_ylim(0.25, 8)
    a.set_yticks([0.25, 0.5, 1, 2, 4])
    a.set_yticklabels(["0.25", "0.5", "1", "2", "4"])
    a.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    _da_ticks(a, da)
    a.set_xlabel(LOG_DA)
    a.set_ylabel(r"median $\hat{k}/k$, $\sigma$ = $\varepsilon$ = 0" + "\n(estimation replicates)")
    tr = a.get_yaxis_transform()
    a.text(0.03, 1.55, "criterion band [0.5, 2]", transform=tr, fontsize=5.5, va="center")
    a.text(0.03, 1.12, "band 0.9–1.1", transform=tr, fontsize=5.5, va="bottom")
    hd = [Line2D([], [], color=DARK, ls="-", marker="o", ms=3, label="Langmuir (filled)"),
          Line2D([], [], color=DARK, ls="--", marker="o", mfc="white", ms=3, label="MOF-303-like step (open)"),
          Line2D([], [], lw=0, label=" ")]
    hd += [Line2D([], [], color=S.IDENT_SHADES[i], lw=0, marker=PE_MARKER[pe], ms=3.5, label=pe_label(pe))
           for i, pe in enumerate(PES)]
    a.legend(handles=hd, loc="upper left", ncol=2, fontsize=5.8)
    # b: gaps with and without Da 316, 1000
    w = R["h2b_without_da_316_1000"]
    lo, hi = -4.2, 0.4
    xx = np.array([lo, hi])
    b.plot(xx, xx, color=GREY, lw=0.6, zorder=1)
    b.axhline(-MDE, color=DARK, lw=0.7, ls="--")
    b.axvline(-MDE, color=DARK, lw=0.7, ls="--")
    for k, r in sorted(w.items()):
        _, _, iso, pe = _parse_slice(k)
        g = V["H2b"][k]["gap_decades"]
        b.plot(g, -r["gap_lower_bound_decades"], ISO_MARKER[iso], ms=3.4, color=S.ROLE["ident"],
               mfc="white" if iso == "step" else S.ROLE["ident"], mew=0.8, zorder=3)
    b.set_xlim(lo, hi)
    b.set_ylim(lo, hi)
    b.set_aspect("equal", adjustable="box")
    b.set_xlabel("H2b gap, all Da levels (decade)")
    b.set_ylabel("gap bound without Da 316 and 1000 (decade)\n"
                 r"$\log_{10}Da^{*}_{disc} - \log_{10}$(highest Da $\leq$ 100 with $P_{ident} \geq$ 0.5)")
    b.text(-2.6, -MDE + 0.06, f"−{MDE} decade threshold", fontsize=5.5, ha="left", va="bottom")
    s = R["h2b_without_da_316_1000_summary"]
    b.text(lo + 0.08, lo + 0.08, f"{s['n_slices']} verdict slices;\nmin $P_{{ident}}$ at Da ≤ 31.6: "
           f"{s['min_p_ident_da_le_31.6']:.2f}", fontsize=5.5, va="bottom")
    b.legend(handles=[Line2D([], [], lw=0, marker=ISO_MARKER[i], ms=3.4, color=S.ROLE["ident"],
                             mfc="white" if i == "step" else S.ROLE["ident"], label=ISO_LABEL[i])
                      for i in ISOS] + [Line2D([], [], color=GREY, lw=0.6, label="identity")],
             loc="lower right", bbox_to_anchor=(0.85, 0.0), fontsize=5.8)
    S.letter(a, "a")
    S.letter(b, "b", x=-0.3)
    return S.save(fig, stem, inputs=[F_ROB, F_V])


# ---- ED4: coverage ---------------------------------------------------------------------
def fig_coverage(Cv, stem):
    """E3: how often the profile interval passes the identifiability criterion, against how
    often it contains the true k, per Da on O1 and in total on O1, O2, O3."""
    S.apply()
    fig = plt.figure(figsize=(S.W2, 70 * MM), layout="constrained")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.6, 1.0])
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    pd = Cv["per_model_da"]["O1"]
    das = sorted(pd, key=float)
    x = np.log10([float(d) for d in das])
    fi = [pd[d]["identifiable"] / pd[d]["n"] for d in das]
    fc = [pd[d]["covers"] / pd[d]["n"] for d in das]
    a.plot(x, fi, "-s", color=S.ROLE["ident"], ms=3.2, label="interval passes the criterion (identifiable)")
    a.plot(x, fc, ":o", color=DARK, ms=3.2, mfc="white", label="interval contains the true k")
    a.set_ylim(-0.03, 1.12)
    a.set_xlim(x.min() - 0.25, x.max() + 0.25)
    a.set_xticks(np.arange(-1, 4))
    a.set_xlabel(LOG_DA)
    a.set_ylabel("fraction of O1 rows, all σ, ε, Pe")
    a.legend(loc="upper right", fontsize=5.8, bbox_to_anchor=(1.0, 1.04))
    n = pd[das[0]]["n"]
    a.text(0.02, 0.38, f"n = {n} rows per Da level", transform=a.transAxes, fontsize=5.5)
    # b: totals
    obs = ("O1", "O2", "O3")
    pm = Cv["per_model"]
    w = 0.36
    xi = np.arange(len(obs))
    vi = [pm[o]["identifiable"] / pm[o]["n"] for o in obs]
    vc = [pm[o]["covers"] / pm[o]["n"] for o in obs]
    b.bar(xi - w / 2, vi, w, color=S.ROLE["ident"], label="identifiable")
    b.bar(xi + w / 2, vc, w, color="white", edgecolor=DARK, hatch="/////", lw=0.6, label="contains k")
    for j, o in enumerate(obs):
        b.text(xi[j] - w / 2, vi[j] + 0.02, f"{vi[j]:.2f}", ha="center", fontsize=5.5)
        b.text(xi[j] + w / 2, vc[j] + 0.02, f"{vc[j]:.2f}", ha="center", fontsize=5.5)
    b.set_xticks(xi)
    b.set_xticklabels([f"{o}\nn = {pm[o]['n']}" for o in obs])
    b.tick_params(axis="x", length=0)
    b.set_ylim(0, 1.12)
    b.set_ylabel("fraction of rows")
    b.set_xlabel("observation model")
    b.legend(loc="upper right", fontsize=5.8, ncol=2, bbox_to_anchor=(1.0, 1.04))
    S.letter(a, "a")
    S.letter(b, "b", x=-0.25)
    return S.save(fig, stem, inputs=[F_COV])


# ---- ED5: methods by Da ----------------------------------------------------------------
def _m9_pooled():
    rows = _load(F_M9)["rows"]
    acc = defaultdict(lambda: [0, 0])
    for k, r in rows.items():
        p = k.split("|")
        if int(p[3]) < EST_REP:
            continue
        a = acc[(_cell_iso(p[0]), _cell_da(p[0]))]
        a[0] += bool(r["success"])
        a[1] += 1
    del rows
    gc.collect()
    return dict(acc)


def _rows_by_da(path):
    rows = _load(path)["rows"]
    acc = defaultdict(lambda: [0, 0])
    reps = set()
    for k, r in rows.items():
        p = k.split("|")
        reps.add(int(p[3]))
        a = acc[(_cell_iso(p[0]), _cell_da(p[0]))]
        a[0] += bool(r["success"])
        a[1] += 1
    del rows
    gc.collect()
    return dict(acc), sorted(reps)


def fig_methods(FD, m9, m8, m8reps, m1, da, stem):
    """Success of every method vs Da at sigma 2 %, Pe ~94, eps 0 and 2 %, both isotherms; M9
    pooled against its own target; M8 and M1 on their declared subgrids."""
    S.apply()
    fig = plt.figure(figsize=(S.W2, 165 * MM), layout="constrained")
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.9])
    hs = None
    for r, e in enumerate((0.0, 0.02)):
        for c, iso in enumerate(ISOS):
            ax = fig.add_subplot(gs[r, c])
            d = FD["methods"][_key(0.02, e, iso, 1.0)]
            for m in _order(d):
                x, p = _frac(d[m])
                ax.plot(x, p, ls=_method_style(m), color=_method_colour(m), marker="o", ms=2.2,
                        lw=1.5 if m.startswith("eiv") else 1.0, label=METHOD_LABEL.get(m, m))
            ax.text(0.98, 0.97, f"{ISO_LABEL[iso]}, {pe_label(1.0)}\nσ = 2 %, ε = {_pct(e)}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=6)
            zero = [METHOD_SHORT.get(m, m) for m in _order(d) if not any(n for _, n, _ in d[m])]
            if zero:
                ax.text(0.98, 0.80, "no success at any Da\n(lines overlap at 0):\n" + ", ".join(zero),
                        transform=ax.transAxes, ha="right", va="top", fontsize=5.5)
            ax.set_ylim(-0.03, 1.03)
            _da_ticks(ax, da)
            ax.set_xlabel(LOG_DA)
            ax.set_ylabel("P(success)")
            S.letter(ax, "abcd"[2 * r + c])
            if hs is None:
                hs = ax.get_legend_handles_labels()
    fig.legend(*hs, loc="outside upper center", ncol=5, fontsize=5.8, handlelength=2.2)
    # e: M9 pooled
    ax = fig.add_subplot(gs[2, 0])
    for iso in ISOS:
        pts = sorted((d_, v) for (i, d_), v in m9.items() if i == iso)
        x = np.log10([p[0] for p in pts])
        y = [p[1][0] / p[1][1] for p in pts]
        ax.plot(x, y, "-" if iso == "langmuir" else "--", marker=ISO_MARKER[iso], color=S.SOLVER["slow_manifold"],
                mfc="white" if iso == "step" else S.SOLVER["slow_manifold"], ms=3, label=ISO_LABEL[iso])
    n9 = sorted({v[1] for v in m9.values()})
    ax.set_ylim(-0.03, 1.03)
    _da_ticks(ax, da)
    ax.set_xlabel(LOG_DA)
    ax.set_ylabel("P(success), M9\nagainst its own target")
    ax.text(0.02, 0.62, f"pooled over σ, ε, Pe;\nn = {n9[0]} estimation replicates\nper point",
            transform=ax.transAxes, fontsize=5.5, va="top")
    ax.legend(loc="upper left", fontsize=5.8)
    S.letter(ax, "e")
    # f: M8 and M1
    ax = fig.add_subplot(gs[2, 1])
    for iso in ISOS:
        pts = sorted((d_, v) for (i, d_), v in m8.items() if i == iso)
        x = np.log10([p[0] for p in pts])
        ax.plot(x, [p[1][0] / p[1][1] for p in pts], ls="-" if iso == "langmuir" else "--",
                marker=ISO_MARKER[iso], color=DARK, mfc="white" if iso == "step" else DARK, ms=3,
                lw=0.8, label=f"M8, {ISO_LABEL[iso]}")
    pts = sorted(m1.items())
    ax.plot(np.log10([p[0] for p in pts]), [p[1] for p in pts], lw=0, marker="D", ms=3.4,
            mfc="white", mec=DARK, mew=0.8, label="M1 UDE, Langmuir (O3, 1 replicate)")
    n8 = sorted({v[1] for v in m8.values()})
    ax.set_ylim(-0.08, 1.12)
    _da_ticks(ax, da)
    ax.set_xlabel(LOG_DA)
    ax.set_ylabel("success\n(fraction or 0/1)")
    ax.text(0.98, 0.40, f"M8: {sum(v[0] for v in m8.values())} successes in "
            f"{sum(v[1] for v in m8.values())} rows;\nn = {n8[0]} per point (σ 0.5, 2 %; ε 0, 2 %;\n"
            f"reps {m8reps[0]}–{m8reps[-1]}), {pe_label(1.0)}\nM1: σ 2 %, ε 0, rep 0, {pe_label(1.0)}",
            transform=ax.transAxes, fontsize=5.5, ha="right", va="center")
    ax.legend(loc="upper right", fontsize=5.8)
    S.letter(ax, "f")
    return S.save(fig, stem, inputs=[F_FD, F_M9, F_M8, F_M1, F_MAN])


# ---- ED6: H2d heatmap ------------------------------------------------------------------
def fig_h2d(V, stem):
    """H2d (exploratory): the best success fraction over methods and Pe for the loading-
    dependent rate law L2 (step isotherm), per (sigma, eps) and Da."""
    S.apply()
    h = V["H2d_descriptive"]
    best = defaultdict(float)
    for k, v in h.items():
        cell, s, e, _, _ = k.split("|")
        if v is not None:
            key = (float(s), float(e), _cell_da(cell))
            best[key] = max(best[key], v)
    rows = sorted({(s, e) for s, e, _ in best})
    das = sorted({d for _, _, d in best})
    M = np.array([[best[(s, e, d)] for d in das] for s, e in rows])
    fig, ax = plt.subplots(figsize=(S.W2 * 0.62, 105 * MM), layout="constrained")
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=5,
                    color="#000000" if M[i, j] > 0.55 else "#ffffff")
    ax.set_xticks(range(len(das)))
    ax.set_xticklabels([f"{np.log10(d):.1f}" for d in das])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"σ {_pct(s)}, ε {_pct(e)}" for s, e in rows], fontsize=5.5)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel(LOG_DA)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("best P(success) over the 6 sparse-regression\nmethods and the 3 Pe "
                 "(all replicates in the file)", fontsize=6)
    cb.ax.tick_params(labelsize=5.5)
    cb.outline.set_linewidth(0.5)
    return S.save(fig, stem, inputs=[F_V])


# ---- ED7: as-run against corrected -----------------------------------------------------
def _classes(H):
    out = {"fails before": 0, "fails with": 0, "outlives": 0, "withheld": 0, "no boundary": 0}
    for v in H.values():
        w = v.get("words") or ""
        if w in H2B_WORDS:
            out[WORD_SHORT[w]] += 1
        elif w.startswith("withheld"):
            out["withheld"] += 1
        else:
            out["no boundary"] += 1
    return out


def fig_asrun(A, V, stem, P=None):
    """Positive control, verdict counts and per-slice gaps of the first (as-run) analysis and the
    intermediate one (after A6 and B89, before B90; P) against the corrected one."""
    S.apply()
    fig = plt.figure(figsize=(S.W2, 70 * MM), layout="constrained")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 0.9, 1.0])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))
    # a: positive control
    ticks, w = [], 0.2
    for j, iso in enumerate(ISOS):
        for q, (src, name) in enumerate(((A, "as run"), (V, "corrected"))):
            pc = src["positive_control"][iso]
            x = j + (q - 0.5) * 2 * w
            a.bar(x - w / 2, pc["success_fraction"], w, color=S.ROLE["disc"],
                  hatch=None if q else "////", edgecolor="white" if q else "#ffffff", lw=0)
            a.bar(x + w / 2, pc["identifiable_fraction"], w, color=S.ROLE["ident"],
                  hatch=None if q else "////", edgecolor="white", lw=0)
            ticks.append((x, name))
            if pc["identifiable_fraction"] == 0:
                a.text(x + w / 2, 0.01, "0", ha="center", va="bottom", fontsize=5.5)
            a.text(x, 1.02, "pass" if pc["passed"] else "fail", ha="center", va="bottom", fontsize=5.5)
    a.axhline(A["positive_control"]["langmuir"]["need"], color=DARK, lw=0.7, ls="--")
    a.set_xticks([t[0] for t in ticks])
    a.set_xticklabels([t[1] for t in ticks], fontsize=5.5)
    a.tick_params(axis="x", length=0)
    for j, iso in enumerate(ISOS):
        a.text(j, -0.12, ISO_LABEL[iso], ha="center", va="top", fontsize=6, transform=a.get_xaxis_transform())
    a.set_ylim(0, 1.18)
    a.set_yticks([0, 0.5, 0.9, 1.0])
    a.set_ylabel("positive-control fraction (σ = ε = 0)")
    a.legend(handles=[Patch(facecolor=S.ROLE["disc"], label="discovery"),
                      Patch(facecolor=S.ROLE["ident"], label="identifiable"),
                      Patch(facecolor="#bbbbbb", hatch="////", edgecolor="white", label="as run"),
                      Line2D([], [], color=DARK, ls="--", lw=0.7, label="need 0.9")],
             loc="upper center", ncol=4, fontsize=5.5, bbox_to_anchor=(0.5, 1.2), handlelength=1.4,
             columnspacing=0.8)
    # b: verdict counts, stacked
    runs = [("as run", A)] + ([("A6, B89", P)] if P else []) + [("corrected", V)]
    face = {"fails before": S.WORD[H2B_WORDS[0]], "fails with": S.WORD[H2B_WORDS[1]],
            "outlives": S.WORD[H2B_WORDS[2]], "withheld": "#ffffff", "no boundary": S.NO_VERDICT}
    for j, (_, src) in enumerate(runs):
        cl, bottom = _classes(src["H2b"]), 0
        for name, n in cl.items():
            if not n:
                continue
            b.bar(j, n, 0.6, bottom=bottom, color=face[name], edgecolor=DARK if name == "withheld" else "white",
                  hatch="////" if name == "withheld" else None, lw=0.5)
            b.text(j, bottom + n / 2, f"{n}", ha="center", va="center", fontsize=6,
                   color="#ffffff" if name == "fails before" else "#000000",
                   bbox=dict(facecolor="white", edgecolor="none", pad=0.6) if name == "withheld" else None)
            bottom += n
    b.set_xticks(range(len(runs)))
    b.set_xticklabels([r[0] for r in runs], fontsize=5.5)
    b.tick_params(axis="x", length=0)
    b.set_xlim(-0.6, len(runs) - 0.4)
    b.set_ylim(0, 96)
    b.set_yticks([0, 24, 48, 72, 96])
    b.set_ylabel("O1 H2b slices")
    b.legend(handles=[Patch(facecolor=face["fails before"], label="discovery fails before ident."),
                      Patch(facecolor="#ffffff", edgecolor=DARK, hatch="////", label="withheld (control failed)"),
                      Patch(facecolor=face["no boundary"], label="no boundary for one of the two")],
             loc="upper center", bbox_to_anchor=(0.5, 1.2), fontsize=5.5, ncol=1, handlelength=1.4)
    # c: gaps
    lo, hi = -4.2, 0.4
    c.plot([lo, hi], [lo, hi], color=GREY, lw=0.6)
    c.axhline(-MDE, color=DARK, lw=0.6, ls="--")
    c.axvline(-MDE, color=DARK, lw=0.6, ls="--")
    nd, nnew = 0, 0
    earlier = [(A, "as run", 0.35)] + ([(P, "after A6, B89", 1.0)] if P else [])
    for k in sorted(V["H2b"]):
        gv = V["H2b"][k].get("gap_decades")
        if gv is None:
            continue
        iso = _parse_slice(k)[2]
        def gap(src):   # a withheld slice (failed positive control) has no verdict, so no gap is shown
            s = src["H2b"].get(k, {})
            return None if (s.get("words") or "").startswith("withheld") else s.get("gap_decades")
        if all(gap(src) is None for src, _, _ in earlier):
            nnew += 1
        for src, _, alpha in earlier:
            ga = gap(src)
            if ga is None:
                continue
            if src is earlier[-1][0]:
                nd += abs(ga - gv) > 1e-9
            c.plot(ga, gv, ISO_MARKER[iso], ms=3.4, color=S.WORD[H2B_WORDS[0]] if alpha == 1.0 else GREY,
                   mfc="white" if iso == "step" else (S.WORD[H2B_WORDS[0]] if alpha == 1.0 else GREY), mew=0.8)
    c.set_xlim(lo, hi)
    c.set_ylim(lo, hi)
    c.set_xlabel("gap in the earlier run (decade)")
    c.set_ylabel("gap corrected (decade)")
    n_prev = sum(v.get("gap_decades") is not None for v in earlier[-1][0]["H2b"].values())
    c.text(lo + 0.1, hi - 0.15, f"{nd} of {n_prev} earlier gaps changed;\n"
           f"{nnew} slices have a gap only when corrected", fontsize=5.5, va="top")
    c.legend(handles=[Line2D([], [], lw=0, marker="o", ms=3.4, color=S.WORD[H2B_WORDS[0]], label=f"vs {earlier[-1][1]}"),
                      Line2D([], [], lw=0, marker="o", ms=3.4, color=GREY, label="vs as run (Langmuir only)"),
                      Line2D([], [], lw=0, marker="s", ms=3.4, mfc="white", color=DARK, label="step isotherm"),
                      Line2D([], [], color=GREY, lw=0.6, label="identity")],
             loc="lower right", fontsize=5.5)
    for ax, s_ in zip((a, b, c), "abc"):
        S.letter(ax, s_, y=1.12)
    return S.save(fig, stem, inputs=[F_ASRUN, F_V] + ([F_PRE] if P else []))


def main():
    out = []
    da = da_levels_from_manifest(_load(F_MAN)["cells"])
    V = _load(F_V)
    FD = _load(F_FD)
    out += fig_h2b_slices(V, FD, "langmuir", da, os.path.join(OUT, "fig_ed1_h2b_langmuir"))
    out += fig_h2b_slices(V, FD, "step", da, os.path.join(OUT, "fig_ed2_h2b_step"))
    R = _load(F_ROB)
    out += fig_ident(R, V, da, os.path.join(OUT, "fig_ed3_ident"))
    del R
    out += fig_coverage(_load(F_COV), os.path.join(OUT, "fig_ed4_coverage"))
    out += fig_h2d(V, os.path.join(OUT, "fig_ed6_h2d"))
    # ED5: the row files are loaded one at a time and released; figdata is kept (0.5 MB)
    vslim = {"H2b": V["H2b"], "positive_control": V["positive_control"]}
    del V
    gc.collect()
    m9 = _m9_pooled()
    m8, m8reps = _rows_by_da(F_M8)
    m1 = {_cell_da(k.split("|")[0]): float(r["success"]) for k, r in _load(F_M1)["rows"].items()}
    out += fig_methods(FD, m9, m8, m8reps, m1, da, os.path.join(OUT, "fig_ed5_methods"))
    del FD
    gc.collect()
    out += fig_asrun(_load(F_ASRUN), vslim, os.path.join(OUT, "fig_ed7_asrun"), P=_load(F_PRE))
    for p in out:
        print("wrote", p)


if __name__ == "__main__":
    main()
