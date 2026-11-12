"""Build and check Paper 2 (article + Supplementary Information). Exits 1 on any failure.

Gates (pattern of pinn-machining revision_eaai/build/gates.py; rules from PRESENTATION_PLAN.md):
  G1  the bibliography is regenerated from bib_p2.tex (make_article_bib.py) and nothing is missing
  G2  article.tex and supplementary_main.tex compile with no error and no undefined reference,
      and no line or table runs more than 2 pt past the margin (overfull boxes, read from the logs)
  G3  key numbers in the text are recomputed from the results files and must appear verbatim
  G4  abstract <= 150 words; main text (Introduction + Results + Discussion) <= 3,500 words
  G5  <= 6 display items (figures + tables) in the main text
  G6  em dashes <= 5 in the article
  G7  no banned phrase (paper2/terminology.md) in the article or the SI
  G8  no unresolved placeholder (PENDING, VERIFY, [CHECK, TODO) outside comments
  G9  every Extended Data figure that exists is cited in the article
  G10 every figure file the article includes exists and has a provenance file

    python paper2/build_p2.py            # all gates
"""
import json
import math
import statistics
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BS = chr(92)
TECTONIC = os.environ.get("TECTONIC", r"C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\tools\tectonic.exe")
FAIL = []


def fail(gate, msg):
    FAIL.append(f"{gate}: {msg}")


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def strip_comments(tex):
    return "\n".join(re.sub(r"(?<!" + re.escape(BS) + r")%.*", "", ln) for ln in tex.splitlines())


def norm(s):
    return re.sub(r"\s+", " ", s)


def rendered_words(t):
    """Words a reader sees: citations removed, each inline math expression one word, LaTeX command
    names dropped (their braced text kept), '~' a space, '\\,' and braces removed."""
    t = re.sub(re.escape(BS) + r"cite[pt]?\{[^}]*\}", "", t)
    t = re.sub(r"\$[^$]*\$", " X ", t)
    t = re.sub(re.escape(BS) + r"(sub)*section\*?", " ", t)
    t = re.sub(re.escape(BS) + r"[A-Za-z]+\*?", " ", t)
    t = t.replace(BS + ",", "").replace("~", " ").replace("{", " ").replace("}", " ")
    t = re.sub(re.escape(BS) + r"[^A-Za-z\s]", "", t)
    return len([w for w in t.split() if re.search(r"[A-Za-z0-9]", w)])


def words_between(tex, a, b):
    t = tex[tex.index(a):tex.index(b)]
    t = re.sub(re.escape(BS) + r"cite[pt]?\{[^}]*\}", "", t)
    return len(t.split())


