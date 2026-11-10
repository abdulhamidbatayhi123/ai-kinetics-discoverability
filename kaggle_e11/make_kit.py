"""Build the E11 Kaggle kit (code from the COMMITTED tree at HEAD, the 18 ground-truth fields from data/p2 with a
SHA-256 manifest) and the nine kernels. Hub rule: one private dataset slug per test; kit from git, never the
working directory; loaders accept the zip or the extracted tree (marker KIT_COMMIT).

    python kaggle_e11/make_kit.py     -> kaggle_e11/kit/ (dataset dir), kaggle_e11/k<N>/
"""
import hashlib
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.join(HERE, "kit")
SLUG = "abdulhamidbatayhi/p2-e11-fine-kit"
CODE = ["fetch_real_mof_data.py", "isotherm.py", "solver_fd.py", "p2_generate.py", "p2_observe.py",
        "p2_e6_modelselect.py", "p2_grid_o1.py", "p2_e11_fine.py"]


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True).stdout


def main():
    commit = git("rev-parse", "HEAD").decode().strip()
    assert not git("status", "--porcelain", "--", *CODE, "p2").strip(), "kit code has uncommitted changes"
    shutil.rmtree(KIT, ignore_errors=True)
    os.makedirs(os.path.join(KIT, "data", "p2"))
    files = CODE + sorted(p for p in git("ls-tree", "-r", "--name-only", "HEAD", "p2").decode().split() if p.endswith(".py"))
    for p in files:
        os.makedirs(os.path.dirname(os.path.join(KIT, p)) or KIT, exist_ok=True)
        open(os.path.join(KIT, p), "wb").write(git("show", f"HEAD:{p}"))
    cells = json.load(open(os.path.join(ROOT, "data", "p2", "manifest.json")))["cells"]
    names = sorted(n for n, c in cells.items() if c["law"] == "L1" and c["iso"] in ("langmuir", "step")
                   and c["pe_mult"] == 1.0 and not c.get("refined"))
    assert len(names) == 18, len(names)
    open(os.path.join(KIT, "data", "p2", "manifest.json"), "wb").write(git("show", "HEAD:data/p2/manifest.json"))
    for n in names:
        shutil.copy2(os.path.join(ROOT, "data", "p2", n + ".npz"), os.path.join(KIT, "data", "p2", n + ".npz"))
    man = {}
    for dp, _, fs in os.walk(KIT):
        for f in fs:
            p = os.path.join(dp, f)
            man[os.path.relpath(p, KIT).replace(os.sep, "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(man, open(os.path.join(KIT, "MANIFEST.json"), "w"), indent=0, sort_keys=True)
    open(os.path.join(KIT, "KIT_COMMIT"), "w").write(commit + "\n")
    json.dump({"title": "p2-e11-fine-kit", "id": SLUG, "licenses": [{"name": "CC0-1.0"}]},
              open(os.path.join(KIT, "dataset-metadata.json"), "w"))
    print("kit", commit[:7], len(man), "files")
    make_kernels(names)


RUN = r'''import glob, json, os, shutil, subprocess, sys, time, zipfile, hashlib
GROUPS = {groups!r}
PART = {part}
T0 = time.time()
kit = "/kaggle/working/kit"
marks = glob.glob("/kaggle/input/**/KIT_COMMIT", recursive=True)
zips = glob.glob("/kaggle/input/**/*.zip", recursive=True)
if marks:
    shutil.copytree(os.path.dirname(marks[0]), kit)
elif zips:
    zipfile.ZipFile(zips[0]).extractall(kit)
else:
    sys.exit("KIT NOT MOUNTED")
man = json.load(open(os.path.join(kit, "MANIFEST.json")))
bad = [p for p, h in man.items() if hashlib.sha256(open(os.path.join(kit, p), "rb").read()).hexdigest() != h]
if bad:
    sys.exit(f"MANIFEST MISMATCH {{bad[:5]}}")
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
           E11_DIR="/kaggle/working/fine")
procs = []
for w, g in enumerate(GROUPS):
    procs.append(subprocess.Popen([sys.executable, "-W", "ignore", "p2_e11_fine.py", "rows",
                                   f"/kaggle/working/w{{w}}.json", g], cwd=kit, env=env))
codes = [None] * len(procs)
while any(c is None for c in codes):                  # watchdog: stop before the 12 h limit, keep partial rows
    time.sleep(30)
    codes = [p.poll() for p in procs]
    if time.time() - T0 > 11 * 3600:
        for p in procs:
            if p.poll() is None:
                p.kill()
        codes = [p.wait() for p in procs]
rows, checks = {{}}, {{}}
for w in range(len(procs)):
    p = f"/kaggle/working/w{{w}}.json"
    if os.path.exists(p):
        d = json.load(open(p))
        rows.update(d["rows"])
        checks.update(d.get("checks", {{}}))
        os.remove(p)
json.dump({{"rows": rows, "checks": checks, "groups": GROUPS, "codes": codes,
           "kit_commit": open(os.path.join(kit, "KIT_COMMIT")).read().strip()}},
          open(f"/kaggle/working/e11_part{{PART}}.json", "w"))
print("DONE", len(rows), "rows", codes, round((time.time() - T0) / 3600, 2), "h", flush=True)
shutil.rmtree(kit, ignore_errors=True)
shutil.rmtree("/kaggle/working/fine", ignore_errors=True)
'''


def make_kernels(names):
    # heavy groups (high Da) spread first; four groups per kernel, one per worker
    groups = [f"{n}|{s}" for n in sorted(names, key=lambda n: -json.load(open(os.path.join(KIT, "data", "p2", "manifest.json")))["cells"][n]["Da"])
              for s in (0.005, 0.02)]
    assert len(groups) == 36
    n_k = 9
    for p in range(n_k):
        mine = groups[p::n_k]
        d = os.path.join(HERE, f"k{p}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "run.py"), "w").write(RUN.format(groups=mine, part=p))
        json.dump({"id": f"abdulhamidbatayhi/p2-e11-fine-{p}", "title": f"p2-e11-fine-{p}", "code_file": "run.py",
                   "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False,
                   "enable_internet": False, "dataset_sources": [SLUG], "competition_sources": [],
                   "kernel_sources": []}, open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)
        print("k", p, mine)


if __name__ == "__main__":
    main()
