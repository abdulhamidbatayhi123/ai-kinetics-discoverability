#!/bin/bash
# RETRACTIONS_P2 B88: rerun the M1 demonstration fits that were recorded as errors, with the
# training loop that keeps the best parameters seen (PREREG_P2 A4). Waits for the A6 rerun to
# finish (one job at a time). The as-run file is kept as results/p2_extra_m1_asrun.json; the
# error rows are removed from results/p2_extra_m1.json and the driver recomputes only those.
# Log: p2_rerun_m1_B88.log.
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2
until grep -qE "A6_RERUN_DONE|FAIL" p2_rerun_A6.log; do sleep 300; done
grep -q "A6_RERUN_DONE" p2_rerun_A6.log || { echo "[$(date '+%F %T')] FAIL: the A6 rerun did not finish"; exit 1; }
echo "[$(date '+%F %T')] B88 M1 rerun start; freeze: $("$PY" -c 'import p2_grid_o1;print(p2_grid_o1.frozen())')"
[ -e results/p2_extra_m1_asrun.json ] || cp results/p2_extra_m1.json results/p2_extra_m1_asrun.json
"$PY" -X utf8 -c "
import json
from p2.io_utils import write_atomic
p = 'results/p2_extra_m1.json'
d = json.load(open(p))
bad = [k for k, v in d['rows'].items() if 'error' in v]
for k in bad:
    del d['rows'][k]
write_atomic(d, p)
print('removed', len(bad), 'error rows:', bad)
" || { echo "[$(date '+%F %T')] FAIL prepare"; exit 1; }
"$PY" -X utf8 p2_grid_extra.py m1 || { echo "[$(date '+%F %T')] FAIL m1"; exit 1; }
echo "[$(date '+%F %T')] === B88_M1_RERUN_DONE"
