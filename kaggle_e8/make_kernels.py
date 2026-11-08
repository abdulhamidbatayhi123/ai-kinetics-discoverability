"""Write the five private Kaggle kernels of E8 (sampling rate): 72 (cell, sigma, n_t) groups dealt
round-robin; each kernel runs four workers of p2_e8_sampling.py rows and merges their parts.

    python kaggle_e8/make_kernels.py      -> kaggle_e8/k<N>/{run.py, kernel-metadata.json}
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
cells = sorted(n for n, c in json.load(open(os.path.join(HERE, "kit", "data", "p2", "manifest.json")))["cells"].items()
               if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined"))
assert len(cells) == 18, len(cells)
# heavy groups (n_t = 400, high Da) spread first
groups = [f"{n}|{s}|{t}" for t in (400, 200) for n in cells for s in (0.005, 0.02)]
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
json.dump({{"rows": rows, "groups": GROUPS, "codes": codes}}, open(f"/kaggle/working/e8_part{{PART}}.json", "w"))
print("DONE", len(rows), "rows", codes, flush=True)
shutil.rmtree(kit, ignore_errors=True)
sys.exit(max(codes))
'''
for p in range(N):
    mine = groups[p::N]
    d = os.path.join(HERE, f"k{p}")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "run.py"), "w").write(RUN.format(groups=mine, part=p))
    json.dump({"id": f"abdulhamidbatayhi/p2-e8-sampling-{p}", "title": f"p2-e8-sampling-{p}", "code_file": "run.py",
               "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False,
               "enable_internet": False, "dataset_sources": ["abdulhamidbatayhi/p2-e8-sampling-kit"],
               "competition_sources": [], "kernel_sources": []},
              open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
    print(p, len(mine))
