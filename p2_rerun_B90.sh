#!/bin/bash
# RETRACTIONS_P2 B90: recompute every O1 identifiability row with the corrected exact LDF update,
# then everything that uses them, one job at a time. Pre-fix files are kept as results/*_preB90.json.
# Log: p2_rerun_B90.log. Resumable: the o1ident driver skips rows already on disk, so delete
# results/p2_extra_o1ident.json only before the first run (done by this script once, marker file).
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2
step() { echo "[$(date '+%F %T')] START $1"; shift; "$PY" -X utf8 -W ignore "$@" || { echo "[$(date '+%F %T')] FAIL $*"; exit 1; }; echo "[$(date '+%F %T')] DONE"; }
echo "[$(date '+%F %T')] B90 rerun start; freeze: $("$PY" -c 'import p2_grid_o1;print(p2_grid_o1.frozen())')"
if [ ! -e results/.b90_cleared ]; then rm -f results/p2_extra_o1ident.json; touch results/.b90_cleared; fi
step o1ident p2_grid_extra.py o1ident
step analyze p2_analyze.py
step figdata p2_figdata.py
step robustness p2_ident_robustness.py
step e3 p2_e3_coverage.py
step e4 p2_e4_criteria.py
step e7-ident p2_e7_stepshift.py --ident-only
echo "[$(date '+%F %T')] === B90_RERUN_DONE"
