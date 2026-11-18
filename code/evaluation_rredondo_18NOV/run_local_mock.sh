#!/bin/bash
# Fast local execution of evaluation_rredondo with deterministic CPU heuristics baseline
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/benchmark_rredondo.py" --provider mock "$@"
