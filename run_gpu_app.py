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

LEGIO_PORT = 7860
COMPUTO_PORT = 7870

proxy_target = {
    "host": "computo02",
    "port": COMPUTO_PORT
}

def start_proxy(listen_port):
    """Listens on legio2:listen_port and proxies all TCP traffic to proxy_target['host']:proxy_target['port']."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind(('0.0.0.0', listen_port))
    except Exception as bind_err:
        print(f"[Proxy ERROR] Could not bind to port {listen_port}: {bind_err}")
        return
        
    server_sock.listen(100)
    print(f"[Proxy] Listening on legio2:{listen_port}...")
    
    sockets = [server_sock]
    connections = {}
    
    try:
        while True:
            readable, _, _ = select.select(sockets, [], [], 0.5)
            for s in readable:
                if s is server_sock:
                    try:
                        client_sock, client_addr = server_sock.accept()
                        target_host = proxy_target["host"]
                        target_port = proxy_target["port"]
                        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        target_sock.connect((target_host, target_port))
                        sockets.extend([client_sock, target_sock])
                        connections[client_sock] = target_sock
                        connections[target_sock] = client_sock
                    except Exception as conn_err:
                        pass
                else:
                    try:
                        data = s.recv(16384)
                        if data:
                            connections[s].sendall(data)
                        else:
                            peer = connections.pop(s, None)
                            if peer:
                                if peer in connections:
                                    connections.pop(peer)
                                if peer in sockets:
                                    sockets.remove(peer)
                                peer.close()
                            if s in sockets:
                                sockets.remove(s)
                            s.close()
                    except Exception:
                        peer = connections.pop(s, None)
                        if peer:
                            if peer in connections:
                                connections.pop(peer)
                            if peer in sockets:
                                sockets.remove(peer)
                            peer.close()
                        if s in sockets:
                            sockets.remove(s)
                        s.close()
    except Exception as proxy_err:
        print(f"[Proxy Shutdown] {proxy_err}")
    finally:
        server_sock.close()

def main():
    print("=" * 70)
    print("  CRMs Data Space - Geo-RAG Explorer (Slurm GPU Launcher)")
    print("=" * 70)
    
    # 1. Start proxy thread immediately
    proxy_thread = threading.Thread(target=start_proxy, args=(LEGIO_PORT,), daemon=True)
    proxy_thread.start()
    
    slurm_cmd = [
        "srun", "-p", "computo", "--gres=gpu:1",
        "apptainer", "exec", "--nv",
        "--bind", "/home/felix.demiguel:/home/felix.demiguel",
        "/opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif",
        "python3", "/home/felix.demiguel/contenido_computo03_felix/CRMsDataSpace/run_app.py",
        "--port", str(COMPUTO_PORT)
    ]
    
    print("\n[1/2] Solicitando nodo con GPU NVIDIA en Slurm...")
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(slurm_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    
    print("[2/2] Transmitiendo logs del cluster y sirviendo tráfico GPU...")
    print("=" * 70)
    print(f"  Acceso Local desde Windows: http://localhost:{LEGIO_PORT}")
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
                print(f"  ==> Reverse proxy updated to: http://{proxy_target['host']}:{proxy_target['port']}")
    except KeyboardInterrupt:
        print("\nApagando servidor GPU en Slurm...")
        proc.terminate()

if __name__ == "__main__":
    main()
