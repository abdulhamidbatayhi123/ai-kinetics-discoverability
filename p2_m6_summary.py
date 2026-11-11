"""Summary of the M6 (SINDy-PI, isothermal control) grid rows, which no earlier driver summarised
(found by a pre-submission review, 2026-11-11). Reads results/p2_extra_m6.json only.

    python p2_m6_summary.py  ->  results/p2_m6_summary.json
"""
import collections
import json

from p2.io_utils import write_atomic


def main():
    rows = json.load(open("results/p2_extra_m6.json"))["rows"]
    sizes = collections.Counter(len(v["support"]) for v in rows.values())
    by_sigma = collections.defaultdict(lambda: [0, 0])
    for k, v in rows.items():
        s = k.split("|")[1]
        by_sigma[s][0] += bool(v["success"])
        by_sigma[s][1] += 1
    out = {"n_rows": len(rows), "n_success": sum(bool(v["success"]) for v in rows.values()),
           "support_size_counts": {str(k): n for k, n in sorted(sizes.items())},
           "success_by_sigma": {s: {"success": a, "n": n} for s, (a, n) in sorted(by_sigma.items())},
           "n_distinct_supports": len({tuple(sorted(v["support"])) for v in rows.values()})}
    write_atomic(out, "results/p2_m6_summary.json")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
