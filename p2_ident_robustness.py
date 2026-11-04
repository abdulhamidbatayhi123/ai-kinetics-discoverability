"""Descriptive checks on the corrected O1 identifiability (not a verdict, no rule changed).

1. Estimator accuracy with exact data: the median of sqrt(lo * hi) / k over the estimation
   replicates at sigma = eps = 0, per isotherm, Pe level and Da. Shows where the O1 profile
   (200 observation times) is accurate and where it is limited by time resolution.
2. H2b without the two highest Da levels: for each slice with a verdict, the smallest
   P(identifiable) at Da <= 31.6 and the gap from Da*_disc to the highest Da <= 100 at which
   P(identifiable) >= 0.5. If that gap exceeds 0.25 decade everywhere, the verdict does not
   rest on the levels where the estimator is resolution-limited.
3. The no-verdict H2b slices, classified by whether each probability stays above 50 %, stays
   below it, or straddles it without a logistic crossing (non-monotone in Da).

Reads results/p2_extra_o1ident.json, data/p2/manifest.json, results/p2_verdicts.json,
results/p2_figdata.json; writes results/p2_ident_robustness.json.

    python p2_ident_robustness.py
"""
import collections
import json
import math
import statistics

from p2.io_utils import write_atomic

N_SEL = 15
DAS = ("0.1", "0.316", "1", "3.16", "10", "31.6", "100", "316", "1e+03")


def accuracy():
    rows = json.load(open("results/p2_extra_o1ident.json"))["rows"]
    man = json.load(open("data/p2/manifest.json"))["cells"]
    out = {}
    for iso in ("langmuir", "step"):
        for pe in ("0.2", "1", "5"):
            for da in DAS:
                cell = f"{iso}_L1_pe{pe}_da{da}"
                k0 = man[cell]["k_LDF"]
                mids = [math.sqrt(v["interval"]["lo"] * v["interval"]["hi"]) / k0
                        for key, v in rows.items()
                        if key.startswith(cell + "|0.0|0.0|") and int(key.split("|")[3]) >= N_SEL
                        and "interval" in v]
                out[cell] = statistics.median(mids) if mids else None
    return out


def without_top_levels(verdicts, fig):
    out = {}
    for key, s in verdicts.items():
        if s["gap_decades"] is None:
            continue
        ident = fig[key]["ident"]
        low = min(a / n for da, a, n in ident if da <= 31.7)
        last_ok = max(da for da, a, n in ident if da <= 101 and a / n >= 0.5)
        out[key] = {"min_p_ident_da_le_31.6": low, "highest_da_le_100_p_ge_0.5": last_ok,
                    "gap_lower_bound_decades": math.log10(last_ok / s["da_disc"])}
    return out


def classify_no_verdict(verdicts, fig):
    def kind(levels):
        if not levels:
            return "none"
        fr = [a / n for _, a, n in levels]
        if min(fr) >= 0.5:
            return "always >= 50 %"
        if max(fr) < 0.5:
            return "always < 50 %"
        return "straddles 50 %"
    cnt = collections.Counter()
    for key, s in verdicts.items():
        if s["gap_decades"] is None:
            cnt[f"discovery {kind(fig[key]['disc'])} | identifiability {kind(fig[key]['ident'])}"] += 1
    return dict(cnt)


def main():
    verdicts = json.load(open("results/p2_verdicts.json"))["H2b"]
    fig = json.load(open("results/p2_figdata.json"))["h2b"]
    acc = accuracy()
    top = without_top_levels(verdicts, fig)
    res = {"accuracy_median_khat_over_k_sigma0_eps0": acc,
           "h2b_without_da_316_1000": top,
           "h2b_without_da_316_1000_summary": {
               "n_slices": len(top),
               "min_p_ident_da_le_31.6": min(v["min_p_ident_da_le_31.6"] for v in top.values()),
               "min_gap_lower_bound_decades": min(v["gap_lower_bound_decades"] for v in top.values())},
           "h2b_no_verdict_classes": classify_no_verdict(verdicts, fig)}
    write_atomic(res, "results/p2_ident_robustness.json")
    print(json.dumps(res["h2b_without_da_316_1000_summary"]))
    print(json.dumps(res["h2b_no_verdict_classes"], indent=1))


if __name__ == "__main__":
    main()
