import glob, json, os, shutil, subprocess, sys, zipfile
GROUPS = ['langmuir_L1_pe1_da0.316|0.02|400', 'langmuir_L1_pe1_da100|0.005|400', 'langmuir_L1_pe1_da3.16|0.02|400', 'step_L1_pe1_da0.1|0.005|400', 'step_L1_pe1_da1|0.02|400', 'step_L1_pe1_da1e+03|0.005|400', 'step_L1_pe1_da31.6|0.02|400', 'langmuir_L1_pe1_da0.316|0.005|200', 'langmuir_L1_pe1_da10|0.02|200', 'langmuir_L1_pe1_da3.16|0.005|200', 'langmuir_L1_pe1_da316|0.02|200', 'step_L1_pe1_da1|0.005|200', 'step_L1_pe1_da100|0.02|200', 'step_L1_pe1_da31.6|0.005|200']
PART = 3
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
                                       f"/kaggle/working/w{w}.json"] + mine, cwd=kit, env=env))
codes = [p.wait() for p in procs]
rows = {}
for w in range(4):
    p = f"/kaggle/working/w{w}.json"
    if os.path.exists(p):
        rows.update(json.load(open(p))["rows"])
        os.remove(p)
json.dump({"rows": rows, "groups": GROUPS, "codes": codes}, open(f"/kaggle/working/e8_part{PART}.json", "w"))
print("DONE", len(rows), "rows", codes, flush=True)
shutil.rmtree(kit, ignore_errors=True)
sys.exit(max(codes))
