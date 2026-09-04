import json
import re

LOG_FILE = r"C:\Users\fdemiguel\.gemini\antigravity-cli\brain\a5c434bd-134a-4cf9-8453-50fd3eec4c46\.system_generated\logs\transcript_full.jsonl"
INDEX_PATH = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\static\index.html"
GEO_INDEX_PATH = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\index.html"

# Search transcript_full.jsonl for lines of index.html viewed or returned by tools
js_content = None

with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "Showing lines 210 to 260" in line or "Showing lines 445 to 470" in line or "Showing lines 1940 to 1960" in line:
            pass
        if "function initMap" in line or "window.addEventListener('DOMContentLoaded'" in line:
            print("Found log line containing initMap / DOMContentLoaded")

# Let's inspect log lines to find any full dump of index.html or construct it cleanly
