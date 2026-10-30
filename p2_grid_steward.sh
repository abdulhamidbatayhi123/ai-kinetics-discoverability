#!/bin/bash
# Copy kept in the repository so it survives scratch cleanups. Run: bash p2_grid_steward.sh
# Watch the Paper 2 grid chain. On each finished step: summarise every new or changed results
# file, commit it with its marker, push. Exit (waking Claude) on any failure, on an error row,
# when a step in WAKE_ON finishes, or when the chain ends.
cd "/c/Users/abdulhamid batayhi/Desktop/ai-kinetics-discoverability" || exit 1
PY="C:/Users/abdulhamid batayhi/AppData/Local/Programs/Python/Python312/python.exe"
CHK="p2_check_results.py"
WAKE_ON=" ${WAKE_ON:-o2ident m7 m1 refinelevels generate_ref analyze} "
declare -A FILE=([o1]=p2_o1 [o1_ref]=p2_o1 [m5]=p2_extra_m5 [m5_ref]=p2_extra_m5 [m9]=p2_extra_m9
  [m6]=p2_extra_m6 [l2]=p2_extra_l2 [o1ident]=p2_extra_o1ident [m7]=p2_extra_m7 [m7_ref]=p2_extra_m7
  [m1]=p2_extra_m1 [o2]=p2_o2 [o2ident]=p2_o2_ident [o3]=p2_o3_ident)
n0=$(wc -l < p2_grid_chain.log)
while true; do
  new="$(tail -n +$((n0+1)) p2_grid_chain.log)"
  if echo "$new" | grep -qE "FAIL|STOP|Traceback"; then
    echo "PROBLEM:"; echo "$new" | grep -E "FAIL|STOP|Traceback" | head; tail -5 p2_grid_chain.log; exit 0
  fi
  if echo "$new" | grep -q "CHAIN_DONE"; then echo "CHAIN DONE"; tail -3 p2_grid_chain.log; exit 0; fi
  step="$(echo "$new" | grep -oE "DONE  [a-z0-9_]+" | head -1 | awk '{print $2}')"
  if [ -n "$step" ]; then
    n0=$(( n0 + $(echo "$new" | grep -n "DONE  $step" | head -1 | cut -d: -f1) ))
    summary=""
    f="results/${FILE[$step]}.json"
    if [ -z "${FILE[$step]}" ]; then echo "step $step has no mapped results file; not committed"; git status --short; exit 0; fi
    s="$("$PY" -X utf8 "$CHK" "$f" 2>&1 | head -3)"; summary="$f: $s"
    git add "$f"; git add -f "results/.p2_grid_done/$step"
    git commit -q -m "Grid step $step done

$summary
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q origin main 2>&1 | grep -v "^remote:"
    echo "[$(date '+%F %T')] committed step $step: $(git log --oneline -1)"
    echo "$summary"
    echo "$s" | grep -q "errors 0" || { echo "ERROR ROWS or bad file in $f"; exit 0; }
    case "$WAKE_ON" in *" $step "*) exit 0;; esac
  fi
  i=$((i+1))
  if [ $((i % 10)) = 0 ]; then   # every ~10 min: is the chain still alive?
    alive=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='bash.exe'\" | Where-Object { \$_.CommandLine -match 'run_p2_grid' }).Count" 2>/dev/null | tr -d '\r')
    if [ "$alive" = "0" ]; then echo "CHAIN DEAD (no run_p2_grid process) at $(date '+%F %T')"; tail -5 p2_grid_chain.log | cut -c1-200; exit 0; fi
  fi
  sleep 60
done
