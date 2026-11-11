"""PREREG_P2 s.5 "S1 on the map": the closest prior study's Damkohler number under this study's definition.

S1 = Santana et al., Chem. Eng. Sci. 282, 119223 (2023), doi:10.1016/j.ces.2023.119223; inputs read from
the arXiv version of record text, arXiv:2303.13555v3 (read live 2026-11-11):
- Table 1 (training set): v = 5.1e-1 dm/min (interstitial velocity), L = 2.0 dm, Pe = 21.0, eps = 0.5;
  feed c_in = 5.5 mg/L; observation time 110 min; sampling 0.5 min^-1; outlet breakthrough only;
  5 % Gaussian noise (Sec. 2).
- Appendix A: dc/dt* = -(1-eps)/eps g(q, q*) tau_s - dc/dx* + (1/Pe) d2c/dx*2, dq/dt* = g tau_s,
  tau_s = L/v; g_LDF = 0.22 (q* - q); Langmuir q* = 55.54 x 1.8 c / (1 + 1.8 c).
The model is written with q and c in the same balance with the factor (1-eps)/eps and no density, so
the stoichiometric time follows from those equations as written:
    t_stoich = tau_s [1 + (1-eps)/eps q*(c_in)/c_in],   Da = k t_stoich,   residence form k tau_s.
k = 0.22 is per unit of t, which is in minutes (v in dm/min). This study's definition is the same
(solver_fd.stoichiometric_time: capacity L / (v_superficial c_in) with capacity
(1-eps) rho q* + eps c_in), which equals the expression above with v interstitial.

    python p2_s1_anchor.py  ->  results/p2_s1_anchor.json
"""
import json

from p2.io_utils import write_atomic

V_DM_MIN, L_DM, EPS, C_IN, K_PER_MIN = 0.51, 2.0, 0.5, 5.5, 0.22
QMAX, B = 55.54, 1.8
T_OBS_MIN, F_SAMPLE_PER_MIN, NOISE = 110.0, 0.5, 0.05


def main():
    tau = L_DM / V_DM_MIN
    qstar = QMAX * B * C_IN / (1 + B * C_IN)
    t_st = tau * (1 + (1 - EPS) / EPS * qstar / C_IN)
    out = {"source": "Santana et al. 2023, doi:10.1016/j.ces.2023.119223; arXiv:2303.13555v3 Table 1, Appendix A",
           "tau_s_min": tau, "qstar_cin_mg_g": qstar, "t_stoich_min": t_st,
           "Da": K_PER_MIN * t_st, "Da_residence": K_PER_MIN * tau,
           "observation_horizon_over_t_stoich": T_OBS_MIN / t_st,
           "n_samples": int(T_OBS_MIN * F_SAMPLE_PER_MIN), "noise": NOISE, "observation": "outlet only (O3-like)",
           "pe": 21.0, "isotherm_given_exactly": True}
    # Their Sips case (Appendix A, eq. A.5: q* = 55.54 x 1.8 c^1.5 / (1 + 1.8 c^1.5)), same column and feed.
    qs_sips = QMAX * B * C_IN ** 1.5 / (1 + B * C_IN ** 1.5)
    t_sips = tau * (1 + (1 - EPS) / EPS * qs_sips / C_IN)
    out.update({"sips_qstar_cin_mg_g": qs_sips, "sips_t_stoich_min": t_sips, "sips_Da": K_PER_MIN * t_sips,
                "readouts": {"langmuir_ldf_sparse_and_symbolic": "-0.535 - 0.225 q + 0.234 q* (Tables 4, 5)",
                             "sips_ldf_symbolic": "0.198 q* - 0.200 q (Table 5)",
                             "sips_ldf_sparse": "-0.275 - 0.210 q + 0.214 q* (Table 4)"}})
    write_atomic(out, "results/p2_s1_anchor.json")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
