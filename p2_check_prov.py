"""Check that every figure in the paper was drawn from the current scripts and results.

Each figure script writes paper2/<figure>.prov.json beside the PDF and PNG, with SHA-256 hashes of the style
file (p2_figstyle.py), the script and every input file. This script recomputes those hashes and lists any
figure whose script, style file or inputs changed after it was drawn. Text files are hashed with line endings
normalised, so the result does not depend on how the repository was checked out.

    python p2_check_prov.py            # every paper2/*.prov.json; exit code 1 if any figure is stale
    python p2_check_prov.py STEM ...   # selected figures, e.g. paper2/fig_p2_map
"""
import glob
import sys

from p2_figstyle import check_prov


def main(stems):
    paths = [s + ".prov.json" for s in stems] if stems else sorted(glob.glob("paper2/*.prov.json"))
    stale = 0
    for p in paths:
        bad = check_prov(p)
        print(("OK     " if not bad else "STALE  ") + p + ("" if not bad else ": " + "; ".join(bad)))
        stale += bool(bad)
    print(f"{len(paths) - stale} of {len(paths)} figures match their scripts and inputs")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
