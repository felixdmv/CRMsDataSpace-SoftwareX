#!/usr/bin/env python3
"""
GitHub Codespaces Background Service Orchestrator:
Automatically starts both CRMsDataSpace (Port 8080) and GIS Template (Port 8085)
in the background without blocking the container attach lifecycle.
"""

import sys
import socket
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def start_daemon(cmd: list, log_file: Path):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as out:
        subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

def main():
    print("==========================================================================")
    print(" 🚀 GitHub Codespaces Auto-Launcher: SoftwareX Demonstrator & Template")
    print("==========================================================================")

    # 1. Start CRMsDataSpace European Demonstrator on Port 8080
    if not is_port_listening(8080):
        print(" [*] Launching CRMsDataSpace WebApp on port 8080 (background)...")
        log_8080 = ROOT_DIR / ".cache" / "crms_webapp.log"
        start_daemon([sys.executable, "run_app.py", "--port", "8080"], log_8080)
    else:
        print(" [✓] CRMsDataSpace WebApp is already active on port 8080.")

    # 2. Start General-Purpose GIS Architecture Template on Port 8085
    if not is_port_listening(8085):
        print(" [*] Launching General GIS Template Sandbox on port 8085 (background)...")
        log_8085 = ROOT_DIR / ".cache" / "gis_template.log"
        start_daemon([sys.executable, "run_template.py", "--port", "8085"], log_8085)
    else:
        print(" [✓] General GIS Template is already active on port 8085.")

    # Give a brief moment for binding
    time.sleep(0.5)

    print("\n [✓] Applications ready for evaluation:")
    print("     👉 [Port 8080] CRMsDataSpace European WebApp: http://localhost:8080")
    print("     👉 [Port 8085] General GIS Template Sandbox:  http://localhost:8085")
    print("==========================================================================")

if __name__ == "__main__":
    main()
