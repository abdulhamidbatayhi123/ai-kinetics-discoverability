import glob, os, shutil, subprocess, sys, zipfile
CELLS = ['langmuir_L1_pe0.2_da1', 'langmuir_L1_pe0.2_da316', 'langmuir_L1_pe1_da1e+03', 'langmuir_L1_pe5_da1', 'langmuir_L1_pe5_da316', 'step_L1_pe0.2_da1e+03', 'step_L1_pe1_da1', 'step_L1_pe1_da316', 'step_L1_pe5_da1e+03']
PART = 2
kit = "/kaggle/working/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kitb90.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/o1ident_runner.py", recursive=True)][0]
        shutil.copytree(src, kit)
print("kit files:", len(os.listdir(kit)), flush=True)
out = f"/kaggle/working/o1ident_part{PART}.json"
r = subprocess.run([sys.executable, os.path.join(kit, "o1ident_runner.py"), kit, out] + CELLS)
sys.exit(r.returncode)
