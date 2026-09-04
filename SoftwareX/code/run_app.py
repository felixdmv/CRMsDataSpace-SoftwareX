"""
SoftwareX Web Application Server:
Launches local web server providing REST APIs and static GIS dashboard for SoftwareX reviewers.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Ensure code directory is in sys.path
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from agent import process_chat_message
from mock_api import load_dataset

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
                    else:
                        os.environ["GEMINI_API_KEY"] = api_key

                result = process_chat_message(query, provider=provider)
                
                # Format evidences from matched docs for frontend visualization
                docs = result.get("docs", [])
                evidences = []
                primary_site_id = docs[0]["id"] if docs else ""
                
                for doc in docs:
                    evidences.append({
                        "title": f"Informe_Tecnico_{doc.get('id', 'site').upper()}.pdf",
                        "page": 1,
                        "score": 0.95,
                        "entities": [f"Mineral: {doc.get('commodities_label', doc.get('commodities', ['CRM'])[0])}", f"País: {doc.get('country_name', doc.get('country', 'Europe'))}"],
                        "snippet": doc.get("description", "Descripción del depósito en la base de datos de SoftwareX."),
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
                print(f"[API ERROR] Fallo al procesar /api/chat: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err_resp = {"error": str(e)}
                self.wfile.write(json.dumps(err_resp).encode("utf-8"))
            return
            
        self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

class SoftwareXHTTPServer(HTTPServer):
    allow_reuse_address = True

def run_server(port=PORT, host="0.0.0.0"):
    import socket
    try:
        import torch
        cuda_status = f"CUDA GPU ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else "CPU Mode (WARNING: No GPU detected!)"
    except Exception:
        cuda_status = "CPU Mode (No GPU)"
        
    server_address = (host, port)
    httpd = SoftwareXHTTPServer(server_address, SoftwareXHandler)
    url = f"http://{socket.gethostname()}:{port}"
    print("=" * 60)
    print("  CRMs Data Space - SoftwareX Architecture Demonstrator")
    print(f"  [INFO] Servidor Híbrido iniciado con éxito en {url}")
    print(f"  [INFO] Modo de Inferencia: {cuda_status}")
    print(f"  [INFO] Endpoint API REST en: http://{socket.gethostname()}:{port}/api/chat")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    sys.stdout.flush()
    
    # Optionally open web browser
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoftwareX Web Application Server")
    parser.add_argument("--port", type=int, default=PORT, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
