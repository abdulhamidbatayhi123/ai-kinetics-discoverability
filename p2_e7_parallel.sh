#!/bin/bash
# E7 --ident-only (B90) in three parallel parts (rows are independent), then --merge-parts.
# Resumable: OUT keeps rows already flagged b90; each part file keeps its own finished rows.
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1
echo "[$(date '+%F %T')] START e7-ident (3 parallel parts)"
for i in 0 1 2; do "$PY" -X utf8 -W ignore p2_e7_stepshift.py --ident-only --part $i 3 results/.e7_part$i.json & eval p$i=\$!; done
wait $p0 && wait $p1 && wait $p2 || { echo "[$(date '+%F %T')] FAIL e7 part"; exit 1; }
"$PY" -X utf8 -W ignore p2_e7_stepshift.py --merge-parts results/.e7_part0.json results/.e7_part1.json results/.e7_part2.json || { echo "[$(date '+%F %T')] FAIL e7 merge"; exit 1; }
echo "[$(date '+%F %T')] DONE"
echo "[$(date '+%F %T')] === B90_RERUN_DONE"
