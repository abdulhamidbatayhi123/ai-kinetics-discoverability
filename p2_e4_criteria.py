"""E4 (post-verdict, declared in EXPLORATORY_P2.md before running): H2b under matched success
criteria. p2_analyze.verdicts is called UNCHANGED; only each row's 'success' is re-scored:

  pre      the pre-registered criteria (reproduces results/p2_verdicts.json's words)
  a        discovery relaxed: support exactly {q, qstar} and k_hat > 0 (q coefficient negative);
           the ratio test dropped (the q* coefficient is not stored)
  b        identifiability strict: 95 % interval inside [0.9 k, 1.1 k]
  c        identifiability by the point estimate: sqrt(lo * hi) inside [k/2, 2k]
  d        a and c together

Boundaries are point estimates (n_boot = 0): the verdict words depend only on them.
Writes results/p2_e4_criteria.json.

    python p2_e4_criteria.py
"""
import collections
import json
import math

import p2_analyze as A
from p2.io_utils import write_atomic


def load(p):
    return json.load(open(p))["rows"]


def rescore_disc(rows):
    out = {}
    for k, r in rows.items():
        if "error" in r:
            out[k] = r
            continue
        sup = set(r.get("support", []))
        kh = r.get("k_hat")
        out[k] = {**r, "success": sup == {"q", "qstar"} and kh is not None and kh > 0}
    return out


def rescore_ident(rows, cells, rule):
    out = {}
    for k, r in rows.items():
        if "error" in r or "interval" not in r:
            out[k] = r
            continue
        kt = cells[k.split("|")[0]]["k_LDF"]
        lo, hi = r["interval"]["lo"], r["interval"]["hi"]
        if rule == "b":
            ok = 0.9 * kt <= lo and hi <= 1.1 * kt
        else:   # "c"
            ok = 0.5 * kt <= math.sqrt(lo * hi) <= 2.0 * kt
        out[k] = {**r, "success": bool(ok)}
    return out


def summarise(v):
    h = v["H2b"]
    words = collections.Counter(s["words"] for s in h.values())
    gaps = [s["gap_decades"] for s in h.values() if s.get("gap_decades") is not None]
    return {"overall": v["H2b_overall"]["words"], "word_counts": dict(words),
            "n_with_verdict": len(gaps),
            "gap_min": min(gaps) if gaps else None, "gap_max": max(gaps) if gaps else None,
            "gap_median": sorted(gaps)[len(gaps) // 2] if gaps else None,
            "positive_control": {i: p["passed"] for i, p in v["positive_control"].items()},
            "slices": {k: {"words": s["words"], "gap": s.get("gap_decades"),
                           "da_disc": s.get("da_disc"), "da_ident": s.get("da_ident")}
                       for k, s in h.items()}}


def main():
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    o1 = load("results/p2_o1.json")
    o1.update(load("results/p2_extra_m7.json"))
    o2 = load("results/p2_o2.json")
    ident = load("results/p2_extra_o1ident.json")
    rstats = json.load(open("results/p2_rstats.json"))["cells"]
    o1a = rescore_disc(o1)
    idb, idc = rescore_ident(ident, cells, "b"), rescore_ident(ident, cells, "c")
    runs = {"pre": (o1, ident), "a": (o1a, ident), "b": (o1, idb), "c": (o1, idc), "d": (o1a, idc)}
    out = {"_what": __doc__.splitlines()[0], "variants": {}}
    for name, (d, i) in runs.items():
        v = A.verdicts(cells, d, o2, i, rstats, n_boot=0)
        out["variants"][name] = summarise(v)
        s = out["variants"][name]
        print(f"{name}: {s['overall']} | {s['word_counts']} | gaps {s['gap_min']} .. {s['gap_max']}", flush=True)
    write_atomic(out, "results/p2_e4_criteria.json")


if __name__ == "__main__":
    main()
