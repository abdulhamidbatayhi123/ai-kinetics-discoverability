"""Write the five private Kaggle kernels of E13 (information-matched sampling; EXPLORATORY_P2.md E13).

E13 runs E8's unchanged code (p2_e8_sampling.py rows, from the existing E8 kit dataset) at the grid's 200 times
with the noise SD per sample divided by sqrt(10), so each run carries about the information of E11's 1,996 times
at the original noise. 36 (cell, sigma, n_t) groups are dealt round-robin over five kernels; each kernel runs four
workers and merges their parts into e13_part<N>.json.

    python kaggle_e13/make_kernels.py      -> kaggle_e13/k<N>/{run.py, kernel-metadata.json}
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIGMAS = (0.005 / math.sqrt(10), 0.02 / math.sqrt(10))      # 0.0015811388300841897, 0.006324555320336759
N_T = 200
cells = sorted(n for n, c in json.load(open(os.path.join(ROOT, "data", "p2", "manifest.json")))["cells"].items()
               if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined"))
assert len(cells) == 18, len(cells)
groups = [f"{n}|{s!r}|{N_T}" for n in sorted(cells, key=lambda n: -float(n.split("_da")[1]))
          for s in SIGMAS]                                     # high Da first: the slower profiles start early
N = 5
RUN = r'''import glob, json, os, shutil, subprocess, sys, zipfile
GROUPS = {groups!r}
PART = {part}
kit = "/kaggle/working/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kite8.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/p2_e8_sampling.py", recursive=True)][0]
        shutil.copytree(src, kit)
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
procs = []
for w in range(4):
    mine = GROUPS[w::4]
    if mine:
        procs.append(subprocess.Popen([sys.executable, "-W", "ignore", "p2_e8_sampling.py", "rows",
                                       f"/kaggle/working/w{{w}}.json"] + mine, cwd=kit, env=env))
codes = [p.wait() for p in procs]
rows = {{}}
for w in range(4):
    p = f"/kaggle/working/w{{w}}.json"
    if os.path.exists(p):
        rows.update(json.load(open(p))["rows"])
        os.remove(p)
json.dump({{"rows": rows, "groups": GROUPS, "codes": codes}}, open(f"/kaggle/working/e13_part{{PART}}.json", "w"))
print("DONE", len(rows), "rows", codes, flush=True)
shutil.rmtree(kit, ignore_errors=True)
sys.exit(max(codes))
'''

if __name__ == "__main__":
    for p in range(N):
        mine = groups[p::N]
        d = os.path.join(HERE, f"k{p}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "run.py"), "w", newline="\n").write(RUN.format(groups=mine, part=p))
        json.dump({"id": f"abdulhamidbatayhi/p2-e13-infomatched-{p}", "title": f"p2-e13-infomatched-{p}",
                   "code_file": "run.py", "language": "python", "kernel_type": "script", "is_private": True,
                   "enable_gpu": False, "enable_internet": False,
                   "dataset_sources": ["abdulhamidbatayhi/p2-e8-sampling-kit"],
                   "competition_sources": [], "kernel_sources": []},
                  open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
        print(p, len(mine), mine[:2])
