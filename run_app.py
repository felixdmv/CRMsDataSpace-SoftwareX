#!/usr/bin/env python3
"""
Geo-RAG Explorer Web Application Server:
Delegates to SoftwareX architecture demonstrator providing multi-model European CRM GIS dashboard.
"""

import sys
from pathlib import Path

# Add SoftwareX/code to path
SOFTWAREX_CODE_DIR = Path(__file__).resolve().parent / "SoftwareX" / "code"
sys.path.insert(0, str(SOFTWAREX_CODE_DIR))

# Import and execute SoftwareX server
from run_app import run_server, PORT

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Geo-RAG Explorer Web Application Server")
    parser.add_argument("--port", type=int, default=7860, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    
    run_server(port=args.port, host=args.host)
