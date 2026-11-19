#!/bin/bash
# Fast local execution of SoftwareX benchmark with deterministic CPU heuristics baseline
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/benchmark_unified.py" ]; then
    python3 "${SCRIPT_DIR}/benchmark_unified.py" --provider mock "$@"
else
    python3 "${SCRIPT_DIR}/benchmark_rredondo.py" --provider mock "$@"
fi
