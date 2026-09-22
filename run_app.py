#!/usr/bin/env python3
"""
Geo-RAG Explorer Web Application Server:
Delegates to SoftwareX architecture demonstrator providing multi-model European CRM GIS dashboard.
"""

import sys
from pathlib import Path

# Add code to path
CODE_DIR = Path(__file__).resolve().parent / "code"
if not CODE_DIR.exists():
    CODE_DIR = Path(__file__).resolve().parent / "SoftwareX" / "code"
sys.path.insert(0, str(CODE_DIR))

# Import and execute SoftwareX server
from run_app import run_server, PORT

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Geo-RAG Explorer Web Application Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    
    run_server(port=args.port, host=args.host)
