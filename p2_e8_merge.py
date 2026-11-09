"""E8: merge the five Kaggle parts, validate them locally, then write the rows and the summary.

Checks (any failure exits 1 and writes nothing): exactly the 4,320 expected keys, each once
(p2_e8_sampling.expected_keys); a fixed-seed sample of rows (default 4, half at each sampling rate)
recomputed locally with p2_e8_sampling.one_row agrees exactly on every discovery outcome, on the
identifiability outcome with lo and hi to a relative 1e-6 (or the same error text), and, for
replicates 15..59, on the chosen law with every law's log-likelihood to a relative 1e-6.
Then writes results/p2_e8_sampling.json and results/p2_e8_summary.json (p2_e8_sampling.summarise).

    python p2_e8_merge.py [n_check]
"""
import glob
import json
import random
import sys

from p2.io_utils import write_atomic

PARTS = sorted(glob.glob("kaggle_e8/out/k*/e8_part*.json"))


def close(a, b):
    return abs(a - b) <= 1e-6 * max(abs(a), abs(b), 1e-300)


def same(loc, kag):
    if loc["disc"] != kag["disc"]:
        return False
    li, ki = loc["ident"], kag["ident"]
    if "error" in li or "error" in ki:
        if li.get("error") != ki.get("error"):
            return False
    elif li["success"] != ki["success"] or not (close(li["lo"], ki["lo"]) and close(li["hi"], ki["hi"])):
        return False
    if "select" in loc or "select" in kag:
        ls, ks = loc.get("select", {}), kag.get("select", {})
        if "error" in ls or "error" in ks:
            return ls.get("error") == ks.get("error")
        return ls["best"] == ks["best"] and all(close(ls["ll"][n], ks["ll"][n]) for n in ls["ll"])
    return True


def main():
    n_check = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    from p2_e8_sampling import ROWS, SUMMARY, expected_keys, one_row, summarise
    if len(PARTS) != 5:
        sys.exit(f"FAIL: {len(PARTS)} part files, 5 expected")
    rows, seen = {}, 0
    for p in PARTS:
        part = json.load(open(p))["rows"]
        seen += len(part)
        rows.update(part)
    _, want = expected_keys()
    if seen != len(rows) or set(rows) != want:
        sys.exit(f"FAIL keys: {seen} read, {len(rows)} unique, {len(want)} expected")
    cells = json.load(open("data/p2/manifest.json"))["cells"]
    random.seed(8)
    pick = (random.sample(sorted(k for k in rows if k.split("|")[2] == "200"), n_check // 2)
            + random.sample(sorted(k for k in rows if k.split("|")[2] == "400"), n_check - n_check // 2))
    bad = []
    for key in pick:
        name, s, n_t, rep = key.split("|")
        loc = one_row(name, int(rep), float(s), int(n_t), cells[name]["k_LDF"])
        ok = same(loc, rows[key])
        print(("ok   " if ok else "DIFF ") + key, flush=True)
        if not ok:
            bad.append(key)
    if bad:
        sys.exit(f"FAIL validation: {bad}")
    write_atomic({"source": "Kaggle E8 (kaggle_e8/), validated locally (p2_e8_merge.py)", "rows": rows}, ROWS)
    write_atomic(summarise(rows), SUMMARY)
    n_err = sum(any(k.endswith("|error") for k in r["disc"]) or "error" in r["ident"]
                or "error" in r.get("select", {}) for r in rows.values())
    print(f"MERGED {len(rows)} rows ({n_err} rows with an error), {n_check} sampled rows match -> {ROWS}, {SUMMARY}",
          flush=True)


if __name__ == "__main__":
    main()
