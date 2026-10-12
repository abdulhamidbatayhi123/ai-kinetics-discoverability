#!/bin/bash
# Detached launcher for run_p2_grid.sh (survives the terminal closing).
cd "$(dirname "$0")" || exit 1
exec bash run_p2_grid.sh >> p2_grid_chain.log 2>&1
