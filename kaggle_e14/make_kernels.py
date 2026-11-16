"""Write the Kaggle GPU kernels of E14 (PSE on M7's subgrid; EXPLORATORY_P2.md E14).

Each kernel copies the E8 kit (dataset p2-e8-sampling-kit: the fields, p2_observe.py and the p2 package), clones
PSE (github.com/intell-sci-comput/PSE) at the pinned commit, generates PSE's mask for the declared operators, and fits
its groups row by row. Final settings (ledger E14, pilots 3 to 5): inputs are the raw variables c, q, T and q* at the
observed values, stacked over the 20 probes (pilot 3: with M7's Lib-B columns PSE returned a full linear combination); target the Savitzky-Golay derivative of q (p2.features.derivative), multiplied by t_stoich so that the
coefficients are of order Da (a constant factor, which changes neither the law's terms nor the coefficient ratio the
success rule checks); M7's strict bridge (SymPy expansion, any monomial that is not a single feature is extra support)
and p2.metric.success_L1.

    python kaggle_e14/make_kernels.py           -> kaggle_e14/k<N>/{run.py, kernel-metadata.json}
    python kaggle_e14/make_kernels.py --pilot   -> kaggle_e14/kpilot/ (three timing rows, not reported)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PSE_COMMIT = "7105caba63e754150dd3b160443984456ec99cd7"
SIGMAS, EPSS, REPS = (0.005, 0.02), (0.0, 0.02), range(15, 30)
TIME_LIMIT = 30
FEATS = ["c", "q", "T", "qstar"]
USE_CONST = False   # PSE's default; with constants every expression carried an intercept (ledger E14, pilot 5)
# FEATS: raw variables; PSE builds products itself (ledger E14, pilot 3)
cells = sorted(n for n, c in json.load(open(os.path.join(ROOT, "data", "p2", "manifest.json")))["cells"].items()
               if c["law"] == "L1" and c["iso"] in ("langmuir", "step") and c["pe_mult"] == 1.0 and not c.get("refined"))
assert len(cells) == 18, len(cells)
groups = [f"{n}|{s}|{e}" for n in sorted(cells, key=lambda n: -float(n.split("_da")[1])) for s in SIGMAS for e in EPSS]
N = 6

RUN = r'''import glob, json, os, random, shutil, subprocess, sys, time, zipfile
GROUPS = {groups!r}
REPS = {reps!r}
PART = {part!r}
PSE_COMMIT = "{commit}"
TIME_LIMIT = {time_limit}
USE_CONST = {use_const}
W = "/kaggle/working"
kit = W + "/kit"
if not os.path.exists(kit):
    zips = glob.glob("/kaggle/input/**/kite8.zip", recursive=True)
    if zips:
        zipfile.ZipFile(zips[0]).extractall(kit)
    else:
        src = [os.path.dirname(p) for p in glob.glob("/kaggle/input/**/p2_e8_sampling.py", recursive=True)][0]
        shutil.copytree(src, kit)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "deap", "symengine", "click", "pyyaml"],
               check=True)   # PSE pins deap 1.3.3 / symengine 0.11.0, which have no wheels for Kaggle's Python 3.13
from importlib.metadata import version as _v
VERSIONS = {{p: _v(p) for p in ("deap", "symengine", "torch", "sympy", "numpy")}}
print("versions", VERSIONS, flush=True)
pse = W + "/PSE"
if not os.path.exists(pse):
    subprocess.run(["git", "clone", "-q", "https://github.com/intell-sci-comput/PSE.git", pse], check=True)
    subprocess.run(["git", "-C", pse, "checkout", "-q", PSE_COMMIT], check=True)
OPS = ["Add", "Mul", "Sub", "Identity"]
os.chdir(pse)
mask = "dr_mask/3_5_[" + "_".join(OPS) + "]_mask.npy"
if not os.path.exists(mask):
    subprocess.run([sys.executable, "utils/gen_dr_mask.py", "--n_symbol_layers=3", "--n_inputs=5",
                    "--ops=" + str(OPS).replace(" ", "")], check=True)
sys.path.insert(0, pse)
sys.path.insert(1, kit)
import numpy as np
import sympy as sp
import torch
from model.regressor import PSRN_Regressor
os.chdir(kit)
from p2_observe import observe
from p2.features import derivative, lib_b
from p2.metric import success_L1
cells = json.load(open("data/p2/manifest.json"))["cells"]
NAMES = {names!r}
PH = [f"x{{i}}" for i in range(len(NAMES))]
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
import yaml
TG_CONFIG = yaml.safe_load(open(pse + "/token_generator_config.yaml"))
TG_CONFIG["GP"]["base"]["tokens"] = [o for o in OPS if o != "Identity"]   # the declared operators, as for PSRN
TG_CONFIG["GP"]["base"]["has_const"] = USE_CONST
TG_CONFIG["GP"]["base"]["verbose"] = False
print("token generator", TG_CONFIG["GP"]["base"], flush=True)
print("device", dev, flush=True)

def bridge(expr_str):
    expr = sp.expand(sp.sympify(expr_str))
    syms = {{sp.Symbol(p): n for p, n in zip(PH, NAMES)}}
    back = {{sp.Symbol(p): sp.Symbol(n) for p, n in zip(PH, NAMES)}}
    co = {{n: 0.0 for n in NAMES}}
    for term in sp.Add.make_args(expr):
        c, rest = term.as_coeff_Mul()
        if rest in syms and rest.is_Symbol:
            co[syms[rest]] += float(c)
        else:
            key = str((term if rest == 1 else rest).xreplace(back))
            co[key] = co.get(key, 0.0) + float(c if rest != 1 else term)
    return co, str(expr.xreplace(back))

def knee(front):
    """M7's selection rule (PySR's model_selection='best') applied to PSE's Pareto front: among expressions whose loss
    is within 1.5 times the smallest, the one with the largest score -d ln(loss) / d complexity against the next
    simpler expression on the front."""
    pts = sorted(front, key=lambda x: (x[3], x[2]))
    best_loss, cur = {{}}, None
    for e, r, l, c in pts:                      # keep the lowest loss at each complexity
        if c not in best_loss or l < best_loss[c][2]:
            best_loss[c] = (e, r, l, c)
    pf = [best_loss[c] for c in sorted(best_loss)]
    pf2 = []
    for x in pf:                                # a Pareto front: loss falls with complexity
        if not pf2 or x[2] < pf2[-1][2]:
            pf2.append(x)
    lmin = min(x[2] for x in pf2)
    tiny = 1e-300
    scores = [0.0] + [-(np.log(max(pf2[i][2], tiny)) - np.log(max(pf2[i - 1][2], tiny))) / max(pf2[i][3] - pf2[i - 1][3], 1e-12)
                      for i in range(1, len(pf2))]
    ok = [i for i in range(len(pf2)) if pf2[i][2] <= 1.5 * lmin]
    return pf2[max(ok, key=lambda i: scores[i])]

def one(name, sigma, eps, rep):
    obs = observe(name, rep, sigma, eps, "O1")
    ch = obs["channels"]
    rows = []
    for j in range(ch["q"].shape[0]):
        c, q, T = ch["c"][j], ch["q"][j], ch["T"][j]
        F = lib_b(c, q, T, obs["qstar_meas"](c, T))
        rows.append((np.column_stack([F[n] for n in NAMES]), derivative(q, obs["t"])))   # NAMES: see make_kernels.FEATS
    X = np.concatenate([r[0] for r in rows])
    y = np.concatenate([r[1] for r in rows]) * cells[name]["t_stoich_s"]
    random.seed(rep); np.random.seed(rep); torch.manual_seed(rep)
    os.chdir(pse)                        # PSE resolves its own modules and configs from its folder
    reg = PSRN_Regressor(variables=PH, dr_mask_dir=pse + "/dr_mask", use_const=USE_CONST, device=str(dev),
                         token_generator="GP", token_generator_config=TG_CONFIG,
                         stage_config={{"default": {{"operators": OPS, "time_limit": TIME_LIMIT, "n_psrn_inputs": 5,
                                                   "n_sample_variables": 3}}, "stages": [{{}}]}})
    Xt = torch.from_numpy(X).to(dev).to(torch.float32)
    yt = torch.from_numpy(y.reshape(-1, 1)).to(dev).to(torch.float32)
    t0 = time.time()
    reg.fit(Xt, yt, n_down_sample=100, use_threshold=False, threshold=1e-20, probe=None, prun_const=True,
            prun_ndigit=6, top_k=10)
    front = [(str(e), float(r), float(l), float(c)) for e, r, l, c in reg.display_expr_table(sort_by="mse")]
    os.chdir(kit)
    pick = knee(front)
    co, expr = bridge(pick[0])
    by_reward = max(front, key=lambda x: x[1])[0]
    return {{"success": bool(success_L1(co)), "support": sorted(k for k, v in co.items() if v != 0.0),
            "expr": expr, "sec": time.time() - t0, "front": front, "reward_pick": by_reward}}

out = W + f"/e14_part{{PART}}.json"
res = {{"rows": {{}}, "pse_commit": PSE_COMMIT, "time_limit": TIME_LIMIT, "groups": GROUPS, "versions": VERSIONS}}
for g in GROUPS:
    name, s, e = g.split("|")
    for rep in REPS:
        key = f"{{name}}|{{s}}|{{e}}|{{rep}}|pse|strong"
        os.chdir(kit)                    # the observations load from the kit folder (data/p2)
        try:
            res["rows"][key] = one(name, float(s), float(e), rep)
        except Exception as ex:          # a failure, never dropped (A2)
            res["rows"][key] = {{"success": False, "error": f"{{type(ex).__name__}}: {{ex}}"}}
        os.chdir(kit)
        json.dump(res, open(out, "w"))
        print(key, res["rows"][key].get("success"), res["rows"][key].get("expr", res["rows"][key].get("error", ""))[:120],
              round(res["rows"][key].get("sec", 0), 1), flush=True)
print("DONE", len(res["rows"]), flush=True)
'''


def write(d, slug, groups_, reps, part):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "run.py"), "w", newline="\n").write(
        RUN.format(groups=groups_, reps=list(reps), part=part, commit=PSE_COMMIT, time_limit=TIME_LIMIT, names=FEATS, use_const=USE_CONST))
    json.dump({"id": f"abdulhamidbatayhi/{slug}", "title": slug, "code_file": "run.py", "language": "python",
               "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
               "dataset_sources": ["abdulhamidbatayhi/p2-e8-sampling-kit"], "competition_sources": [],
               "kernel_sources": []}, open(os.path.join(d, "kernel-metadata.json"), "w"), indent=1)


if __name__ == "__main__":
    if "--pilot" in sys.argv:
        pg = ["langmuir_L1_pe1_da1|0.005|0.0", "langmuir_L1_pe1_da31.6|0.02|0.02", "step_L1_pe1_da3.16|0.005|0.0"]
        write(os.path.join(HERE, "kpilot"), "p2-e14-pse-pilot", pg, [15], "pilot")
        print("pilot written:", pg)
    else:
        for p in range(N):
            write(os.path.join(HERE, f"k{p}"), f"p2-e14-pse-{p}", groups[p::N], REPS, p)
            print(p, len(groups[p::N]))
