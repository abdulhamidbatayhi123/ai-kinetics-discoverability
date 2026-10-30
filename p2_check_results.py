"""Summarise a grid results file: rows, cells, rows per cell, errors, freeze commit.
Used after each grid step, before its results are committed.

    python p2_check_results.py results/<file>.json
"""
import collections
import json
import sys

r = json.load(open(sys.argv[1]))
rows = r["rows"]
cells = collections.Counter(k.split("|")[0] for k in rows)
err = collections.Counter()
for k, v in rows.items():
    if isinstance(v, dict) and v.get("error"):
        err[str(v["error"])[:80]] += 1
capped = sum(1 for v in rows.values() if isinstance(v, dict) and v.get("n_capped"))
print("freeze", str(r.get("freeze_commit", ""))[:8], "| rows", len(rows), "| cells", len(cells),
      "| rows/cell", sorted(set(cells.values())), "| errors", sum(err.values()),
      "| rows with capped solves (A5)", capped)
for e, n in err.most_common(5):
    print("  ", n, e)
k0 = next(iter(rows))
print("  e.g.", k0, str(rows[k0])[:200])
