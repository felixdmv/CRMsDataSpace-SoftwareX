"""
SoftwareX Web Application Server:
Launches local web server providing REST APIs and static GIS dashboard for SoftwareX reviewers.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading

# Ensure Python.h and system headers are available for Triton JIT compilation
header_candidates = [
    os.path.expanduser("~/.local/include/python3.12"),
    os.path.expanduser("~/anaconda3/include/python3.12"),
    os.path.expanduser("~/miniconda3/include/python3.12"),
]
if "CONDA_PREFIX" in os.environ:
    header_candidates.insert(0, os.path.join(os.environ["CONDA_PREFIX"], "include", "python3.12"))

for candidate in header_candidates:
    if os.path.exists(candidate):
        cur_cpath = os.environ.get("CPATH", "")
        if candidate not in cur_cpath:
            os.environ["CPATH"] = f"{candidate}:{cur_cpath}" if cur_cpath else candidate
        cur_cinc = os.environ.get("C_INCLUDE_PATH", "")
        if candidate not in cur_cinc:
            os.environ["C_INCLUDE_PATH"] = f"{candidate}:{cur_cinc}" if cur_cinc else candidate
        break

# Ensure code directory is in sys.path
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message
from mock_api import load_dataset
from llm_client import get_model_state, load_local_model_weights, unload_all_local_models

PORT = 8080
STATIC_DIR = CODE_DIR / "static"

class SoftwareXHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/sites":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            sites = load_dataset()
            self.wfile.write(json.dumps(sites, ensure_ascii=False).encode("utf-8"))
            return
            
        elif self.path == "/api/gpu_status" or self.path == "/api/model_status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status = get_model_state()
            vram_total = status.get("vram_total_gb", 0)
            vram_used = status.get("vram_gb", 0)
            status["vram_used_gb"] = vram_used
            status["vram_percent"] = round((vram_used / vram_total) * 100, 1) if vram_total > 0 else 0.0
            self.wfile.write(json.dumps(status).encode("utf-8"))
            return
            
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(post_data)
                query = payload.get("question", payload.get("query", ""))
                provider = payload.get("provider", "mock")
                if provider == "rules":
                    provider = "mock"
                api_key = payload.get("api_key", "")
                
                if api_key:
                    if provider == "openai":
                        os.environ["OPENAI_API_KEY"] = api_key
                    elif provider in ["claude", "anthropic", "claude-code"]:
                        os.environ["ANTHROPIC_API_KEY"] = api_key
                    else:
                        os.environ["GEMINI_API_KEY"] = api_key

                result = process_chat_message(query, provider=provider)
                
                # Format evidences from matched docs for frontend visualization
                docs = result.get("docs", [])
                evidences = []
                primary_site_id = docs[0]["id"] if docs else ""
                
                for doc in docs:
                    evidences.append({
                        "title": f"Technical_Report_{doc.get('id', 'site').upper()}.pdf",
                        "page": 1,
                        "score": 0.95,
                        "entities": [f"Mineral: {doc.get('commodities_label', doc.get('commodities', ['CRM'])[0])}", f"Country: {doc.get('country_name', doc.get('country', 'Europe'))}"],
                        "snippet": doc.get("description", "Deposit description from SoftwareX CRM repository."),
                        "site_id": doc.get("id")
                    })
                
                formatted_response = {
                    "question": query,
                    "query": query,
                    "narrative": result.get("response_text", ""),
                    "response_text": result.get("response_text", ""),
                    "primary_site_id": primary_site_id,
                    "evidences": evidences,
                    "solr_query": result.get("solr_query", {}),
                    "solr_facets": {"facet_counts": {"facet_fields": result.get("facets", {})}},
                    "ner_entities": {"ner_extraction": {"text": query, "entities": result.get("active_map_filters", [])}},
                    "active_map_filters": result.get("active_map_filters", []),
                    "filters": result.get("extracted_json", {}).get("filters", {}),
                    "extracted_json": result.get("extracted_json", {}),
                    "matched_ids": result.get("matched_ids", []),
                    "docs": docs,
                    "llm1_prompt": f"Executing process_chat_message(query='{query}', provider='{provider}')"
                }
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(formatted_response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                print(f"[API ERROR] Failed to process /api/chat: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err_resp = {"error": str(e)}
                self.wfile.write(json.dumps(err_resp).encode("utf-8"))
            return

        elif self.path == "/api/load_model":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_data)
                provider = payload.get("provider", "llama")
                state = get_model_state()
                
                if state.get("status") == "loading":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(state).encode("utf-8"))
                    return

                if state.get("status") == "ready" and state.get("current_model") == provider:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(state).encode("utf-8"))
                    return

                def _bg_load():
                    load_local_model_weights(provider)

                threading.Thread(target=_bg_load, daemon=True).start()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "loading", "provider": provider}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))
            return

        elif self.path == "/api/unload_model":
            try:
                unload_all_local_models()
                state = get_model_state()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(state).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))
            return
            
        self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

class SoftwareXHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(port=PORT, host="0.0.0.0"):
    current_port = port
    httpd = None
    while current_port < port + 20:
        try:
            server_address = (host, current_port)
            httpd = SoftwareXHTTPServer(server_address, SoftwareXHandler)
            break
        except OSError:
            current_port += 1

    if not httpd:
        raise RuntimeError(f"Could not bind to any port in range {port}-{port + 20}")

    engine_status = "Deterministic Standalone Engine (CPU - Zero Dependencies)"
    try:
        import torch
        if torch.cuda.is_available():
            engine_status = f"Local GPU Acceleration ({torch.cuda.get_device_name(0)})"
    except Exception:
        pass

    import socket
    node_hostname = os.environ.get("SLURMD_NODENAME") or socket.gethostname() or "localhost"

    print("=" * 68)
    print("  CRMsDataSpace Explorer — Elsevier SoftwareX Reference WebApp")
    print("=" * 68)
    print(f"  [INFO] Web Application running at: http://{node_hostname}:{current_port}")
    print(f"  [INFO] Execution Mode:             {engine_status}")
    print(f"  [INFO] REST API Endpoint:          http://{node_hostname}:{current_port}/api/chat")
    print(f"  [TIP]  Codespaces View: Click 'Open in New Tab ↗' in the header")
    print(f"         or the globe icon in Ports tab for full-screen GIS layout.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 68)
    sys.stdout.flush()
    
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        try:
            webbrowser.open(f"http://localhost:{current_port}")
        except Exception:
            pass
        
    httpd.serve_forever()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoftwareX Web Application Server")
    parser.add_argument("--port", type=int, default=PORT, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
