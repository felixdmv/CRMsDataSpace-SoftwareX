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
                query = payload.get("query", "")
                provider = payload.get("provider", "mock")
                api_key = payload.get("api_key", "")
                
                if api_key:
                    os.environ["GEMINI_API_KEY"] = api_key

                result = process_chat_message(query, provider=provider)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
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

def run_server(port=PORT):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SoftwareXHandler)
    url = f"http://localhost:{port}"
    print("=" * 60)
    print("  CRMs Data Space - SoftwareX Architecture Demonstrator")
    print(f"  Server running live at: {url}")
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    
    # Optionally open web browser
    try:
        webbrowser.open(url)
    except Exception:
        pass
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
