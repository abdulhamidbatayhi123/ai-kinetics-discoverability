"""Diagnostic for E2 (not a result): does M8's KAN train on grid-scale data?

Runs M8's exact fit on the E2 smoke cell and prints the per-step training loss, the input
scales and whether the gradients are finite. kan_symbolic itself is not changed.

    python p2_e2_diag.py
"""
import json
import tempfile

import numpy as np

from p2.features import derivative
from p2_observe import observe

man = json.load(open("data/p2/manifest.json"))["cells"]
name = min((n for n, r in man.items() if r["iso"] == "langmuir" and r["law"] == "L1"
            and r["pe_mult"] == 1.0 and not r.get("refined")), key=lambda n: abs(np.log(man[n]["Da"])))
obs = observe(name, 0, 0.02, 0.02, "O1")
V = {"c": np.concatenate(obs["channels"]["c"]), "q": np.concatenate(obs["channels"]["q"]),
     "T": np.concatenate(obs["channels"]["T"]),
     "qstar": np.concatenate([obs["qstar_meas"](c, T) for c, T in
                              zip(obs["channels"]["c"], obs["channels"]["T"])])}
y = np.concatenate([derivative(q, obs["t"]) for q in obs["channels"]["q"]])
print("cell", name, "n", y.size, "k_true", man[name]["k_LDF"])
for n, v in V.items():
    print(f"  {n:6s} mean {v.mean():.4g} sd {v.std():.4g} finite {np.isfinite(v).all()}")
print(f"  y      mean {y.mean():.4g} sd {y.std():.4g} finite {np.isfinite(y).all()}")
# least-squares check: how much of y does the true law explain on these data?
A = np.column_stack([V["qstar"] - V["q"]])
kk, *_ = np.linalg.lstsq(A, y, rcond=None)
r = y - A @ kk
print(f"  LS k(q*-q): k_hat {kk[0]:.4g}, R^2 {1 - r.var() / y.var():.4f}, "
      f"normalised MSE {np.mean(r ** 2) / y.var():.4f}")

import torch  # noqa: E402
from kan import KAN  # noqa: E402
names = list(V)
X0 = np.column_stack([V[n] for n in names]).astype(float)
mu, sd = X0.mean(0), X0.std(0)
sd[sd == 0] = 1.0
ys = float(np.std(y)) or 1.0
torch.manual_seed(0)
X = torch.tensor((X0 - mu) / sd, dtype=torch.float32)
Y = torch.tensor((y / ys)[:, None], dtype=torch.float32)
ds = {"train_input": X, "train_label": Y, "test_input": X, "test_label": Y}
model = KAN(width=[len(names), 1], grid=5, k=3, seed=0, auto_save=False,
            ckpt_path=tempfile.mkdtemp(prefix="p2kan_"), device="cpu")
out = model(X)
loss0 = torch.mean((out - Y) ** 2)
loss0.backward()
g = [p.grad for p in model.parameters() if p.grad is not None]
print("initial MSE", float(loss0), "grads finite", all(torch.isfinite(t).all().item() for t in g),
      "max |grad|", max(float(t.abs().max()) for t in g))
res = model.fit(ds, opt="LBFGS", steps=100, lamb=1e-3, log=101)
tl = res["train_loss"]
print("train_loss (RMSE) at steps 0,1,2,5,10,50,99:",
      [round(float(tl[i]), 5) for i in (0, 1, 2, 5, 10, 50, 99)])
print("reg at 0, 99:", round(float(res["reg"][0]), 5), round(float(res["reg"][99]), 5))
