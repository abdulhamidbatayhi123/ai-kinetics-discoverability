"""Build and check Paper 2 (article + Supplementary Information). Exits 1 on any failure.

Gates (pattern of pinn-machining revision_eaai/build/gates.py; rules from PRESENTATION_PLAN.md):
  G1  the bibliography is regenerated from bib_p2.tex (make_article_bib.py) and nothing is missing
  G2  article.tex and supplementary_main.tex compile with no error and no undefined reference
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
    out = [("H2b slices with a verdict", f"Of the {len(h2b)} slices, {len(gaps)} had both"),
           ("H2b gap range (Results)", f"from {lo:.1f} to {hi:.1f} decades"),
           ("H2b gap range (abstract)", f"by {lo:.1f} to {hi:.1f} decades"),
           ("H2b median gap, Langmuir", f"median of {med(lang):.1f} decades for the"),
           ("H2b median gap, step", f"{med(step):.1f} for the step"),
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
            ("gap lower bound", f"at least {summ['min_gap_lower_bound_decades']:.1f} decades")]
    cls = rob["h2b_no_verdict_classes"]
    miss = sum(n for k, n in cls.items() if k.startswith("discovery missing"))
    never = sum(n for k, n in cls.items() if "discovery missing, always < 50" in k)
    always = sum(n for k, n in cls.items() if "discovery missing, always >= 50" in k)
    strad = sum(n for k, n in cls.items() if "discovery missing, straddles" in k)
    only_id = sum(n for k, n in cls.items() if k.startswith("discovery present"))
    out += [("no-verdict: discovery missing", f"missing in {miss}"), ("never 50 %", f"In {never},"),
            ("never below 50 %", f"In {always}, all"), ("straddles", f"other {strad},"),
            ("only identifiability missing", f"remaining {only_id} slices")]
    m1 = load("results/p2_extra_m1.json")["rows"]
    n_ok = sum(bool(v.get("success")) for v in m1.values())
    names = {1: "one", 2: "two", 3: "three"}
    out += [("M1 successes", f"{names.get(n_ok, n_ok)} of its nine fits" if len(m1) == 9 else "M1 rows != 9")]
    m8 = load("results/p2_e2_m8.json")["rows"]
    out += [("M8 (E2)", f"none of {len(m8)} fits" if not any(v.get("success") for v in m8.values())
             else "M8 has successes")]
    fig = load("results/p2_figdata.json")["h2b"]
    eps2 = [k for k in h2b if "eps=0.02" in k]
    reach = sum(any(a / n >= 0.5 for _, a, n in (fig[k]["disc"] or [])) for k in eps2)
    out += [("eps 2 %: slices reaching 50 % at any level", f"in only {reach} of {len(eps2)} slices")]
    e3 = load("results/p2_e3_coverage.json")["per_model"]["O1"]["coverage"]
    out += [("E3 coverage", f"only about {round(e3 * 100)}{BS},{BS}%")]
    return out


def main():
    os.chdir(HERE)
    r = subprocess.run([sys.executable, "make_article_bib.py"], capture_output=True, text=True)
    if r.returncode or "missing: []" not in r.stdout:
        fail("G1", r.stdout + r.stderr)
    for doc in ("article.tex", "supplementary_main.tex"):
        r = subprocess.run([TECTONIC, "-X", "compile", doc], capture_output=True, text=True)
        log = r.stdout + r.stderr
        if r.returncode or re.search(r"^error|undefined", log, re.M | re.I):
            fail("G2", f"{doc}: " + "; ".join(l for l in log.splitlines() if re.search("error|undefined", l, re.I))[:400])
    tex = open("article.tex", encoding="utf-8").read()
    si = open("supplementary.tex", encoding="utf-8").read()
    body, si_body = strip_comments(tex), strip_comments(si)
    flat = norm(body)
    for desc, lit in bindings():
        if norm(lit) not in flat:
            fail("G3", f"{desc}: expected {lit!r} in the text")
    abst = body[body.index(BS + "begin{abstract}") + 16:body.index(BS + "end{abstract}")]
    if len(abst.split()) > 150:
        fail("G4", f"abstract {len(abst.split())} words > 150")
    # main text as the journal counts it: Introduction + Results + Discussion (the display items,
    # their legends, Methods, references and the abstract are excluded); comments already stripped
    a, b = tex.index("---- Introduction"), tex.index("% ---- Display items")
    main_words = len(re.sub(re.escape(BS) + r"cite[pt]?\{[^}]*\}", "", strip_comments(tex[a:b])).split())
    disp = len(re.findall(re.escape(BS) + r"begin\{(figure|table)\}", body))
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
    for f in sorted(os.listdir(HERE)):
        m = re.match(r"fig_ed(\d+)\.pdf$", f)
        if m and f"Extended Data Fig.~{int(m.group(1))}" not in body:
            fail("G9", f"{f} exists but 'Extended Data Fig.~{int(m.group(1))}' is not cited")
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
