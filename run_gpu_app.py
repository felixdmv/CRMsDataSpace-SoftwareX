#!/usr/bin/env python3
"""
run_gpu_app.py:
Automated Slurm GPU launcher for Geo-RAG Explorer.
Runs the Web Application backend inside an Apptainer container on an NVIDIA GPU compute node,
and creates a transparent TCP reverse proxy on legio2:7860 so reviewers and users can access
the application at http://localhost:7860 with full GPU hardware acceleration.
"""

import os
import sys
import time
import socket
import select
import re
import subprocess
import threading

LEGIO_PORT = 8081
COMPUTO_PORT = 7870

backend_ready = threading.Event()

proxy_target = {
    "host": "",
    "port": COMPUTO_PORT
}

def handle_client(client_sock, client_addr):
    """Handles an individual client connection by forwarding bidirectionally to compute node."""
    if not backend_ready.is_set():
        if not backend_ready.wait(timeout=45):
            try:
                client_sock.close()
            except Exception:
                pass
            return

    target_host = proxy_target["host"]
    target_port = proxy_target["port"]
    
    try:
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.settimeout(15.0)
        target_sock.connect((target_host, target_port))
        target_sock.settimeout(None)
    except Exception as conn_err:
        try:
            client_sock.close()
        except Exception:
            pass
        return

    def forward(src, dst):
        try:
            while True:
                buf = src.recv(65536)
                if not buf:
                    break
                dst.sendall(buf)
        except Exception:
            pass
        finally:
            try:
                dst.shutdown(socket.SHUT_WR)
            except Exception:
                pass
            try:
                src.close()
            except Exception:
                pass
            try:
                dst.close()
            except Exception:
                pass

    t1 = threading.Thread(target=forward, args=(client_sock, target_sock), daemon=True)
    t2 = threading.Thread(target=forward, args=(target_sock, client_sock), daemon=True)
    t1.start()
    t2.start()

def start_proxy(listen_port):
    """Listens on legio2:listen_port and proxies all TCP traffic to proxy_target['host']:proxy_target['port']."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind(('0.0.0.0', listen_port))
    except Exception as bind_err:
        print(f"[Proxy ERROR] Could not bind to port {listen_port}: {bind_err}")
        return
        
    server_sock.listen(128)
    print(f"[Proxy] Listening on legio2:{listen_port}...")
    
    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            client_thread.start()
    except Exception as proxy_err:
        print(f"[Proxy Shutdown] {proxy_err}")
    finally:
        server_sock.close()

def main():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="CRMs Data Space - Geo-RAG Explorer (Slurm GPU Launcher)")
    parser.add_argument("--port", type=int, default=LEGIO_PORT, help=f"Port on legio2 to access from your browser (default: {LEGIO_PORT})")
    parser.add_argument("--compute-port", type=int, default=COMPUTO_PORT, help=f"Internal port on compute node (default: {COMPUTO_PORT})")
    args = parser.parse_args()

    legio_port = args.port
    compute_port = args.compute_port
    proxy_target["port"] = compute_port

    root_dir = Path(__file__).resolve().parent
    run_app_path = root_dir / "run_app.py"

    print("=" * 70)
    print("  CRMs Data Space - Geo-RAG Explorer (Slurm GPU Launcher)")
    print("=" * 70)
    
    # 1. Start proxy thread immediately
    proxy_thread = threading.Thread(target=start_proxy, args=(legio_port,), daemon=True)
    proxy_thread.start()
    
    bind_dirs = ["/home/felix.demiguel:/home/felix.demiguel"]
    if os.path.exists("/home/ubu"):
        bind_dirs.append("/home/ubu:/home/ubu")
    bind_arg = ",".join(bind_dirs)

    slurm_cmd = [
        "srun", "-p", "computo", "--gres=gpu:1",
        "apptainer", "exec", "--nv",
        "--bind", bind_arg,
        "/opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif",
        "python3", "-u", str(run_app_path),
        "--port", str(compute_port)
    ]
    
    print("\n[1/2] Solicitando nodo con GPU NVIDIA en Slurm...")
    env = dict(os.environ)
    env.pop("VSCODE_IPC_HOOK_CLI", None)
    env["PYTHONUNBUFFERED"] = "1"
    env["APPTAINERENV_PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(slurm_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    
    print("[2/2] Transmitiendo logs del cluster y sirviendo tráfico GPU...")
    print("=" * 70)
    print(f"  Acceso Local desde tu Navegador: http://localhost:{legio_port}")
    print("=" * 70)
    
    try:
        for line in proc.stdout:
            line_str = line.strip()
            print(f"  [Cluster GPU Log] {line_str}")
            
            # Parse target node & port from startup log
            match = re.search(r"http://([a-zA-Z0-9_\-]+):(\d+)", line_str)
            if match:
                proxy_target["host"] = match.group(1)
                proxy_target["port"] = int(match.group(2))
                backend_ready.set()
                print(f"  ==> Reverse proxy updated to: http://{proxy_target['host']}:{proxy_target['port']}")
    except KeyboardInterrupt:
        print("\nApagando servidor GPU en Slurm...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    main()
