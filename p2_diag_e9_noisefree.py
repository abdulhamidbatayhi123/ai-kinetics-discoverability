"""Diagnostic (not reported unless declared): E6's choice on fully noise-free O1 data."""
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from p2_observe import observe
from p2_e6_modelselect import select

cells = json.load(open("data/p2/manifest.json"))["cells"]
for n in ["langmuir_L1_pe1_da31.6", "langmuir_L1_pe1_da100", "step_L1_pe1_da100", "langmuir_L1_pe1_da1e+03"]:
    o = observe(n, 15, 0.0, 0.0, "O1")
    ch = o["channels"]
    sq = 1e-4 * float(np.ptp(ch["q"]))
    b, f = select(o["t"], list(ch["c"]), list(ch["q"]), o["qstar_meas"], sq, Ts=list(ch["T"]))
    print(n, b, {k: (round(v["ll"], 1), round(v["k_hat"] / cells[n]["k_LDF"], 3)) for k, v in f.items()}, flush=True)
