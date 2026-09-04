import os
import sys
import math
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Define Output Paths
MANUSCRIPT_DIR = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\manuscript"
SCHEMAS_DIR = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\code\variants\schemas"
os.makedirs(MANUSCRIPT_DIR, exist_ok=True)
os.makedirs(SCHEMAS_DIR, exist_ok=True)

# Color Palette (Publication-Grade Professional System)
BG_WHITE = "#FFFFFF"
BORDER_DEFAULT = "#E2E8F0"
TEXT_MAIN = "#0F172A"
TEXT_SUB = "#334155"
TEXT_MUTED = "#64748B"
LINE_COLOR = "#64748B"

COLOR_CATEGORIES = {
    "user": {"header": "#3B82F6", "border": "#1D4ED8", "badge": "#DBEAFE", "badge_text": "#1E40AF"},
    "nlu": {"header": "#6366F1", "border": "#4338CA", "badge": "#EEF2FF", "badge_text": "#3730A3"},
    "builder": {"header": "#D97706", "border": "#B45309", "badge": "#FEF3C7", "badge_text": "#92400E"},
    "solr": {"header": "#059669", "border": "#047857", "badge": "#D1FAE5", "badge_text": "#065F46"},
    "vector": {"header": "#0891B2", "border": "#0E7490", "badge": "#CFFAFE", "badge_text": "#155E75"},
    "gis": {"header": "#8B5CF6", "border": "#6D28D9", "badge": "#EDE9FE", "badge_text": "#5B21B6"},
    "nlg": {"header": "#10B981", "border": "#047857", "badge": "#D1FAE5", "badge_text": "#065F46"}
}

