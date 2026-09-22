#!/usr/bin/env bash
# CRMsDataSpace - SoftwareX Demonstrator Quick Launcher
set -e
PORT=${1:-8080}
echo "Starting CRMsDataSpace WebApp on port ${PORT}..."
python3 run_app.py --port "${PORT}"
