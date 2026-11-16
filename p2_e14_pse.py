"""E14 (post hoc, declared in EXPLORATORY_P2.md before running): parallel symbolic enumeration (PSE) on M7's subgrid.

Merges the Kaggle parts (kaggle_e14/), checks that every declared row is present, and reports per slice (isotherm,
sigma, eps at Pe ~94): PSE's success fraction per Da on replicates 15..29, beside M7 (PySR) and the slice's best
method from the main analysis on the same replicates, and the last level with at least 50 % success against the
slice's Da*_ident (results/p2_verdicts.json H2b). The reading fixed in advance: if in any slice PSE succeeds in at
least half the replicates at a level within 0.25 decade of Da*_ident (or above it), the gap closes for PSE there.

    python p2_e14_pse.py summary kaggle_e14/out/k*/e14_part*.json  ->  results/p2_e14_rows.json, p2_e14_summary.json
"""
import json
import math
import sys

REPS = range(15, 30)
SIGMAS, EPSS = ("0.005", "0.02"), ("0.0", "0.02")
ROWS, SUMMARY = "results/p2_e14_rows.json", "results/p2_e14_summary.json"
TOL = 0.25


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "summary":
        sys.exit(__doc__)
    from p2.io_utils import write_atomic
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    names = sorted(n for n, c in cells.items() if c["law"] == "L1" and c["iso"] in ("langmuir", "step")
                   and c["pe_mult"] == 1.0 and not c.get("refined"))
    rows, meta, seen = {}, {}, 0
    for p in sys.argv[2:]:
        part = json.load(open(p))
        seen += len(part["rows"])
        rows.update(part["rows"])
        meta = {k: part.get(k) for k in ("pse_commit", "time_limit", "versions")}
    want = {f"{n}|{s}|{e}|{r}|pse|strong" for n in names for s in SIGMAS for e in EPSS for r in REPS}
    if seen != len(rows) or set(rows) != want:
        sys.exit(f"FAIL keys: {seen} read, {len(rows)} unique, {len(want)} expected")
    m7 = json.load(open("results/p2_extra_m7.json"))["rows"]
    o1 = json.load(open("results/p2_o1.json"))["rows"]
    V = json.load(open("results/p2_verdicts.json"))["H2b"]
    out = {"design": {**meta, "rows": len(rows), "replicates": [REPS.start, REPS.stop - 1],
                      "errors_counted_as_failures": sum(1 for v in rows.values() if "error" in v)}, "slices": {}}
    closes = []
    for iso in ("langmuir", "step"):
        for s in SIGMAS:
            for e in EPSS:
                vk = f"sigma={float(s)}|eps={float(e)}|{iso}|pe=1.0"
                best = V[vk]["best_method"]
                da_id = V[vk]["da_ident"]
                pse, m7f, bestf = {}, {}, {}
                for n in names:
                    if cells[n]["iso"] != iso:
                        continue
                    da = cells[n]["Da"]
                    pse[da] = sum(rows[f"{n}|{s}|{e}|{r}|pse|strong"]["success"] for r in REPS) / len(REPS)
                    m7f[da] = sum(m7[f"{n}|{s}|{e}|{r}|m7|strong"]["success"] for r in REPS) / len(REPS)
                    src = m7 if best.startswith("m7") else o1
                    bestf[da] = sum(src[f"{n}|{s}|{e}|{r}|{best}"]["success"] for r in REPS) / len(REPS)
                last = max((d for d, f in pse.items() if f >= 0.5), default=None)
                dist = math.log10(da_id / last) if (last and da_id) else None
                close = dist is not None and dist <= TOL
                closes.append(close)
                out["slices"][vk] = {
                    "pse_by_da": {str(d): pse[d] for d in sorted(pse)}, "m7_by_da": {str(d): m7f[d] for d in sorted(m7f)},
                    "best_method": best, "best_by_da": {str(d): bestf[d] for d in sorted(bestf)},
                    "pse_last_ge50": last, "da_ident": da_id,
                    "decades_below_ident": dist, "gap_closes": close}
    out["reading"] = {"gap_closes_in_any_slice": any(closes), "slices_closing": sum(closes)}
    write_atomic({"rows": rows}, ROWS)
    write_atomic(out, SUMMARY)
    for k, v in out["slices"].items():
        print(k, "PSE last>=50%:", v["pse_last_ge50"], "Da*_ident:", round(v["da_ident"] or 0, 1),
              "below by:", None if v["decades_below_ident"] is None else round(v["decades_below_ident"], 2))
    print(out["reading"], out["design"])


if __name__ == "__main__":
    main()
