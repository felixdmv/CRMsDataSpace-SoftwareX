#!/usr/bin/env python3
"""
SoftwareX Slurm GPU Launcher & TCP Reverse Proxy:
Automates execution on institutional cluster compute nodes equipped with NVIDIA GPUs (NVIDIA A100),
running the Web Application backend inside an Apptainer container and establishing a transparent
TCP reverse proxy on the cluster login node so users can access http://localhost:<port>
with full hardware acceleration.
"""

import os
import sys
import time
import socket
import select
import re
import subprocess
import threading
from pathlib import Path

LOGIN_DEFAULT_PORT = 8081
COMPUTE_DEFAULT_PORT = 7870

backend_ready = threading.Event()

proxy_target = {
    "host": "",
    "port": COMPUTE_DEFAULT_PORT
}

def find_free_port(start_port: int, max_tries: int = 50, host: str = "0.0.0.0") -> int:
    """Finds an available TCP port starting from start_port up to start_port + max_tries."""
    for p in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    raise RuntimeError(f"No free port available in range {start_port}-{start_port + max_tries}")

def get_slurm_node_for_user():
    try:
        user = os.environ.get("USER", "")
        cmd = ["squeue", "-u", user, "-o", "%N", "-h"] if user else ["squeue", "-o", "%N", "-h"]
        out = subprocess.check_output(cmd, text=True, timeout=5).strip().split()
        for node in out:
            node = node.strip()
            if node and node not in ("(null)", "None", ""):
                if "[" in node:
                    node = node.split("[")[0] + node.split("[")[1].split("-")[0].split(",")[0].replace("]", "")
                return node
    except Exception:
        pass
    return None

