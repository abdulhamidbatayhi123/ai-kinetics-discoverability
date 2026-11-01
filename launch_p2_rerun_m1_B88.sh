#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec bash p2_rerun_m1_B88.sh >> p2_rerun_m1_B88.log 2>&1
