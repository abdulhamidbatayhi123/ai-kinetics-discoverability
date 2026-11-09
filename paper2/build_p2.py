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
           ("H2b slices with a verdict (abstract)", f"In all {len(gaps)} of {len(h2b)} conditions"),
           ("H2b slices with a verdict (Fig. 3 legend)", f"for the {len(gaps)} slices with both boundaries"),
           ("H2b gap range (Results)", f"from {lo:.1f} to {hi:.1f} decades"),
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
            ("min P(ident) at Da <= 31.6", f"at least {int(summ['min_p_ident_da_le_31.6'] * 100)}{BS},{BS}% of replicates"),
            ("gap lower bound", f"at least {math.floor(summ['min_gap_lower_bound_decades'] * 100) / 100:.2f} decades")]
    cls = rob["h2b_no_verdict_classes"]
    miss = sum(n for k, n in cls.items() if k.startswith("discovery missing"))
    never = sum(n for k, n in cls.items() if "discovery missing, always < 50" in k)
    always = sum(n for k, n in cls.items() if "discovery missing, always >= 50" in k)
    strad = sum(n for k, n in cls.items() if "discovery missing, straddles" in k)
    only_id = sum(n for k, n in cls.items() if k.startswith("discovery present"))
    out += [("no-verdict: discovery missing", f"missing in all {miss}" if only_id == 0 else f"missing in {miss}"),
            ("never 50 %", f"In {never},"), ("never below 50 %", f"In {always}, all"), ("straddles", f"other {strad},")]
    if only_id:
        out += [("only identifiability missing", f"remaining {only_id} slices")]
    no_ident = sum(n for k, n in cls.items() if "identifiability missing" in k)
    out += [("identifiability boundary present among no-verdict slices",
             f"on the grid in {miss + only_id - no_ident} of the {miss + only_id}")]
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
        out += [("M7 last level vs Da*_ident", f"that level lay {min(m7gaps):.1f} to {max(m7gaps):.1f} decades"),
                ("Table 1 envelope: M7 range", f"{min(m7gaps):.1f} to {max(m7gaps):.1f} decades below"),
                ("Table 1 envelope: M7 slices", f"symbolic regression ({ {4: 'four', 3: 'three', 5: 'five'}.get(len(m7gaps), len(m7gaps))} slices")]
    # Review P4: the selected method equals each slice's best monotone method on the estimation replicates
    env_same = all(s["da_disc"] is not None and abs(math.log10(max(x for x in s["da_disc_by_method"].values() if x)
                                                                  / s["da_disc"])) < 1e-9
                   for s in h2b.values() if s["gap_decades"] is not None)
    out += [("Table 1 envelope equals selection", f"gives the same {len(gaps)} gaps" if env_same else "envelope differs")]
    fig = load("results/p2_figdata.json")["h2b"]
    eps2 = [k for k in h2b if "eps=0.02" in k]
    reach = sum(any(a / n >= 0.5 for _, a, n in (fig[k]["disc"] or [])) for k in eps2)
    out += [("eps 2 %: slices reaching 50 % at any level", f"only {reach} of {len(eps2)} slices reached it")]
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
            ("E6 min with isotherm error", f"at least {round(lo10e * 100)}" + BS + "," + BS + "% with 2"),
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
    out.append(("discovery at 0.5 % noise and error", f"confined discovery to $" + BS + f"Da " + BS + f"le {math.ceil(max(d55) * 100) / 100:.2f}$"))
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
             f"identifiability boundary fell to $" + BS + f"Da " + BS + f"approx {min(e7_1):.0f}$ to {max(e7_1):.0f}"
             if all(e7_1) else "E7 ident missing"),
            ("E7 discovery at 1 % shift", f"at or below {math.floor(e7_disc * 100 + 0.5):.0f}" + BS + "," + BS + "% at every rate")]
    # review round 2 (M1): the bias of k under a 1 % step shift, medians over estimation replicates per (sigma, shift)
    b1, b10 = e7_bias(1.0), e7_bias(10.0)
    out += [("E7 bias at Da 1", f"by {round((1 - min(b1)) * 100)} to {round((max(b1) - 1) * 100)}" + BS + "," + BS + "% at $" + BS + "Da = 1$"
             if min(b1) < 1 < max(b1) else "E7 bias Da 1 one-sided"),
            ("E7 bias at Da 10", f"by a factor of {1 / max(x for x in b10 if x < 1):.1f} to {max(b10):.1f} at $" + BS + "Da = 10$")]
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
    out += [("E8 discovery shift", f"discovery by {f1(min(sh['disc']))} to {f1(max(sh['disc']))} decade"),
            ("E8 selection shift", f"among the laws by {f1(min(sh['select']))} to {f1(max(sh['select']))} decade"),
            ("E8 selection shift (Discussion)", f"sampling rate widened it by {f1(min(sh['select']))} to {f1(max(sh['select']))} decade"),
            ("E8 identifiability shift", f"identifiability by up to {f1(max(sh['ident']))} decade"
             + (" or beyond the grid" if beyond else "")),
            ("E8 every boundary up or unchanged", "moved to higher $" + BS + "Da$ or stayed"
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
    out += [("E9 rescued cells", "rescued" + "\n" + "it only for the Langmuir sorbent at $" + BS + "Da = 31.6$"
             if rescued == ["langmuir_L1_pe1_da31.6"] else f"E9 rescued {rescued}"),
            ("E9 at most above 31.6", f"chosen in at most {round(hi * 100)}" + BS + "," + BS + "% of replicates"
             if hi <= 1 / 3 else "E9 above one third")]
    # E10: the LDF law wins at the finest sampling (3,991 times) where it lost at the grid's own 200 times
    r10 = load("results/p2_e10_resolution.json")["rows"]
    cells10 = sorted({k.split("|")[0] for k in r10})
    won = [c for c in cells10 if r10[f"{c}|3991"]["best"] == "ldf" and r10[f"{c}|grid200"]["best"] != "ldf"]
    words = {1: "one", 2: "two", 3: "three", 4: "four"}
    out.append(("E10 cells won", f"LDF law won in {words.get(len(won), len(won))} of the {words[len(cells10)]} cells tested"
                if all(r10[f"{c}|grid200"]["best"] != "ldf" for c in cells10) else "E10 LDF already won at grid 200"))
    e3 =load("results/p2_e3_coverage.json")["per_model"]["O1"]["coverage"]
    out += [("E3 coverage", f"only about {round(e3 * 100)}{BS},{BS}%")]
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
    r10 = load("results/p2_e10_resolution.json")
    out.append(("E10 fields match", "agreed exactly with the stored fields"
                if all(v == 0.0 for ch in r10["checks"].values() for v in ch.values()) else "E10 fields differ"))
    out.append(("E10 even 200 at Langmuir 1000", "chose the LDF law by "
                + f"{-r10['rows']['langmuir_L1_pe1_da1e+03|200']['dll']['qdf']:.0f} log-likelihood units"
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
