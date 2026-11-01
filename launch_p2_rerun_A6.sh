#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec bash p2_rerun_A6.sh >> p2_rerun_A6.log 2>&1
