#!/bin/bash
# PREREG_P2 amendment A6: recompute every O1 identifiability row with the corrected k range,
# then rerun the pre-registered analysis unchanged. Log: p2_rerun_A6.log. Resumable (the driver
# skips rows already on disk); delete results/p2_extra_o1ident.json only before the first run.
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2
echo "[$(date '+%F %T')] A6 rerun start; freeze: $("$PY" -c 'import p2_grid_o1;print(p2_grid_o1.frozen())')"
"$PY" -X utf8 p2_grid_extra.py o1ident || { echo "[$(date '+%F %T')] FAIL o1ident"; exit 1; }
echo "[$(date '+%F %T')] DONE o1ident"
"$PY" -X utf8 p2_analyze.py || { echo "[$(date '+%F %T')] FAIL analyze"; exit 1; }
echo "[$(date '+%F %T')] DONE analyze"
echo "[$(date '+%F %T')] === A6_RERUN_DONE"
