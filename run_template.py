#!/usr/bin/env python3
"""
General-Purpose GIS Architecture Template Server Launcher:
Delegates to template/run_template.py for domain-agnostic GIS sandbox exploration.
"""

import sys
import importlib.util
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"
if not TEMPLATE_DIR.exists():
    TEMPLATE_DIR = Path(__file__).resolve().parent / "SoftwareX" / "template"

server_script = TEMPLATE_DIR / "run_template.py"
spec = importlib.util.spec_from_file_location("template_server", str(server_script))
template_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_module)
run_server = template_module.run_server

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="General-Purpose GIS Architecture Template Launcher")
    parser.add_argument("--port", type=int, default=8085, help="Port to listen on (default: 8085)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host)
