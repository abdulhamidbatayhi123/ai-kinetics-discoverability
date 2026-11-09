#!/bin/bash
# E4 in three parallel parts (each variant is independent), merged, then e7 --ident-only.
# Replaces the tail of p2_rerun_B90.sh after the 2026-11-09 interruption. Log: p2_rerun_B90.log.
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1
echo "[$(date '+%F %T')] START e4 (parallel parts pre,a | b,c | d)"
"$PY" -X utf8 -W ignore p2_e4_criteria.py --only pre,a results/.e4_p1.json & p1=$!
"$PY" -X utf8 -W ignore p2_e4_criteria.py --only b,c results/.e4_p2.json & p2=$!
"$PY" -X utf8 -W ignore p2_e4_criteria.py --only d results/.e4_p3.json & p3=$!
wait $p1 && wait $p2 && wait $p3 || { echo "[$(date '+%F %T')] FAIL e4 part"; exit 1; }
"$PY" -X utf8 p2_e4_criteria.py --merge results/.e4_p1.json results/.e4_p2.json results/.e4_p3.json || { echo FAIL merge; exit 1; }
echo "[$(date '+%F %T')] DONE e4"
echo "[$(date '+%F %T')] START e7-ident"
"$PY" -X utf8 -W ignore p2_e7_stepshift.py --ident-only || { echo "[$(date '+%F %T')] FAIL e7"; exit 1; }
echo "[$(date '+%F %T')] DONE"
echo "[$(date '+%F %T')] === B90_RERUN_DONE"
