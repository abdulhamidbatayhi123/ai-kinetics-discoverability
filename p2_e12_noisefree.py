"""E12/E12b diagnostic made after both positive controls failed (not declared in advance; labelled so in the paper):
discovery on the NOISE-FREE trajectories with the exact equilibrium constant, at every Da, for both feeds. It asks
whether the failure at 0.5 % noise is structural (the methods cannot recover the law even from exact data) or caused
by noise (the main study's mechanism). Same library, methods and success rule as p2_e12_reaction.py.

    python p2_e12_noisefree.py  ->  results/p2_e12_noisefree.json
"""
import json
import subprocess
import sys

from p2.io_utils import write_atomic


def run(variant_b):
    sys.argv = ["p2_e12_reaction.py"] + (["--variant-b"] if variant_b else [])
    import importlib
    import p2_e12_reaction as E
    E = importlib.reload(E)
    out = {}
    for da in E.DAS:
        truth = E.solve(da / E.TAU, E.K_true)
        out[f"{da:g}"] = E.discover(truth, E.K_true)
    return out, E.B_IN


def main():
    res = {"commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    for tag, vb in (("E12", False), ("E12b", True)):
        rows, b_in = run(vb)
        res[tag] = {"B_in": b_in, "by_da": rows,
                    "any_method_succeeds_at_every_da": all(any(v.values()) for v in rows.values()),
                    "best_subset_weak_succeeds_at_every_da": all(v["best_subset|weak"] for v in rows.values())}
    write_atomic(res, "results/p2_e12_noisefree.json")
    print(json.dumps({k: (v if k == "commit" else {a: b for a, b in v.items() if a != "by_da"}) for k, v in res.items()},
                     indent=1))


if __name__ == "__main__":
    main()