def handle_client(client_sock, client_addr):
    """Handles an individual client connection by forwarding bidirectionally to compute node."""
    if not backend_ready.is_set():
        if not backend_ready.wait(timeout=60):
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
    except Exception as e:
        print(f"  [Proxy WARNING] No se pudo conectar con el backend en {target_host}:{target_port}: {e}")
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
    """Listens on 0.0.0.0:listen_port and proxies all TCP traffic to proxy_target['host']:proxy_target['port']."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind(('0.0.0.0', listen_port))
    except Exception as bind_err:
        print(f"[Proxy ERROR] No se pudo vincular al puerto {listen_port}: {bind_err}")
        return
        
    server_sock.listen(128)
    print(f"  [Proxy OK] Escuchando en 0.0.0.0:{listen_port} (listo para reenviar al nodo GPU)")
    
    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            client_thread.start()
    except Exception:
        pass
    finally:
        server_sock.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="CRMs Data Space - SoftwareX (Slurm GPU Launcher)")
    parser.add_argument("--port", type=int, default=LOGIN_DEFAULT_PORT, help=f"Puerto en el nodo de login para el navegador (default: {LOGIN_DEFAULT_PORT})")
    parser.add_argument("--compute-port", type=int, default=COMPUTE_DEFAULT_PORT, help=f"Puerto interno en nodo de computo (default: {COMPUTE_DEFAULT_PORT})")
    args = parser.parse_args()

    # 1. Dynamically find free port on login node
    try:
        login_port = find_free_port(args.port)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
        
    if login_port != args.port:
        print(f"  [INFO] El puerto solicitado {args.port} estaba ocupado. Asignado puerto libre: {login_port}")

    compute_port = args.compute_port
    proxy_target["port"] = compute_port

    base_dir = Path(__file__).resolve().parent
    code_dir = base_dir / "code" if (base_dir / "code" / "run_app.py").exists() else base_dir
    run_app_path = code_dir / "run_app.py"

    print("=" * 70)
    print("  CRMs Data Space - SoftwareX Architecture Demonstrator")
    print("  Lanzador GPU Automatizado Slurm + Proxy Inverso TCP")
    print("=" * 70)
    
    # Start proxy thread on the confirmed free port
    proxy_thread = threading.Thread(target=start_proxy, args=(login_port,), daemon=True)
    proxy_thread.start()
    
    # 2. Universal bindings for any cluster user
    user_home = os.environ.get("HOME") or str(Path.home())
    code_dir_str = str(code_dir)
    bind_dirs = set()
    
    if os.path.exists(user_home):
        bind_dirs.add(f"{user_home}:{user_home}")
    if os.path.exists(code_dir_str):
        bind_dirs.add(f"{code_dir_str}:{code_dir_str}")
        
    try:
        import pwd
        passwd_home = pwd.getpwuid(os.getuid()).pw_dir
        if passwd_home and passwd_home != user_home:
            bind_dirs.add(f"{user_home}:{passwd_home}")
    except Exception:
        pass

    # Mount parent directory of user home if located in a non-standard cluster path
    if user_home:
        parent_dir = str(Path(user_home).parent)
        if parent_dir and parent_dir != "/home" and os.path.exists(parent_dir):
            bind_dirs.add(f"{parent_dir}:{parent_dir}")
        
    # Bind standard institutional shared storage directories if present on host
    for shared_path in ["/datasets", "/opt", "/scratch"]:
        if os.path.exists(shared_path):
            bind_dirs.add(f"{shared_path}:{shared_path}")
            
    bind_arg = ",".join(sorted(bind_dirs))

    slurm_cmd = [
        "srun", "-p", "computo", "--gres=gpu:1",
        "apptainer", "exec", "--nv",
        "--home", user_home,
        "--bind", bind_arg,
        "/opt/ohpc/pub/containers/nvidia-pytorch-24.03-uv.sif",
        "python3", "-u", str(run_app_path),
        "--port", str(compute_port)
    ]
    
    current_user = os.environ.get("USER", "usuario")
    print(f"\n[1/3] Proxy TCP activo en puerto {login_port}.")
    print("[2/3] Solicitando nodo con GPU NVIDIA A100 en Slurm (particion 'computo')...")
    
    env = dict(os.environ)
    env.pop("VSCODE_IPC_HOOK_CLI", None)
    env["PYTHONUNBUFFERED"] = "1"
    env["APPTAINERENV_PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(slurm_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    
    print("[3/3] Conectando servicio y transmitiendo logs del cluster GPU...")
    print("=" * 70)
    print(f"  URL DE ACCESO: http://localhost:{login_port}")
    print("  INSTRUCCIONES DE CONEXION:")
    print(f"  * En VS Code: Abre la pestaña 'PORTS' (abajo) -> Añade o conecta al puerto {login_port}")
    print(f"  * Desde tu PC local vía SSH: ssh -L {login_port}:localhost:{login_port} {current_user}@<cluster-login-host>")
    print("=" * 70)
    sys.stdout.flush()
    
    try:
        for line in proc.stdout:
            line_str = line.strip()
            print(f"  [Cluster GPU Log] {line_str}")
            
            # Parse target node & port from startup log (supports FQDN)
            match = re.search(r"http://([a-zA-Z0-9_\-\.]+):(\d+)", line_str)
            if match and not backend_ready.is_set():
                parsed_host = match.group(1)
                parsed_port = int(match.group(2))

                # If host was reported as localhost/0.0.0.0/127.0.0.1, detect the actual Slurm compute node
                if parsed_host in ("localhost", "127.0.0.1", "0.0.0.0"):
                    slurm_node = get_slurm_node_for_user()
                    if slurm_node:
                        parsed_host = slurm_node

                proxy_target["host"] = parsed_host
                proxy_target["port"] = parsed_port
                backend_ready.set()
                print("\n" + "=" * 70)
                print(f"  >>> [REVERSE PROXY ACTIVO] Trafico reenviado: 0.0.0.0:{login_port} -> {proxy_target['host']}:{proxy_target['port']}")
                print(f"  >>> Aplicacion lista para usar en: http://localhost:{login_port}")
                print("=" * 70 + "\n")
                sys.stdout.flush()
                
                # If running on a desktop with display, attempt opening browser automatically
                if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
                    try:
                        import webbrowser
                        webbrowser.open(f"http://localhost:{login_port}")
                    except Exception:
                        pass
    except KeyboardInterrupt:
        print("\nApagando servidor GPU en Slurm...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    main()
