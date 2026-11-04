"""Side-by-side of the as-run verdicts (before A6/B89) and the corrected ones (Supplementary
Note 2). Reads results/p2_verdicts_asrun.json and results/p2_verdicts.json; prints only.

    python p2_compare_verdicts.py
"""
import collections
import json

o = json.load(open("results/p2_extra_o1ident.json"))["rows"]
print("o1ident rows", len(o), "errors", sum("error" in v for v in o.values()),
      "identifiable", sum(bool(v.get("success")) for v in o.values()))
a = json.load(open("results/p2_verdicts_asrun.json"))
c = json.load(open("results/p2_verdicts.json"))
print("positive control, as run:", json.dumps(a["positive_control"]))
print("positive control, corrected:", json.dumps(c["positive_control"]))
for key in ("H2b_overall", "H2a", "H2c"):
    print(f"{key} as run   :", json.dumps(a.get(key))[:400])
    print(f"{key} corrected:", json.dumps(c.get(key))[:400])


def words(v):
    cnt = collections.Counter()
    for k, s in v["H2b"].items():
        w = s.get("verdict") if isinstance(s, dict) else s
        iso = next((p for p in k.split("|") if p in ("langmuir", "step")), "?")
        cnt[(iso, str(w)[:70])] += 1
    return cnt


for name, v in (("as run", a), ("corrected", c)):
    print("H2b slices,", name)
    for k, n in sorted(words(v).items()):
        print("   ", k, n)
