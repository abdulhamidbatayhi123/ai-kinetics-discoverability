#!/bin/bash
# B90, after Kaggle: wait for all six outputs, merge and validate them (p2_b90_merge.py), then run the
# rest of p2_rerun_B90.sh locally (its o1ident step skips the rows already on disk). Log: p2_rerun_B90.log.
cd "$(dirname "$0")" || exit 1
PY="${P2_PY:-C:/Users/abdulhamid batayhi/Desktop/ai-mof-cof-dynamics/.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2
until grep -q "ALL_OUTPUTS_DOWNLOADED" kaggle_b90/registry.txt 2>/dev/null; do sleep 300; done
echo "[$(date '+%F %T')] START merge + validation of the Kaggle parts"
"$PY" -X utf8 -W ignore p2_b90_merge.py 24 || { echo "[$(date '+%F %T')] FAIL merge"; exit 1; }
echo "[$(date '+%F %T')] DONE merge"
touch results/.b90_cleared        # never delete the merged rows
exec bash p2_rerun_B90.sh