def get_font(size, bold=False):
    font_names = ["segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "calibri.ttf", "arial.ttf"]
    for name in font_names:
        path = os.path.join("C:/Windows/Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

class ProfessionalDiagramBuilder:
    def __init__(self, title, subtitle="", width=1600, height=950, bg_color=BG_WHITE):
        self.width = width
        self.height = height
        self.title = title
        self.subtitle = subtitle
        
        self.img = Image.new("RGB", (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.img)
        
        self.svg = []
        self.svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
        self.svg.append(f'  <rect width="100%" height="100%" fill="{bg_color}" />')
        
        # Add SVG styles and drop shadow filter
        self.svg.append("""  <defs>
    <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="100%" stop-color="#1E293B" />
    </linearGradient>
  </defs>""")
        
        self._draw_header()

    def _draw_header(self):
        if not self.title:
            return
            
        # Top banner in PIL
        self.draw.rectangle([0, 0, self.width, 60], fill="#0F172A")
        self.draw.text((30, 16), self.title, fill="#FFFFFF", font=get_font(20, bold=True))
        if self.subtitle:
            self.draw.text((30 + self.draw.textlength(self.title, font=get_font(20, bold=True)) + 20, 20),
                           f"|  {self.subtitle}", fill="#94A3B8", font=get_font(13))

        # Top banner in SVG
        self.svg.append(f'  <rect x="0" y="0" width="{self.width}" height="60" fill="url(#headerGrad)" />')
        self.svg.append(f'  <text x="30" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="20" font-weight="bold" fill="#FFFFFF">{self.title}</text>')
        if self.subtitle:
            title_w = len(self.title) * 11 + 30
            self.svg.append(f'  <text x="{title_w}" y="38" font-family="system-ui, -apple-system, sans-serif" font-size="13" fill="#94A3B8">|  {self.subtitle}</text>')

    def add_node(self, node_id, x, y, w, h, icon, title, subtitle, details, tech="", category="user"):
        cat_info = COLOR_CATEGORIES.get(category, COLOR_CATEGORIES["user"])
        header_color = cat_info["header"]
        border_color = cat_info["border"]
        badge_bg = cat_info["badge"]
        badge_fg = cat_info["badge_text"]

        # ------------------------------------
        # PIL RENDERING
        # ------------------------------------
        # Soft shadow
        self.draw.rounded_rectangle([x+2, y+4, x+w+2, y+h+4], radius=10, fill="#F1F5F9")
        # Main Box
        self.draw.rounded_rectangle([x, y, x+w, y+h], radius=10, fill="#FFFFFF", outline=border_color, width=2)
        
        # Header strip
        header_h = 36
        self.draw.rounded_rectangle([x, y, x+w, y+header_h], radius=10, fill=header_color)
        self.draw.rectangle([x, y+header_h-8, x+w, y+header_h], fill=header_color)
        self.draw.rounded_rectangle([x, y, x+w, y+h], radius=10, outline=border_color, width=2)
        
        # Header Title with Icon
        header_text = f"{icon}  {title}" if icon else title
        self.draw.text((x + 12, y + 8), header_text, fill="#FFFFFF", font=get_font(13, bold=True))
        
        # Tech Badge (Top Right)
        if tech:
            tech_font = get_font(9, bold=True)
            t_w = self.draw.textlength(tech, font=tech_font) + 12
            bx = x + w - t_w - 8
            by = y + 7
            self.draw.rounded_rectangle([bx, by, bx + t_w, by + 20], radius=5, fill="#0F172A")
            self.draw.text((bx + 6, by + 4), tech, fill="#FFFFFF", font=tech_font)

        # Body Content
        curr_y = y + header_h + 10
        if subtitle:
            self.draw.text((x + 12, curr_y), subtitle, fill=TEXT_MAIN, font=get_font(11, bold=True))
            curr_y += 18
            
        for line in details:
            self.draw.text((x + 12, curr_y), f"• {line}", fill=TEXT_SUB, font=get_font(10))
            curr_y += 15

        # ------------------------------------
        # SVG RENDERING
        # ------------------------------------
        self.svg.append(f'  <!-- Node: {title} -->')
        self.svg.append(f'  <g filter="url(#softShadow)">')
        self.svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill="#FFFFFF" stroke="{border_color}" stroke-width="2" />')
        
        # Header path with rounded top corners
        header_path = f"M {x+10} {y} L {x+w-10} {y} A 10 10 0 0 1 {x+w} {y+10} L {x+w} {y+header_h} L {x} {y+header_h} L {x} {y+10} A 10 10 0 0 1 {x+10} {y} Z"
        self.svg.append(f'    <path d="{header_path}" fill="{header_color}" />')
        
        # Header text
        clean_header = f"{icon}  {title}" if icon else title
        self.svg.append(f'    <text x="{x+12}" y="{y+23}" font-family="system-ui, -apple-system, sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF">{clean_header}</text>')
        
        if tech:
            bw = len(tech) * 6.5 + 14
            bx = x + w - bw - 8
            by = y + 7
            self.svg.append(f'    <rect x="{bx}" y="{by}" width="{bw}" height="20" rx="5" ry="5" fill="#0F172A" />')
            self.svg.append(f'    <text x="{bx+7}" y="{by+14}" font-family="system-ui, -apple-system, sans-serif" font-size="9" font-weight="bold" fill="#FFFFFF">{tech}</text>')

        curr_svg_y = y + header_h + 22
        if subtitle:
            self.svg.append(f'    <text x="{x+12}" y="{curr_svg_y}" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold" fill="{TEXT_MAIN}">{subtitle}</text>')
            curr_svg_y += 18
            
        for line in details:
            clean_l = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self.svg.append(f'    <text x="{x+12}" y="{curr_svg_y}" font-family="system-ui, -apple-system, sans-serif" font-size="10" fill="{TEXT_SUB}">• {clean_l}</text>')
            curr_svg_y += 15
            
        self.svg.append('  </g>')

    def add_arrow(self, x1, y1, x2, y2, label="", color=LINE_COLOR, width=2, curve=False, label_bg="#FFFFFF"):
        # ------------------------------------
        # PIL RENDERING
        # ------------------------------------
        if curve:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2 - 40
            points = []
            for t in [i/15 for i in range(16)]:
                px = (1-t)**2 * x1 + 2*(1-t)*t*cx + t**2 * x2
                py = (1-t)**2 * y1 + 2*(1-t)*t*cy + t**2 * y2
                points.append((px, py))
            self.draw.line(points, fill=color, width=width)
            
            t = 0.94
            x_prev = (1-t)**2 * x1 + 2*(1-t)*t*cx + t**2 * x2
            y_prev = (1-t)**2 * y1 + 2*(1-t)*t*cy + t**2 * y2
            angle = math.atan2(y2 - y_prev, x2 - x_prev)
        else:
            self.draw.line([x1, y1, x2, y2], fill=color, width=width)
            angle = math.atan2(y2 - y1, x2 - x1)
            
        arrow_len = 10
        arrow_angle = math.pi / 6
        xa1 = x2 - arrow_len * math.cos(angle - arrow_angle)
        ya1 = y2 - arrow_len * math.sin(angle - arrow_angle)
        xa2 = x2 - arrow_len * math.cos(angle + arrow_angle)
        ya2 = y2 - arrow_len * math.sin(angle + arrow_angle)
        self.draw.polygon([x2, y2, xa1, ya1, xa2, ya2], fill=color)
        
        if label:
            l_font = get_font(9, bold=True)
            mx = (x1 + x2) / 2
            my = ((y1 + y2) / 2 - 20) if curve else ((y1 + y2) / 2 - 10)
            lw = self.draw.textlength(label, font=l_font)
            self.draw.rounded_rectangle([mx - lw/2 - 4, my - 3, mx + lw/2 + 4, my + 14], radius=4, fill=label_bg, outline=color, width=1)
            self.draw.text((mx - lw/2, my), label, fill=TEXT_MAIN, font=l_font)

        # ------------------------------------
        # SVG RENDERING
        # ------------------------------------
        if curve:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2 - 40
            path_str = f"M {x1} {y1} Q {cx} {cy} {x2} {y2}"
            self.svg.append(f'  <path d="{path_str}" fill="none" stroke="{color}" stroke-width="{width}" />')
        else:
            self.svg.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" />')
            
        arrow_head = f"M {x2} {y2} L {xa1} {ya1} L {xa2} {ya2} Z"
        self.svg.append(f'  <path d="{arrow_head}" fill="{color}" />')
        
        if label:
            mx = (x1 + x2) / 2
            my = ((y1 + y2) / 2 - 15) if curve else ((y1 + y2) / 2 - 5)
            bw = len(label) * 6 + 10
            self.svg.append(f'  <rect x="{mx - bw/2}" y="{my - 10}" width="{bw}" height="16" rx="4" fill="{label_bg}" stroke="{color}" stroke-width="1" />')
            self.svg.append(f'  <text x="{mx}" y="{my + 2}" font-family="system-ui, -apple-system, sans-serif" font-size="9" font-weight="bold" fill="{TEXT_MAIN}" text-anchor="middle">{label}</text>')

    def save(self, filepath_base):
        png_path = f"{filepath_base}.png"
        self.img.save(png_path, "PNG")
        print(f"Saved PNG figure to: {png_path}")
        
        self.svg.append("</svg>")
        svg_path = f"{filepath_base}.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.svg))
        print(f"Saved SVG figure to: {svg_path}")

# =========================================================================
# 1. GENERATE REDESIGNED SYSTEM ARCHITECTURE DIAGRAM
# =========================================================================
def generate_architecture_diagram():
    builder = ProfessionalDiagramBuilder(
        title="CRMsDataSpace: Decoupled Conversational NLU-Solr-GIS Architecture",
        subtitle="SoftwareX Publication Reference Architecture Pipeline",
        width=1600,
        height=950
    )
    
    # ---------------------------------------------------------------------
    # Tier 1: User & Input (Left Column / Top Entry)
    # ---------------------------------------------------------------------
    builder.add_node(
        "query", x=50, y=100, w=260, h=130,
        icon="👤", title="1. User NL Query Input",
        subtitle="Conversational Front-End",
        details=[
            "Multilingual free-text input (ES/EN)",
            "e.g. 'Escombreras de litio activas'",
            "Preset reviewer query triggers",
            "Real-time session state management"
        ],
        tech="Web UI", category="user"
    )
    
    # ---------------------------------------------------------------------
    # Tier 2: Dual NLU Engine (Center-Left Column)
    # ---------------------------------------------------------------------
    builder.add_node(
        "nlu_v1", x=370, y=100, w=270, h=130,
        icon="🧠", title="2A. Few-Shot Parser (v1)",
        subtitle="Intent & Entity Extraction",
        details=[
            "5-example domain prompt engineering",
            "Classifies intent: filter, hybrid, qa",
            "Extracts raw query entities & slots",
            "Zero database schema hallucination"
        ],
        tech="LLM Few-Shot", category="nlu"
    )
    
    builder.add_node(
        "nlu_v3", x=370, y=270, w=270, h=130,
        icon="📐", title="2B. Schema Validator (v3)",
        subtitle="OpenAPI JSON Contract",
        details=[
            "Native Gemini responseSchema",
            "Enforces strict typed output fields",
            "Greedy decoding (T=0.0) for stability",
            "100% machine-parseable JSON contract"
        ],
        tech="OpenAPI / Schema", category="nlu"
    )
    
    # ---------------------------------------------------------------------
    # Tier 3: Normalizer & QueryBuilder (Center Column)
    # ---------------------------------------------------------------------
    builder.add_node(
        "normalizer", x=690, y=100, w=260, h=130,
        icon="⚙️", title="3A. Term Normalizer",
        subtitle="Canonical Thesaurus Mapper",
        details=[
            "Maps slang ('wolframio' -> 'tungsten')",
            "Translates chemical symbols & synonyms",
            "Standardizes facility types & status",
            "Validates against WARM ontology"
        ],
        tech="Python Pipeline", category="builder"
    )
    
    builder.add_node(
        "builder", x=690, y=270, w=260, h=130,
        icon="🔧", title="3B. Solr QueryBuilder",
        subtitle="Search Parameter Generator",
        details=[
            "Constructs Solr filter query array (fq)",
            "Generates disjunctions (country:(...))",
            "Applies edismax query boost factors",
            "Prepares facet field request parameters"
        ],
        tech="QueryBuilder.py", category="builder"
    )
    
    # ---------------------------------------------------------------------
    # Tier 4: Storage & Search Engine (Center-Right Column)
    # ---------------------------------------------------------------------
    builder.add_node(
        "solr", x=1000, y=100, w=270, h=130,
        icon="🔍", title="4A. Apache Solr Engine",
        subtitle="Spatial & Facet Search Index",
        details=[
            "Indexed 100 European CRM facilities",
            "Geospatial bounding box filtering",
            "Computes live facet count distributions",
            "Returns geo-coordinates & WARM records"
        ],
        tech="Apache Solr", category="solr"
    )
    
    builder.add_node(
        "vector", x=1000, y=270, w=270, h=130,
        icon="📄", title="4B. Document Vector Index",
        subtitle="PDF Evidence Retriever",
        details=[
            "Indexed technical report PDF chunks",
            "FAISS vector similarity search (kNN)",
            "Density score reranker (Top K=3)",
            "Provides exact page & snippet citations"
        ],
        tech="FAISS Vector DB", category="vector"
    )
    
    # ---------------------------------------------------------------------
    # Tier 5: Output & GIS Synchronizer (Bottom Row / Right Column)
    # ---------------------------------------------------------------------
    builder.add_node(
        "gis_map", x=1320, y=100, w=230, h=300,
        icon="🗺️", title="5A. Leaflet GIS Map",
        subtitle="Dynamic Map Synchronization",
        details=[
            "Displays active visual filter badges",
            "Renders glowing pulse markers",
            "Dims non-matching facilities",
            "Updates matching site counter",
            "Interactive popups with metadata",
            "Auto-fits map bounds to results"
        ],
        tech="Leaflet.js / JS", category="gis"
    )

    builder.add_node(
        "nlg_chat", x=690, y=470, w=580, h=140,
        icon="💬", title="5B. Grounded NLG Synthesizer & Chat Response UI",
        subtitle="Zero-Knowledge Evidence Fusion & Developer Inspection Drawer",
        details=[
            "Synthesizes natural language summary using retrieved Solr records and PDF evidence snippets",
            "Enforces strict context grounding: zero external knowledge usage to eliminate hallucinations",
            "Renders interactive Solr Engine Inspector drawer (showing raw JSON, fq params, facet counts)",
            "Presents structured evidence cards with technical PDF source citations for domain auditing"
        ],
        tech="LLM Synthesizer + Single-Page UI", category="nlg"
    )

    # ---------------------------------------------------------------------
    # Arrows / Workflows
    # ---------------------------------------------------------------------
    # 1. User -> NLU
    builder.add_arrow(310, 165, 370, 165, "Raw NL Prompt")
    
    # 2. NLU V1 <-> NLU V3 (Dual Variant Pipeline)
    builder.add_arrow(505, 230, 505, 270, "Schema Contract", color="#6366F1")
    
    # 3. NLU -> Normalizer
    builder.add_arrow(640, 165, 690, 165, "Extracted JSON")
    
    # 4. Normalizer -> QueryBuilder
    builder.add_arrow(820, 230, 820, 270, "Normalized Terms")
    
    # 5. QueryBuilder -> Solr Engine
    builder.add_arrow(950, 335, 1000, 165, "Solr Params (q, fq)", color="#D97706")
    
    # 6. QueryBuilder -> Vector Index
    builder.add_arrow(950, 335, 1000, 335, "RAG Query Text", color="#0891B2")
    
    # 7. Solr Engine -> GIS Map
    builder.add_arrow(1270, 165, 1320, 165, "Matching GeoJSON", color="#059669")
    
    # 8. Vector Index -> NLG Synthesizer
    builder.add_arrow(1135, 400, 1135, 470, "Top 3 PDF Evidence Snippets", color="#0891B2")
    
    # 9. Solr Engine -> NLG Synthesizer
    builder.add_arrow(1050, 230, 1050, 470, "Solr Facets & Site Records", color="#059669")
    
    # 10. User Query Context to NLG
    builder.add_arrow(180, 230, 690, 540, "Original Query Context", curve=True, color="#3B82F6")

    # 11. NLG -> User Interface / GIS Map Sync
    builder.add_arrow(1270, 540, 1435, 400, "Synchronized Render Signal", curve=True, color="#8B5CF6")

    # Save to manuscript dir and schemas dir
    builder.save(os.path.join(MANUSCRIPT_DIR, "architecture_diagram"))
    builder.save(os.path.join(SCHEMAS_DIR, "architecture_diagram"))

# =========================================================================
# 2. GENERATE HIGH-IMPACT GRAPHICAL ABSTRACT
# =========================================================================
def generate_graphical_abstract():
    builder = ProfessionalDiagramBuilder(
        title="CRMsDataSpace: Conversational Spatial Discovery for European Critical Raw Materials",
        subtitle="Graphical Abstract — SoftwareX Submission",
        width=1800,
        height=950
    )
    
    # Background Panels for 3 Core Stages
    # Section 1 Panel (Left)
    builder.draw.rounded_rectangle([30, 80, 550, 870], radius=15, fill="#F8FAFC", outline="#CBD5E1", width=2)
    builder.draw.text((50, 95), "1. CONVERSATIONAL USER INPUT", fill="#1E293B", font=get_font(14, bold=True))
    
    # Section 2 Panel (Center)
    builder.draw.rounded_rectangle([580, 80, 1220, 870], radius=15, fill="#F8FAFC", outline="#CBD5E1", width=2)
    builder.draw.text((600, 95), "2. DECOUPLED NLU-SOLR PIPELINE ENGINE", fill="#1E293B", font=get_font(14, bold=True))
    
    # Section 3 Panel (Right)
    builder.draw.rounded_rectangle([1250, 80, 1770, 870], radius=15, fill="#F8FAFC", outline="#CBD5E1", width=2)
    builder.draw.text((1270, 95), "3. SYNCHRONIZED GIS OUTPUT DASHBOARD", fill="#1E293B", font=get_font(14, bold=True))

    # ---------------------------------------------------------------------
    # SECTION 1 NODES (INPUT)
    # ---------------------------------------------------------------------
    builder.add_node(
        "ga_query1", x=60, y=140, w=470, h=160,
        icon="💬", title="Natural Language Free-Text Prompt",
        subtitle="Multilingual Conversational Queries (ES / EN)",
        details=[
            "e.g. 'Muestra escombreras de litio y cobalto en España y Finlandia'",
            "e.g. 'Balsas de wolframio sin restaurar en Alemania'",
            "Domain-specific terminology handling without manual SQL/Solr coding"
        ],
        tech="User Input", category="user"
    )
    
    builder.add_node(
        "ga_presets", x=60, y=320, w=470, h=150,
        icon="⚡", title="Reviewer Presets & Quick Testing",
        subtitle="Zero-Setup Interactive Evaluation",
        details=[
            "Preset 1: Geo-kNN Wolframio (Tungsten dumps in Galicia)",
            "Preset 2: Multilingual Lithium & Cobalt tailings in Spain & Finland",
            "Preset 3: Strategic Rare Earth Elements (REE) in Sweden & France",
            "Instant execution in Standalone Mock Mode without API key"
        ],
        tech="Reviewer Friendly", category="user"
    )

    builder.add_node(
        "ga_case_study", x=60, y=490, w=470, h=350,
        icon="🇪🇺", title="CRMsDataSpace Case Study Dataset",
        subtitle="100 Synthetic European Extractive Waste Facilities",
        details=[
            "Dataset Scope: 12 European Countries (ES, PT, DE, FR, SE, FI, PL, IT, etc.)",
            "12 Critical Raw Materials (Lithium, Cobalt, Tungsten, REE, Nickel, Copper, etc.)",
            "Storage Types: Tailings Ponds, Waste Dumps, Slime Lagoons, Stockpiles",
            "Project Status: Active, Inactive, Abandoned, Reprocessing",
            "Environmental Parameters: Acid Mine Drainage (AMD), Restoration Status",
            "Complies with EU Critical Raw Materials Act framework guidelines",
            "Provides full reproducibility for scientific software benchmark"
        ],
        tech="100 Sites DB", category="solr"
    )

    # ---------------------------------------------------------------------
    # SECTION 2 NODES (DECOUPLED ENGINE)
    # ---------------------------------------------------------------------
    builder.add_node(
        "ga_nlu", x=610, y=140, w=580, h=190,
        icon="🧠", title="Dual-Variant NLU Engine (v1 Few-Shot + v3 OpenAPI Schema)",
        subtitle="Hallucination-Free Semantic Intent & Filter Extraction",
        details=[
            "Variant 1 (Few-Shot Parsing): 5 domain examples mapping prompts to canonical filters",
            "Variant 3 (OpenAPI Schema): Enforces Gemini responseSchema for 100% structured JSON",
            "Temperature T=0.0 greedy decoding guarantees deterministic output across pipeline nodes",
            "Eliminates LLM schema hallucinations and invalid field extractions"
        ],
        tech="LLM Parser + Schema", category="nlu"
    )

    builder.add_node(
        "ga_normalizer", x=610, y=350, w=580, h=170,
        icon="⚙️", title="Multilingual Normalizer, Validator & Solr QueryBuilder",
        subtitle="Standardization & Structured Query Syntax Translation",
        details=[
            "Normalizer: Maps regional slang ('wolframio' -> 'tungsten') & chemical symbols",
            "Validator: Enforces canonical WARM schema constraints and default fallback values",
            "QueryBuilder: Constructs Apache Solr filter queries: fq=['country:(...)', 'commodities:(...)']",
            "Calculates disjunctions and spatial bounding box queries for engine execution"
        ],
        tech="Python Pipeline", category="builder"
    )

    builder.add_node(
        "ga_solr", x=610, y=540, w=580, h=300,
        icon="🔍", title="Apache Solr Spatial Engine & Facet Aggregator",
        subtitle="Sub-Second Geospatial Search & Categorical Breakdown",
        details=[
            "Filters 100 European CRM facilities using spatial bounding boxes & disjunctions",
            "Computes live categorical facets: country breakdown, commodities, project status",
            "Generates geo-coordinate pairs for interactive web map rendering",
            "Returns structured JSON site records for downstream narrative synthesis",
            "Includes optional FAISS vector search over technical PDF report evidence chunks"
        ],
        tech="Apache Solr + FAISS", category="solr"
    )

    # ---------------------------------------------------------------------
    # SECTION 3 NODES (SYNCHRONIZED OUTPUT DASHBOARD)
    # ---------------------------------------------------------------------
    builder.add_node(
        "ga_map", x=1280, y=140, w=470, h=250,
        icon="🗺️", title="Dynamic GIS Leaflet Map",
        subtitle="Visual Synchronization & Pulse Markers",
        details=[
            "Active visual filter badges over Leaflet map header",
            "Matching facilities highlight with glowing pulse rings",
            "Non-matching sites automatically dimmed for visual clarity",
            "Dynamic site counter indicator ('Showing N / 100 European Sites')",
            "Interactive markers with detailed popup metadata cards"
        ],
        tech="Leaflet.js GIS", category="gis"
    )

    builder.add_node(
        "ga_inspector", x=1280, y=410, w=470, h=200,
        icon="🔍", title="Solr Engine Inspector Drawer",
        subtitle="Developer & Auditor Transparency Panel",
        details=[
            "Side-by-side inspection of raw extracted NLU JSON",
            "Real-time display of Solr query parameters (q, fq, defType)",
            "Live facet count distribution tables",
            "Enables complete technical pipeline audit for reviewers"
        ],
        tech="Pipeline Inspector", category="gis"
    )

    builder.add_node(
        "ga_nlg", x=1280, y=630, w=470, h=210,
        icon="💬", title="Grounded Narrative Summary",
        subtitle="Evidence-Based Chat Response UI",
        details=[
            "Concise, scientific response summary in Spanish or English",
            "Strict context grounding: zero external knowledge usage",
            "PDF evidence cards with page numbers & relevance scores",
            "Seamless integration between Chat and Map dashboard"
        ],
        tech="NLG Synthesis UI", category="nlg"
    )

    # Arrows connecting Sections
    builder.add_arrow(530, 220, 610, 220, "NL Prompt Text")
    builder.add_arrow(1190, 220, 1280, 220, "Filter Badges & GeoJSON", color="#059669")
    builder.add_arrow(1190, 500, 1280, 500, "Solr Params & Facets", color="#D97706")
    builder.add_arrow(1190, 730, 1280, 730, "Site Records & Evidences", color="#10B981")

    # Save to manuscript dir and schemas dir
    builder.save(os.path.join(MANUSCRIPT_DIR, "graphical_abstract"))
    builder.save(os.path.join(SCHEMAS_DIR, "graphical_abstract"))

# =========================================================================
# 3. GENERATE BENCHMARK EVALUATION METRICS FIGURE (MATPLOTLIB)
# =========================================================================
def generate_benchmark_chart():
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    
    categories = [
        'Intent\nClassification', 
        'Countries\nFilter', 
        'Commodities\n(CRMs)', 
        'Facility\nTypes', 
        'Project\nStatus', 
        'Overall\nMacro Avg'
    ]
    
    precision = [85.00, 100.00, 100.00, 60.34, 63.64, 81.80]
    recall    = [85.00, 100.00, 100.00, 100.00, 100.00, 97.00]
    f1_score  = [85.00, 100.00, 100.00, 75.27, 77.78, 87.61]

    x = np.arange(len(categories))
    width = 0.25

    rects1 = ax.bar(x - width, precision, width, label='Precision (%)', color='#3B82F6', edgecolor='#1D4ED8', linewidth=1)
    rects2 = ax.bar(x, recall, width, label='Recall (%)', color='#10B981', edgecolor='#047857', linewidth=1)
    rects3 = ax.bar(x + width, f1_score, width, label='F1-Score (%)', color='#6366F1', edgecolor='#4338CA', linewidth=1)

    ax.set_ylabel('Accuracy Metrics (%)', fontsize=12, fontweight='bold', color='#0F172A')
    ax.set_title('Empirical NLU Extraction Metrics across 100 Benchmark Queries', fontsize=14, fontweight='bold', color='#0F172A', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylim(0, 115)
    ax.legend(frameon=True, facecolor='#F8FAFC', edgecolor='#CBD5E1', fontsize=10, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.5, color='#94A3B8')
    ax.set_axisbelow(True)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color='#0F172A', rotation=0)

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    plt.tight_layout()
    chart_path = os.path.join(MANUSCRIPT_DIR, "benchmark_evaluation_metrics.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved benchmark metrics chart to: {chart_path}")

if __name__ == "__main__":
    print("Generating manuscript figures...")
    generate_architecture_diagram()
    generate_graphical_abstract()
    generate_benchmark_chart()
    print("All manuscript figures generated successfully!")
