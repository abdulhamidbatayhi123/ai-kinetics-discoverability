import glob, json, os, random, shutil, subprocess, sys, time, zipfile
GROUPS = ['langmuir_L1_pe1_da1e+03|0.02|0.0', 'langmuir_L1_pe1_da316|0.005|0.0', 'step_L1_pe1_da316|0.02|0.0', 'step_L1_pe1_da100|0.005|0.0', 'langmuir_L1_pe1_da31.6|0.02|0.0', 'langmuir_L1_pe1_da10|0.005|0.0', 'step_L1_pe1_da10|0.02|0.0', 'step_L1_pe1_da3.16|0.005|0.0', 'langmuir_L1_pe1_da1|0.02|0.0', 'langmuir_L1_pe1_da0.316|0.005|0.0', 'step_L1_pe1_da0.316|0.02|0.0', 'step_L1_pe1_da0.1|0.005|0.0']
REPS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
PART = 2
PSE_COMMIT = "7105caba63e754150dd3b160443984456ec99cd7"
TIME_LIMIT = 30
USE_CONST = False
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
VERSIONS = {p: _v(p) for p in ("deap", "symengine", "torch", "sympy", "numpy")}
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
NAMES = ['c', 'q', 'T', 'qstar']
PH = [f"x{i}" for i in range(len(NAMES))]
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
    syms = {sp.Symbol(p): n for p, n in zip(PH, NAMES)}
    back = {sp.Symbol(p): sp.Symbol(n) for p, n in zip(PH, NAMES)}
    co = {n: 0.0 for n in NAMES}
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
    best_loss, cur = {}, None
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
                         stage_config={"default": {"operators": OPS, "time_limit": TIME_LIMIT, "n_psrn_inputs": 5,
                                                   "n_sample_variables": 3}, "stages": [{}]})
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
    return {"success": bool(success_L1(co)), "support": sorted(k for k, v in co.items() if v != 0.0),
            "expr": expr, "sec": time.time() - t0, "front": front, "reward_pick": by_reward}

out = W + f"/e14_part{PART}.json"
res = {"rows": {}, "pse_commit": PSE_COMMIT, "time_limit": TIME_LIMIT, "groups": GROUPS, "versions": VERSIONS}
for g in GROUPS:
    name, s, e = g.split("|")
    for rep in REPS:
        key = f"{name}|{s}|{e}|{rep}|pse|strong"
        os.chdir(kit)                    # the observations load from the kit folder (data/p2)
        try:
            res["rows"][key] = one(name, float(s), float(e), rep)
        except Exception as ex:          # a failure, never dropped (A2)
            res["rows"][key] = {"success": False, "error": f"{type(ex).__name__}: {ex}"}
        os.chdir(kit)
        json.dump(res, open(out, "w"))
        print(key, res["rows"][key].get("success"), res["rows"][key].get("expr", res["rows"][key].get("error", ""))[:120],
              round(res["rows"][key].get("sec", 0), 1), flush=True)
print("DONE", len(res["rows"]), flush=True)
