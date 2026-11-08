import glob, os, shutil, subprocess, sys, zipfile
GROUPS = ['langmuir_L1_pe1_da0.1|0.005|0.02', 'langmuir_L1_pe1_da0.316|0.02|0.0', 'langmuir_L1_pe1_da1|0.02|0.02', 'langmuir_L1_pe1_da100|0.005|0.0', 'langmuir_L1_pe1_da1e+03|0.005|0.02', 'langmuir_L1_pe1_da3.16|0.02|0.0', 'langmuir_L1_pe1_da31.6|0.02|0.02', 'step_L1_pe1_da0.1|0.005|0.0', 'step_L1_pe1_da0.316|0.005|0.02', 'step_L1_pe1_da1|0.02|0.0', 'step_L1_pe1_da10|0.02|0.02', 'step_L1_pe1_da1e+03|0.005|0.0', 'step_L1_pe1_da3.16|0.005|0.02', 'step_L1_pe1_da31.6|0.02|0.0', 'step_L1_pe1_da316|0.02|0.02']
PART = 1
kit = "/kaggle/working/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kite6.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/e6_runner.py", recursive=True)][0]
        shutil.copytree(src, kit)
out = f"/kaggle/working/e6_part{PART}.json"
r = subprocess.run([sys.executable, os.path.join(kit, "e6_runner.py"), kit, out] + GROUPS)
shutil.rmtree(kit, ignore_errors=True)        # leave only the part file and the log as output
sys.exit(r.returncode)