# ---- G3: bindings. Each returns (description, literal expected in the comment-free text). ----
def bindings():
    V = load("results/p2_verdicts.json")
    h2b = V["H2b"]
    gaps = {k: s["gap_decades"] for k, s in h2b.items() if s["gap_decades"] is not None}
    lang = sorted(-g for k, g in gaps.items() if "langmuir" in k)
    step = sorted(-g for k, g in gaps.items() if "step" in k)
    med = lambda xs: (xs[len(xs) // 2] + xs[(len(xs) - 1) // 2]) / 2
    lo, hi = min(-g for g in gaps.values()), max(-g for g in gaps.values())
    pc = V["positive_control"]
    # Review P2: a zero-width bootstrap interval on Da*_ident means perfect separation (interval-censored
    # between two grid levels, Methods). Conservative gap: that boundary placed at the lower level.
    levels = [10 ** (i / 2) for i in range(-2, 7)]
    cons, n_cens = [], 0
    for k, s in h2b.items():
        if s["gap_decades"] is None:
            continue
        a, b = s["da_ident_ci"]
        if a == b:
            n_cens += 1
            low = max(x for x in levels if x < s["da_ident"] * (1 - 1e-9))
            cons.append(math.log10(low) - math.log10(s["da_disc"]))
        else:
            cons.append(-s["gap_decades"])
    cons_min = math.floor(min(cons) * 100) / 100
    out = [("H2b slices with a verdict", f"Of the {len(h2b)} slices, {len(gaps)} had both"),
           ("H2b slices without a verdict", f"The {len(h2b) - len(gaps)} slices without a verdict"),
           ("H2b slices with a verdict (abstract)", f"tested range ({len(gaps)} conditions)"),
           ("H2b slices with a verdict (Fig. 3 legend)", f"for the {len(gaps)} slices with both boundaries"),
           ("H2b gap range (Results)", f"The gap was {lo:.1f} to {hi:.1f} decades of"),
           ("H2b gap range (abstract)", f"by {lo:.1f} to {hi:.1f} decades"),
           ("H2b median gap, Langmuir", f"median of {med(lang):.1f} decades for the"),
           ("H2b median gap, step", f"{med(step):.1f} for the step"),
           ("H2b censored identifiability boundaries", f"identifiability boundary in {n_cens} of the {len(gaps)} slices"),
           ("H2b censoring-aware smallest gap (Results)", f"every gap is at least {cons_min:.2f} decades (Methods)"),
           ("H2b censoring-aware smallest gap (Methods)", f"every gap is still at least {cons_min:.2f}"),
           ("positive control (both isotherms pass, all replicates)",
            f"in {pc['langmuir']['n_success']} of {pc['langmuir']['n_success']} replicates"
            if all(pc[i]["passed"] and pc[i]["success_fraction"] == 1.0 and pc[i]["identifiable_fraction"] == 1.0
                   for i in ("langmuir", "step")) else "positive control not 100 %")]
    rs = V["H2a"]["rstar"]
    if len(rs) == 1:
        est, l, u = next(iter(rs.values()))
        out += [("H2a R*", f"R^{{*}} = {est:.0f}"), ("H2a R* interval", f"{l:.0f} to {u:.0f}")]
    o23 = V["H2b_O2_O3_descriptive"].values()
    o2 = [v["O2_da_ident"] for v in o23 if v["O2_da_ident"]]
    o3 = [v["O3_da_ident"] for v in o23 if v["O3_da_ident"]]
    out += [("O2 identifiability range", f"{min(o2):.0f}$ to {max(o2):.0f}"),
            ("O3 identifiability range", f"{min(o3):.0f}$ to {max(o3):.0f}")]
    cross = {}
    for s in h2b.values():
        for m, d in s["da_disc_by_method"].items():
            cross[m] = cross.get(m, 0) + (d is not None)
    out += [("crossings M4 weak / M2 weak", f"in {cross['best_subset|weak']} of the {len(h2b)} slices, "
             f"against {cross['stlsq|weak']}"),
            ("crossings M3 weak", f"and {cross['ensemble|weak']} for")]
    rob = load("results/p2_ident_robustness.json")
    summ = rob["h2b_without_da_316_1000_summary"]
    acc = [v for k, v in rob["accuracy_median_khat_over_k_sigma0_eps0"].items()
           if v is not None and float(k.split("_da")[1]) <= 100]
    out += [("estimator accuracy up to Da 100",
             f"within {int(-(-max(abs(a - 1) for a in acc) * 100 // 1))}{BS},{BS}% at every"),
            ("gap lower bound", f"gap of at least {math.floor(summ['min_gap_lower_bound_decades'] * 100) / 100:.2f} decade")]
    cls = rob["h2b_no_verdict_classes"]
    miss = sum(n for k, n in cls.items() if k.startswith("discovery missing"))
    never = sum(n for k, n in cls.items() if "discovery missing, always < 50" in k)
    always = sum(n for k, n in cls.items() if "discovery missing, always >= 50" in k)
    strad = sum(n for k, n in cls.items() if "discovery missing, straddles" in k)
    only_id = sum(n for k, n in cls.items() if k.startswith("discovery present"))
    out += [("no-verdict: discovery missing", f"The {miss} slices without a verdict lack a discovery boundary"
             if only_id == 0 else f"missing in {miss}"),
            ("never 50 %", f"in {never}, discovery"), ("never below 50 %", f"in {always}, all"),
            ("straddles", f"in the other {strad} the observed")]
    if only_id:
        out += [("only identifiability missing", f"remaining {only_id} slices")]
    m1 = load("results/p2_extra_m1.json")["rows"]
    n_ok = sum(bool(v.get("success")) for v in m1.values())
    names = {1: "one", 2: "two", 3: "three"}
    out += [("M1 successes", f"{names.get(n_ok, n_ok)} of its nine fits" if len(m1) == 9 else "M1 rows != 9")]
    m8 = load("results/p2_e2_m8.json")["rows"]
    out += [("M8 (E2)", f"none of {len(m8)} fits" if not any(v.get("success") for v in m8.values())
             else "M8 has successes")]
    meth = load("results/p2_figdata.json")["methods"]
    m7gaps = []
    for k, s in h2b.items():
        if s["gap_decades"] is None or "m7|strong" not in meth.get(k, {}):
            continue
        last = max([da for da, a, n in meth[k]["m7|strong"] if a / n >= 0.5], default=None)
        if last:
            m7gaps.append(__import__("math").log10(s["da_ident"] / last))
    if m7gaps:
        m7lo, m7hi = math.floor(min(m7gaps) * 10) / 10, math.ceil(max(m7gaps) * 10) / 10   # a range of lower bounds
        out += [("M7 last level vs Da*_ident", f"that level lay {m7lo:.1f} to {m7hi:.1f}"),
                ("Table 1 envelope: M7 range", f"{m7lo:.1f} to {m7hi:.1f} decades below"),
                ("Table 1 envelope: M7 slices", f"symbolic regression ({ {4: 'four', 3: 'three', 5: 'five'}.get(len(m7gaps), len(m7gaps))} slices")]
    # Review P4: the selected method equals each slice's best monotone method on the estimation replicates
    env_same = all(s["da_disc"] is not None and abs(math.log10(max(x for x in s["da_disc_by_method"].values() if x)
                                                                  / s["da_disc"])) < 1e-9
                   for s in h2b.values() if s["gap_decades"] is not None)
    out += [("Table 1 envelope equals selection", f"gives the same {len(gaps)} gaps" if env_same else "envelope differs")]
    extra = sorted(math.log10(max(x for x in s["da_disc_by_method"].values() if x) / s["da_ident"])
                   for s in h2b.values() if s["gap_decades"] is None and s["da_ident"]
                   and any(s["da_disc_by_method"].values()))
    out += [("Table 1 envelope: two more gaps", f"and two more ($" + BS + "sigma =" if len(extra) == 2 else "extra gaps != 2"),
            ("Table 1 envelope: their values", f"${extra[1]:.2f}$ and ${extra[0]:.2f}$".replace("-", "-")
             if len(extra) == 2 else "extra gaps != 2")]
    e6 = load("results/p2_e6_modelselect.json")["rows"]
    cells = load("data/p2/manifest.json")["cells"]
    e6c = {}   # per condition (isotherm, sigma, eps, Da)
    for key, r in e6.items():
        n, s, e, _ = key.split("|")
        e6c.setdefault((cells[n]["iso"], float(s), float(e), cells[n]["Da"]), []).append(r["success"])
    lo10 = [x for (i, s, e, d), v in e6c.items() if e == 0 and d <= 10 for x in v]
    lo10e = min(sum(v) / len(v) for (i, s, e, d), v in e6c.items() if e > 0 and d <= 10)
    d31 = [x for (i, s, e, d), v in e6c.items() if e == 0 and 30 < d < 32 for x in v]
    hi = [x for (i, s, e, d), v in e6c.items() if e == 0 and d >= 100 for x in v]
    out += [("E6 all LDF at Da <= 10, exact isotherm", "chosen in all 45 replicates at every" if all(lo10) else "E6 not all"),
            ("E6 min with isotherm error", f"at least {round(lo10e * 45)} of 45 with 2"),
            ("E6 Da 31.6", f"in only {sum(d31)} of {len(d31)} replicates at"),
            ("E6 none from Da 100", "in none from" if not any(hi) else "E6 some at Da >= 100")]
    e4 = load("results/p2_e4_criteria.json")["variants"]
    alt = [v for k, v in e4.items() if k != "pre"]
    e4_ok = all(v["overall"] == "discovery fails before identifiability" and all(p for p in v["positive_control"].values())
                and set(v["word_counts"]) <= {"discovery fails before identifiability",
                                               "no boundary on the grid for one of the two; reported as the range tested"}
                for v in alt)
    out += [("E4 every verdict kept", "the point estimate alone kept every verdict" if e4_ok else "E4 verdict differs"),
            ("E4 gap range", f"with gaps of {math.floor(min(-v['gap_max'] for v in alt) * 100) / 100:.2f} to "
             f"{max(-v['gap_min'] for v in alt):.2f} decades")]
    # review round 2 (m2, m4, referee 6): bounds rounded outwards; the borderline verdict slice; boundaries near
    # the bottom of the grid
    h2b_all = load("results/p2_verdicts.json")["H2b"]
    d55 = [s["da_disc"] for k, s in h2b_all.items() if k.startswith("sigma=0.005|eps=0.005|") and s["gap_decades"] is not None]
    near = [s["gap_decades"] for s in h2b_all.values()
            if s["gap_decades"] is not None and math.log10(s["da_disc"] / 0.1) <= 0.25]
    out.append(("boundaries near the grid bottom", f"{len(near)} of the 37 discovery boundaries lie within 0.25 decade"))
    out.append(("their gaps", f"gaps of {math.floor(-max(near) * 10) / 10:.1f} to {-min(near):.1f} decades"))
    fdb = load("results/p2_figdata.json")["h2b"]["sigma=0.02|eps=0.02|langmuir|pe=5.0"]
    lo2 = [n / m for _, n, m in fdb["disc"][:2]]
    out.append(("borderline slice", f"success was {lo2[0]:.2f} at the two lowest levels" if lo2[0] == lo2[1] < 0.5
                else "borderline slice changed"))
    out.append(("borderline crossing", f"crosses 50" + BS + "," + BS + f"% at $" + BS + f"Da = {h2b_all['sigma=0.02|eps=0.02|langmuir|pe=5.0']['da_disc']:.2f}$"))
    e7 = load("results/p2_e7_summary.json")
    e7_1 = [v["da_ident"] for k, v in e7.items() if abs(float(k.split("shift=")[1])) == 0.01]
    e7_disc = max(max(v["disc_by_da"].values()) for k, v in e7.items() if abs(float(k.split("shift=")[1])) == 0.01)
    out += [("E7 identifiability boundary at 1 % shift",
             f"identifiability boundary to $" + BS + f"Da " + BS + f"approx {min(e7_1):.0f}$ to {max(e7_1):.0f}"
             if all(e7_1) else "E7 ident missing"),
            ("E7 discovery at 1 % shift", f"at or below {math.floor(e7_disc * 100 + 0.5):.0f}" + BS + "," + BS + "% at every rate")]
    # review round 2 (M1): the bias of k under a 1 % step shift, medians over estimation replicates per (sigma, shift)
    b1, b10 = e7_bias(1.0), e7_bias(10.0)
    out += [("E7 bias at Da 10", f"by a factor of {1 / max(x for x in b10 if x < 1):.1f} to {max(b10):.1f} at $" + BS + "Da = 10$")]
    e8 = load("results/p2_e8_summary.json")
    sh = {"disc": [], "select": [], "ident": []}
    beyond, gap400, sel100 = 0, [], []
    for key in {k.rsplit("|", 1)[0] for k in e8}:
        a, b = e8[key + "|n_t=200"], e8[key + "|n_t=400"]
        for q in ("disc", "select"):
            sh[q].append(math.log10(b["da_" + q] / a["da_" + q]))
        if b["da_ident"] is None:
            beyond += 1
        else:
            sh["ident"].append(math.log10(b["da_ident"] / a["da_ident"]))
            gap400.append(math.log10(b["da_ident"] / b["da_disc"]))
        sel100 += [a["select_by_da"]["100.0"], b["select_by_da"]["100.0"]]
    f1 = lambda x: f"{math.floor(x * 10 + 0.5) / 10:.1f}"
    out += [("E8 every boundary up or unchanged", "moved to higher $" + BS + "Da$ or stayed"
             if min(min(v) for v in sh.values()) >= 0 and min(min(v) for v in sh.values()) == 0
             else "E8 a boundary moved down, or none stayed"),
            ("E8 smallest gap at 400", f"still failed at least {math.floor(min(gap400) * 10) / 10:.1f} decades"),
            ("E8 verdict words at 400", "discovery still failed" if all(
                v["words"] == "discovery fails before identifiability" for k, v in e8.items()
                if v["da_ident"] is not None) else "E8 words differ")]
    # review round 2 (M3): E9, E6 with noise-free forcing; the pre-declared two-thirds / one-third reading
    s9 = load("results/p2_e9_summary.json")
    rescued = sorted({k.split("|")[0] for k, v in s9.items() if v["frac_clean"] >= 2 / 3 and v["frac_e6"] < 2 / 3})
    hi = max(v["frac_clean"] for k, v in s9.items() if not k.split("|")[0].endswith("da31.6"))
    # E9 is reported in the Supplementary only (si_bindings)
    # E10: the LDF law wins at the finest sampling (3,991 times) where it lost at the grid's own 200 times
    r10 = load("results/p2_e10_resolution.json")["rows"]
    cells10 = sorted({k.split("|")[0] for k in r10})
    won = [c for c in cells10 if r10[f"{c}|3991"]["best"] == "ldf" and r10[f"{c}|grid200"]["best"] != "ldf"]
    words = {1: "one", 2: "two", 3: "three", 4: "four"}
    out.append(("E10 cells won", f"LDF law won in {words.get(len(won), len(won))} of the {words[len(cells10)]} cells tested"
                if all(r10[f"{c}|grid200"]["best"] != "ldf" for c in cells10) else "E10 LDF already won at grid 200"))
    e3 =load("results/p2_e3_coverage.json")["per_model"]["O1"]["coverage"]
    out += [("E3 coverage", f"only about {round(e3 * 100)}{BS},{BS}%")]
    # Discussion: where real columns sit (Supplementary Table 1) and the highest discovery boundary
    _, plo, phi, chem = practical_da()
    out.append(("practical Da physisorbent", f"between ${BS}Da {BS}approx {plo}$ and {phi}"))
    out.append(("practical Da chemisorbent", f"at ${BS}Da {BS}approx {chem['Da_low']:.0f}$ to {chem['Da_high']:.0f}"))
    top = max(s["da_disc"] for s in h2b.values() if s.get("da_disc"))
    topn = max(s["da_disc"] for k, s in h2b.items() if s.get("da_disc") and not k.startswith("sigma=0.0|"))
    out.append(("highest discovery boundary", f"(${BS}Da {BS}approx {topn:.0f}$ with noise, {top:.0f} without)"))
    # fresh review 2026-11-10 (M1): noise-free slices where discovery never fell below 50 % but k failed
    fig = load("results/p2_figdata.json")["h2b"]
    held = [k for k, s in fig.items() if h2b[k]["gap_decades"] is None and min(a / n for _, a, n in s["disc"]) >= 0.5]
    held_k = [h2b[k]["da_ident"] for k in held if h2b[k]["da_ident"] is not None]
    out.append(("no-noise slices: discovery held",
                f"in {len(held)}, all without noise, it never fell below 50" + BS + "," + BS + "%"
                if all(k.startswith("sigma=0.0|") for k in held) else "held slices with noise"))
    # (M3) success not monotone in noise at 2 % isotherm error
    mx = lambda sg: max(max(a for _, a, n in s["disc"]) for k, s in fig.items() if k.startswith(f"sigma={sg}|eps=0.02|"))
    out.append(("non-monotone in noise", f"reached at most {mx('0.0')} of 45 replicates without noise but up to "
                f"{max(mx('0.005'), mx('0.02'), mx('0.05'))} with noise"))
    # (M4) 0.5 % noise and 0.5 % isotherm error: slices with a boundary and its largest value
    b55 = [s["da_disc"] for k, s in h2b.items() if k.startswith("sigma=0.005|eps=0.005|") and s["da_disc"]]
    out.append(("0.5/0.5 slices with a boundary", f"in the {({3: 'three'}).get(len(b55), len(b55))} slices that kept a boundary"))
    out.append(("0.5/0.5 largest boundary", f"every discovery boundary fell to ${BS}Da {BS}le {math.ceil(max(b55) * 100) / 100:.2f}$"))
    # pre-submission revision 2026-11-11: new descriptive checks, M6, S1 on the map, corrections counts
    kh = load("results/p2_kh.json")
    out += [("kh at Da 316", f"($kh = {kh['kh_by_level']['316.227766']:.1f}$,"),
            ("kh at Da 1000", f"($kh = {kh['kh_by_level']['1000.0']:.0f}$)")]
    ns = load("results/p2_noise_support.json")["summary_da_le_10"]["eps0.02|sigma0.0"]
    out += [("support size without noise at 2 % isotherm error",
             f"kept on average {math.floor(ns['mean_support_size_min'] * 10) / 10:.1f} to "
             f"{math.ceil(ns['mean_support_size_max'] * 10) / 10:.1f} terms (four is")]
    m6 = load("results/p2_m6_summary.json")
    out += [("M6 grid", f"recovered it in none of {m6['n_rows']:,} fits".replace(",", "{,}", 1) if m6["n_success"] == 0
             else "M6 succeeded"),
            ("M6 six terms", "every fit kept six" if list(m6["support_size_counts"]) == ["6"] else "M6 sizes differ")]
    s1 = load("results/p2_s1_anchor.json")
    top_noisy = max(s["da_disc"] for k, s in h2b.items() if s.get("da_disc") and not k.startswith("sigma=0.0|"))
    out += [("S1 on the map", f"its columns ran at ${BS}Da {BS}approx {s1['Da']:.1f}$"),
            ("S1 Sips", f"and {s1['sips_Da']:.1f} (Sips)"),
            ("S1 above every noisy boundary", "above every discovery boundary we found with noise"
             if min(s1["Da"], s1["sips_Da"]) > top_noisy else "S1 not above")]
    # E11: about 2,000 observation times (declared 45e6e77 before running)
    e11, e8b = load("results/p2_e11_summary.json"), load("results/p2_e8_summary.json")
    pairs = [(e11[f"{i}|sigma={sg}|both"], e8b[f"{i}|sigma={sg}|n_t=200"]) for i in ("langmuir", "step")
             for sg in ("0.005", "0.02")]
    g11 = [math.log10(b["da_ident"] / b["da_disc"]) for b, _ in pairs if b["da_disc"] and b["da_ident"]]
    dsh = [math.log10(b["da_disc"] / a["da_disc"]) for b, a in pairs]
    ish = [math.log10(b["da_ident"] / a["da_ident"]) for b, a in pairs if b["da_ident"] and a["da_ident"]]
    no_id = [b for b, _ in pairs if b["da_ident"] is None]
    out += [("E11 gaps (abstract)", f"and by {math.floor(min(g11) * 10) / 10:.1f} to {max(g11):.1f} decades in three\nconditions re-run" if min(g11) >= 0.25 and len(g11) == 3
             else "E11 gap below threshold"),
            ("E11 gaps (Results)", f"by {math.floor(min(g11) * 10) / 10:.1f} to {max(g11):.1f}\ndecades, above the 0.25-decade threshold"),
            ("E11 slices with both", f"first in the {({3: 'three'}).get(len(g11), len(g11))} slices with both boundaries"),
            ("E11 discovery shift", f"discovery moved up by {math.floor(min(dsh) * 10) / 10:.1f} to {math.ceil(max(dsh) * 10) / 10:.1f} decades"),
            ("E11 identifiability shift", f"identifiability by {min(ish):.1f} to\n{max(ish):.1f} decade"),
            ("E11 fourth slice", f"reached ${BS}Da {BS}approx {round(no_id[0]['da_disc'], -1):.0f}$ while $k$ stayed identifiable beyond"
             if len(no_id) == 1 else "E11 no-ident slices != 1")]
    pre = load("results/p2_verdicts_preB90.json")["H2b"]
    both = [k for k in h2b if pre.get(k, {}).get("da_ident") and h2b[k].get("da_ident")]
    down = sum(h2b[k]["da_ident"] < pre[k]["da_ident"] * (1 - 1e-9) for k in both)
    up = sum(h2b[k]["da_ident"] > pre[k]["da_ident"] * (1 + 1e-9) for k in both)
    new = sum(1 for k in h2b if h2b[k].get("da_ident") and not pre.get(k, {}).get("da_ident"))
    out += [("B90 boundaries moved", f"moved {down} of the {len(both)} identifiability boundaries" if up == 0 else "B90 some moved up"),
            ("B90 boundaries new", f"brought {new} more onto the grid")]
    # (M5) E7: a 2 % shift of the step
    e7s = load("results/p2_e7_summary.json")
    d2 = {round(v["da_ident"], 1) for k, v in e7s.items() if k.endswith("shift=0.02") or k.endswith("shift=-0.02")}
    out.append(("E7 2 % shift", f"({d2.pop()} with a 2{BS},{BS}% shift)" if len(d2) == 1 else "E7 2% differs"))
    return out


def _thou(n):
    s = f"{n:,}"
    return s.replace(",", BS + ",") if n >= 10000 else s.replace(",", BS + ",") if n >= 1000 else s


def e7_bias(da, shifts=("-0.01", "0.01")):
    """Median k_hat/k (geometric midpoint of the interval) over estimation replicates 15..59, per (sigma, shift)."""
    cells = load("data/p2/manifest.json")["cells"]
    rows = load("results/p2_e7_stepshift.json")["rows"]
    med = []
    for s in ("0.005", "0.02"):
        for sh in shifts:
            est = [math.sqrt(r["ident"]["lo"] * r["ident"]["hi"]) / cells[k.split("|")[0]]["k_LDF"]
                   for k, r in rows.items() if "error" not in r["ident"] and int(k.split("|")[3]) >= 15
                   and k.split("|")[1] == s and k.split("|")[2] == sh and cells[k.split("|")[0]]["Da"] == da]
            med.append(statistics.median(est))
    return med


def e9_rows():
    """E9 table: LDF fraction with noise-free forcing and, in brackets, E6's, per (isotherm, sigma) and Da."""
    s9 = load("results/p2_e9_summary.json")
    f = lambda x: "0" if x == 0 else f"{x:.2f}"
    rows = []
    for iso in ("langmuir", "step"):
        for sg in ("0.005", "0.02"):
            cells_txt = " & ".join(f"{f(s9[k]['frac_clean'])} ({f(s9[k]['frac_e6'])})" for k in
                                   (f"{iso}_L1_pe1_da{d}|{sg}" for d in ("31.6", "100", "316", "1e+03")))
            rows.append(f"{'Langmuir' if iso == 'langmuir' else 'step'} & {float(sg) * 100:g}" + BS + "," + BS
                        + f"% & {cells_txt} " + BS + BS)
    return rows


def e10_rows():
    """E10 table: chosen law and LDF k_hat/k per cell at the grid's 200 and 400 times, 1,996 and 3,991 times."""
    r10 = load("results/p2_e10_resolution.json")["rows"]
    lab = {"ldf": "LDF", "qdf": "QDF", "pso": "PSO"}
    rows = []
    for c in ("langmuir_L1_pe1_da100", "step_L1_pe1_da100", "langmuir_L1_pe1_da1e+03", "step_L1_pe1_da1e+03"):
        iso, da = c.split("_")[0], c.split("_da")[1].replace("1e+03", "1000")
        cells_txt = " & ".join(f"{lab[r10[f'{c}|{n}']['best']]} ({r10[f'{c}|{n}']['k_ldf_over_k']:.2f})"
                               for n in ("grid200", "grid400", "1996", "3991"))
        rows.append(f"{'Langmuir' if iso == 'langmuir' else 'step'} & {da} & {cells_txt} " + BS + BS)
    return rows


def e7_rows():
    """SI Note 3 E7 table rows and the error-row count, from results/p2_e7_*.json."""
    cells = load("data/p2/manifest.json")["cells"]
    summ = load("results/p2_e7_summary.json")
    rows = load("results/p2_e7_stepshift.json")["rows"]
    out, n_err = [], sum("error" in r["ident"] for r in rows.values())
    for key in sorted(summ, key=lambda k: (float(k.split("|")[0][6:]), float(k.split("shift=")[1]))):
        v = summ[key]
        s, sh = key.split("|")[0][6:], key.split("shift=")[1]
        est = [math.sqrt(r["ident"]["lo"] * r["ident"]["hi"]) / cells[k.split("|")[0]]["k_LDF"]
               for k, r in rows.items() if "error" not in r["ident"] and int(k.split("|")[3]) >= 15
               and k.split("|")[1] == s and k.split("|")[2] == sh and cells[k.split("|")[0]]["Da"] == 10.0]
        di = v["da_ident"]
        out.append(f"{float(s) * 100:g}{BS},{BS}% & ${float(sh) * 100:+g}$ & {max(v['disc_by_da'].values()):.2f} & "
                   f"{'--' if di is None else (f'{di:.1f}' if di < 10 else f'{di:.0f}')} & "
                   f"{statistics.median(est):.2f} " + BS + BS)
    return out, n_err


def sig(x, n=2):
    """x rounded to n significant figures, as text with a thousands separator ({,}) above 9,999."""
    r = float(f"{x:.{n}g}")
    s = f"{r:,.0f}" if r >= 10 else f"{r:g}"
    return s.replace(",", "{,}") if r >= 1e4 else s


def practical_da():
    """Supplementary Table 1 and the Discussion: Da = k t_stoich of published columns (results/p2_practical_da.json)."""
    d = load("results/p2_practical_da.json")
    rng = {k: f"{sig(v['Da_low'])} to {sig(v['Da_high'])}" for k, v in d["by_source"].items()}
    s = d["summary"]
    return rng, sig(s["physisorbent_Da_low"], 1), sig(s["physisorbent_Da_high"]), s["chemisorbent_Da"]


def si_bindings():
    """G3 for the Supplementary Information: tables and counts recomputed from the results files."""
    out = []
    cells = load("data/p2/manifest.json")["cells"]
    e6 = load("results/p2_e6_modelselect.json")["rows"]
    by = {}
    for key, r in e6.items():
        n, s, e, _ = key.split("|")
        by.setdefault((cells[n]["iso"], float(s), float(e)), {}).setdefault(cells[n]["Da"], []).append(r["success"])
    pct = lambda x: f"{x:g}" + BS + "," + BS + "%"
    for (iso, s, e), d in sorted(by.items()):
        vals = [sum(v) / len(v) for _, v in sorted(d.items())]
        cells_txt = " & ".join("0" if v == 0 else f"{v:.2f}" for v in vals)
        out.append((f"E6 table row {iso} {s} {e}",
                    f"{'Langmuir' if iso == 'langmuir' else 'step'} & {pct(s * 100)}, "
                    f"{'0' if e == 0 else pct(e * 100)} & {cells_txt} " + BS + BS))
    cov = load("results/p2_e3_coverage.json")["per_model"]["O1"]
    out.append(("E3 O1 identifiable and covering", f"On O1, {_thou(cov['identifiable'])} of 51" + BS + ",840 rows met the "
                f"criterion, but only {_thou(cov['covers'])} intervals"))
    pre = load("results/p2_extra_o1ident_preB90.json")["rows"]
    cor = load("results/p2_extra_o1ident.json")["rows"]
    gain = sum(bool(cor[k].get("success")) and not bool(pre[k].get("success")) for k in cor)
    loss = sum(bool(pre[k].get("success")) and not bool(cor[k].get("success")) for k in cor)
    out.append(("B90 row flips", f"{_thou(gain)} rows became identifiable and {_thou(loss)}"))
    e4 = load("results/p2_e4_criteria.json")["variants"]
    for name, v in e4.items():
        out.append((f"E4 table row {name}", f"& {v['n_with_verdict']} & {-v['gap_max']:.2f} to {-v['gap_min']:.2f} " + BS + BS))
    e8 = load("results/p2_e8_summary.json")
    mn = {"best_subset|weak": "M4, weak", "stlsq|weak": "M2, weak", "ensemble|weak": "M3, weak"}
    f8 = lambda x: "--" if x is None else (f"{x:.2f}" if x < 10 else f"{x:.0f}")
    for key, v in e8.items():
        iso, sg, nt = key.split("|")
        g = "--" if v["da_ident"] is None else f"{math.log10(v['da_ident'] / v['da_disc']):.2f}"
        out.append((f"E8 table row {key}",
                    f"{'Langmuir' if iso == 'langmuir' else 'step'} & {float(sg[6:]) * 100:g}{BS},{BS}% & {nt[4:]} & "
                    f"{mn.get(v['best_method'], v['best_method'])} & {f8(v['da_disc'])} & {f8(v['da_select'])} & "
                    f"{f8(v['da_ident'])} & {g} " + BS + BS))
    out += [(f"E9 table row {i}", r) for i, r in enumerate(e9_rows())]
    out += [(f"E10 table row {i}", r) for i, r in enumerate(e10_rows())]
    rng, _, _, _ = practical_da()
    for src, tag in (("Lassitter et al. 2024", "(Fig.~10, read off) &"), ("Dantas et al. 2011", "(Tables 1, 2, 5) &"),
                     ("Krishnamurthy et al. 2025", "flow &"), ("Stampi-Bombelli et al. 2024", "(Table~6) &")):
        out.append((f"SI Table 2 {src}", f"{tag} {rng[src]} " + BS + BS))
    r10 = load("results/p2_e10_resolution.json")
    out.append(("E10 fields match", "agreed exactly with the stored fields"
                if all(v == 0.0 for ch in r10["checks"].values() for v in ch.values()) else "E10 fields differ"))
    out.append(("E10 even 200 at Langmuir 1000", "the LDF law, "
                + f"{-r10['rows']['langmuir_L1_pe1_da1e+03|200']['dll']['qdf']:.0f} log-likelihood units ahead of the quadratic"
                if r10["rows"]["langmuir_L1_pe1_da1e+03|200"]["best"] == "ldf" else "E10 even 200 not LDF"))
    s9 = load("results/p2_e9_summary.json")
    out.append(("E9 no errors", "No row had an" + "\n" + "error. The table gives the fraction with noise-free"
                if sum(v["errors"] for v in s9.values()) == 0 and sum(v["n"] for v in s9.values()) == 720 else "E9 errors"))
    e7r, e7err = e7_rows()
    out += [(f"E7 table row {i}", r) for i, r in enumerate(e7r)]
    out.append(("E7 error rows", f"these {_thou(e7err)} rows raise an error"))
    # review round 2 (M1, M2, m5): E7 interval widths and bias; the grid's isotherm-error shift of Da*_ident
    e7 = load("results/p2_e7_stepshift.json")["rows"]
    rat = {}
    for k, r in e7.items():
        name, s, sh, rep = k.split("|")
        if int(rep) >= 15 and "error" not in r["ident"] and cells[name]["Da"] <= 31.7:
            rat.setdefault((s, sh, cells[name]["Da"]), []).append(r["ident"]["hi"] / r["ident"]["lo"])
    med_w = max(statistics.median(v) for v in rat.values())
    max_w = max(max(v) for v in rat.values())
    out.append(("E7 widths", f"bound at most {med_w:.2f} per level, and at most {max_w:.2f} in any replicate"))
    b1, b3 = e7_bias(1.0), e7_bias(3.1622776601683795)
    out.append(("E7 bias Da 1 and 3.16", f"off by {round((1 - min(b1)) * 100)} to {round((max(b1) - 1) * 100)}" + BS + "," + BS
                + f"% at $" + BS + f"Da = 1$ and {round((1 - max(x for x in b3 if x < 1)) * 100)} to "
                f"{round((max(b3) - 1) * 100)}" + BS + "," + BS + "% at"))
    h2b = load("results/p2_verdicts.json")["H2b"]
    d5 = [math.log10(h2b[f"sigma=0.005|eps=0.05|{i}|pe={p}"]["da_ident"] / h2b[f"sigma=0.005|eps=0.0|{i}|pe={p}"]["da_ident"])
          for i in ("langmuir", "step") for p in ("0.2", "1.0", "5.0")]
    out.append(("eps 5 % ident shift", f"but by {-max(d5):.2f} to {-min(d5):.2f} decade at 5"))
    out.append(("O1 rows identifiable, corrected", f"& {_thou(sum(bool(v.get('success')) for v in cor.values()))} " + BS + BS))
    # Lib-A held-out fidelity (PREREG s.3, s.4.3; computed after the verdicts)
    g = load("results/p2_liba_summary.json")["groups"]
    t = lambda lib, s, grp, f="median_fid_true": g[f"{lib}|sigma={s}|{grp}"][f]
    out.append(("Lib-A cells", f"on all {load('results/p2_liba_summary.json')['n_cells']} L1 cells"))
    out.append(("Lib-A no noise, low Da", f"was {t('A', '0.0', 'Da<=10'):.3f} for Lib-A and\n{t('B', '0.0', 'Da<=10'):.3f} for Lib-B"))
    out.append(("Lib-A no noise, high Da", f"but {t('A', '0.0', 'Da>=31.6'):.2f} against {t('B', '0.0', 'Da>=31.6'):.2f} at"))
    dmax = max(abs(t("A", s, grp, "median_fid_obs") - t("B", s, grp, "median_fid_obs"))
               for s in ("0.005", "0.02", "0.05") for grp in ("Da<=10", "Da>=31.6"))
    out.append(("Lib-A with noise, largest difference", f"differed by at most {math.ceil(dmax * 100) / 100:.2f} in median"))
    out.append(("Lib-A 2 % noise", f"{t('A', '0.02', 'Da<=10', 'median_fid_obs'):.2f} against "
                f"{t('B', '0.02', 'Da<=10', 'median_fid_obs'):.2f})"))
    return out


def main():
    os.chdir(HERE)
    r = subprocess.run([sys.executable, "make_article_bib.py"], capture_output=True, text=True)
    if r.returncode or "missing: []" not in r.stdout:
        fail("G1", r.stdout + r.stderr)
    for doc in ("article.tex", "supplementary_main.tex"):
        r = subprocess.run([TECTONIC, "-X", "compile", "--keep-logs", doc], capture_output=True, text=True)
        log = r.stdout + r.stderr
        if r.returncode or re.search(r"^error|undefined", log, re.M | re.I):
            fail("G2", f"{doc}: " + "; ".join(l for l in log.splitlines() if re.search("error|undefined", l, re.I))[:400])
        # G2b: nothing may print past the margin (found 2026-11-09: the Unit column of Supplementary
        # Table 1 was 210 pt off the page)
        texlog = open(doc[:-4] + ".log", encoding="utf-8", errors="replace").read()
        over = [float(x) for x in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", texlog)]
        if any(x > 2.0 for x in over):
            fail("G2", f"{doc}: overfull box(es) of {', '.join(f'{x:.0f}' for x in over if x > 2)} pt; see {doc[:-4]}.log")
    tex = open("article.tex", encoding="utf-8").read()
    si = open("supplementary.tex", encoding="utf-8").read()
    body, si_body = strip_comments(tex), strip_comments(si)
    flat = norm(body)
    for desc, lit in bindings():
        if norm(lit) not in flat:
            fail("G3", f"{desc}: expected {lit!r} in the text")
    # G3b: prose joined onto a comment line disappears from the PDF and leaves a paragraph that starts
    # mid-sentence (found 2026-11-09: the M1 sentence had been lost this way)
    for name, txt in (("article", body), ("SI", si_body)):
        for p in re.split(r"\n\s*\n", txt):
            if re.match(r"[a-z]", p.strip()):
                fail("G3", f"{name}: a paragraph starts mid-sentence (text after a % comment?): {p.strip()[:80]!r}")
    si_flat = norm(si_body)
    for desc, lit in si_bindings():
        if norm(lit) not in si_flat:
            fail("G3", f"SI {desc}: expected {lit!r}")
    abst = body[body.index(BS + "begin{abstract}") + 16:body.index(BS + "end{abstract}")]
    if len(abst.split()) > 150:
        fail("G4", f"abstract {len(abst.split())} words > 150")
    # main text as the journal counts it: Introduction + Results + Discussion (the display items,
    # their legends, Methods, references and the abstract are excluded); comments already stripped
    a, b = tex.index("---- Introduction"), tex.index("% ---- Display items")
    main_words = rendered_words(strip_comments(tex[a:b]))
    main_part = body.split(BS + "section*{Extended Data}")[0]   # Extended Data are not display items
    disp = len(re.findall(re.escape(BS) + r"begin\{(figure|table)\}", main_part))
    if main_words > 3500:
        fail("G4", f"main text {main_words} words > 3,500")
    if disp > 6:
        fail("G5", f"{disp} display items > 6")
    nd = tex.count("\u2014") + body.count("---")
    if nd > 5:
        fail("G6", f"{nd} em dashes > 5")
    banned = [r"\bthe first to\b", r"\bnovel\b", r"\bgroundbreaking\b", r"\bparadigm\b", r"\bunprecedented\b",
              r"\bdramatic(ally)?\b", r"\bdrastic(ally)?\b", r"\bremarkabl[ey]\b", r"\bstriking(ly)?\b",
              r"\bseamless(ly)?\b", r"\bleverag(e|es|ing)\b", r"\butiliz(e|es|ing)\b", r"\bdelv(e|es|ing)\b",
              r"\bcrucial\b", r"\bpivotal\b", r"\bstate-of-the-art\b", r"\bit is worth noting\b",
              r"\binterestingly\b", r"\bnotably\b", r"\bproves?\b", r"\bsignificantly\b"]
    for name, text in (("article", body), ("SI", si_body)):
        for b in banned:
            for m in re.finditer(b, text, re.I):
                fail("G7", f"{name}: banned phrase {m.group(0)!r}")
    for name, text in (("article", body), ("SI", si_body)):
        for p in ("PENDING", "VERIFY", "[CHECK", "TODO"):
            if p in text:
                fail("G8", f"{name}: placeholder {p}")
    # every Extended Data figure file must be cited in the main part ("Extended Data Fig.~3",
    # "Extended Data Figs.~1 and~2"); the Extended Data section's own legends do not count
    cited = set()
    for grp in re.findall(r"Extended Data Figs?\.~([0-9~, and\-]+)", main_part):
        cited |= {int(n) for n in re.findall(r"\d+", grp)}
    ed_files = [f for f in sorted(os.listdir(HERE)) if re.match(r"fig_ed\d+(_[^.]*)?\.pdf$", f)]
    for f in ed_files:
        n = int(re.match(r"fig_ed(\d+)", f).group(1))
        if n not in cited:
            fail("G9", f"{f} exists but Extended Data Fig. {n} is not cited in the main text")
    if not ed_files:
        fail("G9", "no Extended Data figure files found (check the file-name pattern)")
    for inc in re.findall(re.escape(BS) + r"includegraphics(?:\[[^]]*\])?\{([^}]*)\}", body):
        stem = os.path.splitext(inc)[0]
        if not os.path.exists(inc):
            fail("G10", f"missing figure {inc}")
        elif not os.path.exists(stem + ".prov.json"):
            fail("G10", f"{inc} has no provenance file")
    print(f"main text (Introduction + Results + Discussion): {main_words} words; "
          f"display items {disp}; em dashes {nd}; abstract {len(abst.split())} words")
    if FAIL:
        print("BUILD FAILED")
        for f in FAIL:
            print("  " + f)
        sys.exit(1)
    print("BUILD OK: all gates passed")


if __name__ == "__main__":
    main()
