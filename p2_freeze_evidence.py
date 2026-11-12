"""Server-side evidence that the pre-registration was frozen before the grid ran (pre-submission review, 2026-11-12).

GitHub's public event log (kept only 90 days) records when each push reached GitHub. This script fetches the push
events of the original repository (ai-mof-cof-dynamics, where the freeze was committed before the history moved
here, COMMIT_MAP.tsv) and keeps those between 2026-10-11 00:00 UTC and the grid start, 2026-10-12 14:59:58 UTC
(p2_grid_chain.log, local time +03:00). The ancestry check (is the freeze commit inside each pushed head) is run
against the original repository's git history.

    python p2_freeze_evidence.py <path to the ai-mof-cof-dynamics checkout>  ->  results/freeze_push_evidence.json
"""
import json
import subprocess
import sys

REPO = "abdulhamidbatayhi123/ai-mof-cof-dynamics"
FREEZE = "d562f195ac7e30f0b7abe039946f4f2bd8b3ad6d"   # original id of 7dcc2fe here
GRID_START_UTC = "2026-10-12T14:59:58Z"


def main():
    src = sys.argv[1]
    raw = subprocess.run(["gh", "api", f"repos/{REPO}/events?per_page=100", "--paginate", "--slurp"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    pages = json.loads(raw)
    evs = [e for page in pages for e in page]
    keep = []
    for e in sorted(evs, key=lambda x: x["created_at"]):
        if e["type"] != "PushEvent" or not ("2026-10-11T00:00:00Z" <= e["created_at"] < GRID_START_UTC):
            continue
        head = e["payload"].get("head")
        anc = subprocess.run(["git", "-C", src, "merge-base", "--is-ancestor", FREEZE, head]).returncode == 0
        keep.append({"event_id": e["id"], "created_at": e["created_at"], "ref": e["payload"].get("ref"),
                     "head": head, "contains_freeze_commit": anc})
    first = next((k for k in keep if k["contains_freeze_commit"]), None)
    out = {"source": f"GET https://api.github.com/repos/{REPO}/events (90-day retention), fetched by this script",
           "freeze_commit_original": FREEZE, "freeze_commit_here": "7dcc2fe (COMMIT_MAP.tsv)",
           "grid_start_utc": GRID_START_UTC, "first_push_containing_freeze": first, "push_events": keep}
    json.dump(out, open("results/freeze_push_evidence.json", "w"), indent=1)
    print(json.dumps(first))


if __name__ == "__main__":
    main()
