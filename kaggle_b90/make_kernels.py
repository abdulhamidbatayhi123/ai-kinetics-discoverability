"""Write the six private Kaggle kernels of the B90 O1 identifiability rerun (one dataset, cells dealt
round-robin). Each kernel finds the kit (zip or auto-extracted folder) under /kaggle/input, copies it to
/kaggle/working/kit, runs o1ident_runner.py on its nine cells and leaves o1ident_part<N>.json.

    python kaggle_b90/make_kernels.py      -> kaggle_b90/k<N>/{run.py, kernel-metadata.json}
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
cells = sorted(n for n, c in json.load(open(os.path.join(HERE, "kit", "data", "p2", "manifest.json")))["cells"].items()
               if c["law"] == "L1" and c["iso"] != "langmuir_iso" and not c.get("refined"))
assert len(cells) == 54, len(cells)
N = 6
RUN = r'''import glob, os, shutil, subprocess, sys, zipfile
CELLS = {cells!r}
PART = {part}
kit = "/kaggle/working/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kitb90.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/o1ident_runner.py", recursive=True)][0]
        shutil.copytree(src, kit)
print("kit files:", len(os.listdir(kit)), flush=True)
out = f"/kaggle/working/o1ident_part{{PART}}.json"
r = subprocess.run([sys.executable, os.path.join(kit, "o1ident_runner.py"), kit, out] + CELLS)
sys.exit(r.returncode)
'''
for p in range(N):
    mine = cells[p::N]
    d = os.path.join(HERE, f"k{p}")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "run.py"), "w").write(RUN.format(cells=mine, part=p))
    json.dump({"id": f"abdulhamidbatayhi/p2-b90-o1ident-{p}", "title": f"p2-b90-o1ident-{p}", "code_file": "run.py",
               "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False,
               "enable_internet": False, "dataset_sources": ["abdulhamidbatayhi/p2-b90-o1ident-kit"],
               "competition_sources": [], "kernel_sources": []},
              open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
    print(p, len(mine), mine[:2])
