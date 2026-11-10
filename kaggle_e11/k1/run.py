import glob, json, os, shutil, subprocess, sys, time, zipfile, hashlib
GROUPS = ['langmuir_L1_pe1_da1e+03|0.02', 'step_L1_pe1_da100|0.005', 'step_L1_pe1_da10|0.02', 'langmuir_L1_pe1_da0.316|0.005']
PART = 1
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
    sys.exit(f"MANIFEST MISMATCH {bad[:5]}")
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
           E11_DIR="/kaggle/working/fine")
procs = []
for w, g in enumerate(GROUPS):
    procs.append(subprocess.Popen([sys.executable, "-W", "ignore", "p2_e11_fine.py", "rows",
                                   f"/kaggle/working/w{w}.json", g], cwd=kit, env=env))
codes = [None] * len(procs)
while any(c is None for c in codes):                  # watchdog: stop before the 12 h limit, keep partial rows
    time.sleep(30)
    codes = [p.poll() for p in procs]
    if time.time() - T0 > 11 * 3600:
        for p in procs:
            if p.poll() is None:
                p.kill()
        codes = [p.wait() for p in procs]
rows, checks = {}, {}
for w in range(len(procs)):
    p = f"/kaggle/working/w{w}.json"
    if os.path.exists(p):
        d = json.load(open(p))
        rows.update(d["rows"])
        checks.update(d.get("checks", {}))
        os.remove(p)
json.dump({"rows": rows, "checks": checks, "groups": GROUPS, "codes": codes,
           "kit_commit": open(os.path.join(kit, "KIT_COMMIT")).read().strip()},
          open(f"/kaggle/working/e11_part{PART}.json", "w"))
print("DONE", len(rows), "rows", codes, round((time.time() - T0) / 3600, 2), "h", flush=True)
shutil.rmtree(kit, ignore_errors=True)
shutil.rmtree("/kaggle/working/fine", ignore_errors=True)
