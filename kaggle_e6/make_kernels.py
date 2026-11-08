"""Write the five private Kaggle kernels of the E6 rerun (after B91): 72 (cell, sigma, eps) groups
of the E6 subgrid dealt round-robin. Each kernel unpacks the kit and runs e6_runner.py.

    python kaggle_e6/make_kernels.py      -> kaggle_e6/k<N>/{run.py, kernel-metadata.json}
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
cells = sorted(n for n, c in json.load(open(os.path.join(HERE, "kit", "data", "p2", "manifest.json")))["cells"].items()
               if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined"))
assert len(cells) == 18, len(cells)
groups = [f"{n}|{s}|{e}" for n in cells for s in (0.005, 0.02) for e in (0.0, 0.02)]
N = 5
RUN = r'''import glob, os, shutil, subprocess, sys, zipfile
GROUPS = {groups!r}
PART = {part}
kit = "/kaggle/working/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kite6.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/e6_runner.py", recursive=True)][0]
        shutil.copytree(src, kit)
out = f"/kaggle/working/e6_part{{PART}}.json"
r = subprocess.run([sys.executable, os.path.join(kit, "e6_runner.py"), kit, out] + GROUPS)
shutil.rmtree(kit, ignore_errors=True)        # leave only the part file and the log as output
sys.exit(r.returncode)
'''
for p in range(N):
    mine = groups[p::N]
    d = os.path.join(HERE, f"k{p}")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "run.py"), "w").write(RUN.format(groups=mine, part=p))
    json.dump({"id": f"abdulhamidbatayhi/p2-e6-select-{p}", "title": f"p2-e6-select-{p}", "code_file": "run.py",
               "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False,
               "enable_internet": False, "dataset_sources": ["abdulhamidbatayhi/p2-e6-select-kit"],
               "competition_sources": [], "kernel_sources": []},
              open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
    print(p, len(mine))
