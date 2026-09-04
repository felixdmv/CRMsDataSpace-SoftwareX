import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

# Define Output Paths
SCHEMAS_DIR = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\code\variants\schemas"
os.makedirs(SCHEMAS_DIR, exist_ok=True)

# Color Palette (Slate Design System)
BG_COLOR = "#F8FAFC"       # Slate 50
DOT_COLOR = "#E2E8F0"      # Slate 200 (for grid)
BORDER_DEFAULT = "#CBD5E1" # Slate 300
TEXT_MAIN = "#0F172A"      # Slate 900
TEXT_SUB = "#475569"       # Slate 600
TEXT_MUTED = "#64748B"     # Slate 500
ARROW_COLOR = "#94A3B8"    # Slate 400

# Color coding for node categories
COLOR_MAP = {
    "slate": {"header": "#64748B", "border": "#475569"},   # Input / Output
    "indigo": {"header": "#4F46E5", "border": "#3730A3"},  # LLM Parser / Synthesizer
    "emerald": {"header": "#059669", "border": "#065F46"}, # Database / Retrieval
    "amber": {"header": "#D97706", "border": "#92400E"},   # Processing / logic
    "red": {"header": "#DC2626", "border": "#991B1B"},     # Error / Early exit
    "cyan": {"header": "#0891B2", "border": "#155E75"}     # Hybrid vector search
}

# Font loading logic with Windows fallbacks
def get_font(size, bold=False):
    font_names = ["segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "calibri.ttf", "arial.ttf"]
    for name in font_names:
        path = os.path.join("C:/Windows/Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

class DiagramBuilder:
    def __init__(self, title, width=1200, height=550):
        self.title = title
        self.width = width
        self.height = height
        
        # Init Pillow Image
        self.img = Image.new("RGB", (width, height), BG_COLOR)
        self.draw = ImageDraw.Draw(self.img)
        
        # Init SVG lines
        self.svg_elements = []
        self.svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">')
        
        # Add SVG styles and filters
        self.svg_elements.append("""  <defs>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.08"/>
    </filter>
    <pattern id="dotGrid" width="20" height="20" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.2" fill="#CBD5E1" />
    </pattern>
  </defs>""")
        
        # Draw background dot grid
        self.draw_grid()

    def draw_grid(self):
        # Draw dots in Pillow
        for x in range(20, self.width, 20):
            for y in range(20, self.height, 20):
                self.draw.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill="#E2E8F0")
                
        # Draw dot grid rect in SVG
        self.svg_elements.append('  <rect width="100%" height="100%" fill="url(#dotGrid)" />')
        
        # Draw main Title in both
        title_font = get_font(18, bold=True)
        self.draw.text((30, 25), self.title.upper(), fill=TEXT_MAIN, font=title_font)
        
        self.svg_elements.append(
            f'  <text x="30" y="42" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="bold" fill="{TEXT_MAIN}">{self.title.upper()}</text>'
        )

    def add_node(self, node_id, x, y, w, h, title, subtitle, details, tech, category="slate"):
        colors = COLOR_MAP.get(category, COLOR_MAP["slate"])
        header_color = colors["header"]
        border_color = colors["border"]
        
        # PIL: Draw drop shadow
        self.draw.rounded_rectangle([x + 3, y + 3, x + w + 3, y + h + 3], radius=10, fill="#E2E8F0")
        # PIL: Draw node container
        self.draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill="#FFFFFF", outline=border_color, width=2)
        # PIL: Draw header strip
        header_h = 32
        self.draw.rounded_rectangle([x, y, x + w, y + header_h], radius=10, fill=header_color)
        # Cover bottom corners of header to make them flat
        self.draw.rectangle([x, y + header_h - 5, x + w, y + header_h], fill=header_color)
        # Re-outline to fix header flat cover overlaps
        self.draw.rounded_rectangle([x, y, x + w, y + h], radius=10, outline=border_color, width=2)
        
        # PIL text titles
        self.draw.text((x + 12, y + 8), title, fill="#FFFFFF", font=get_font(12, bold=True))
        
        # Tech Badge (PIL)
        if tech:
            tech_font = get_font(9, bold=True)
            badge_w = self.draw.textlength(tech, font=tech_font) + 12
            badge_x = x + w - badge_w - 8
            badge_y = y + 6
            self.draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 18], radius=4, fill="#1E293B")
            self.draw.text((badge_x + 6, badge_y + 3), tech, fill="#FFFFFF", font=tech_font)

        # PIL Body content
        curr_y = y + header_h + 10
        if subtitle:
            self.draw.text((x + 12, curr_y), subtitle, fill=TEXT_MAIN, font=get_font(11, bold=True))
            curr_y += 18
            
        for line in details:
            self.draw.text((x + 12, curr_y), f"- {line}", fill=TEXT_SUB, font=get_font(10))
            curr_y += 15

        # SVG: Draw Node with shadow
        self.svg_elements.append(f'  <!-- Node: {title} -->')
        self.svg_elements.append(f'  <g filter="url(#shadow)">')
        # Base container
        self.svg_elements.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill="#FFFFFF" stroke="{border_color}" stroke-width="2" />')
        # Header strip (clipped via path or just overlayed)
        header_path = f"M {x+10} {y} L {x+w-10} {y} A 10 10 0 0 1 {x+w} {y+10} L {x+w} {y+header_h} L {x} {y+header_h} L {x} {y+10} A 10 10 0 0 1 {x+10} {y} Z"
        self.svg_elements.append(f'    <path d="{header_path}" fill="{header_color}" />')
        
        # Header Title
        self.svg_elements.append(f'    <text x="{x+12}" y="{y+21}" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF">{title}</text>')
        
        # Tech Badge (SVG)
        if tech:
            badge_char_w = 6.2
            badge_width = len(tech) * badge_char_w + 12
            bx = x + w - badge_width - 8
            by = y + 6
            self.svg_elements.append(f'    <rect x="{bx}" y="{by}" width="{badge_width}" height="18" rx="4" ry="4" fill="#1E293B" />')
            self.svg_elements.append(f'    <text x="{bx+6}" y="{by+12}" font-family="system-ui, -apple-system, sans-serif" font-size="9" font-weight="bold" fill="#FFFFFF">{tech}</text>')

        # Body Subtitle (SVG)
        curr_svg_y = y + header_h + 22
        if subtitle:
            self.svg_elements.append(f'    <text x="{x+12}" y="{curr_svg_y}" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold" fill="{TEXT_MAIN}">{subtitle}</text>')
            curr_svg_y += 18
            
        # Details lines
        for line in details:
            clean_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self.svg_elements.append(f'    <text x="{x+12}" y="{curr_svg_y}" font-family="system-ui, -apple-system, sans-serif" font-size="10" fill="{TEXT_SUB}">• {clean_line}</text>')
            curr_svg_y += 15
            
        self.svg_elements.append('  </g>')

    def add_arrow(self, x1, y1, x2, y2, label="", color=ARROW_COLOR, width=2, curve=False, label_color=TEXT_MUTED):
        # PIL Draw Line
        if curve:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2 - 50
            points = []
            for t in [i/10 for i in range(11)]:
                px = (1-t)**2 * x1 + 2*(1-t)*t*cx + t**2 * x2
                py = (1-t)**2 * y1 + 2*(1-t)*t*cy + t**2 * y2
                points.append((px, py))
            self.draw.line(points, fill=color, width=width)
            
            t = 0.95
            x_prev = (1-t)**2 * x1 + 2*(1-t)*t*cx + t**2 * x2
            y_prev = (1-t)**2 * y1 + 2*(1-t)*t*cy + t**2 * y2
            angle = math.atan2(y2 - y_prev, x2 - x_prev)
        else:
            self.draw.line([x1, y1, x2, y2], fill=color, width=width)
            angle = math.atan2(y2 - y1, x2 - x1)
            
        # Draw PIL Arrow Head
        arrow_len = 10
        arrow_angle = math.pi / 6
        x_a1 = x2 - arrow_len * math.cos(angle - arrow_angle)
        y_a1 = y2 - arrow_len * math.sin(angle - arrow_angle)
        x_a2 = x2 - arrow_len * math.cos(angle + arrow_angle)
        y_a2 = y2 - arrow_len * math.sin(angle + arrow_angle)
        self.draw.polygon([x2, y2, x_a1, y_a1, x_a2, y_a2], fill=color)
        
        # PIL label
        if label:
            label_font = get_font(9, bold=True)
            if curve:
                mx = (x1 + x2) / 2
                my = ((y1 + y2) / 2 - 50 + (y1+y2)/2) / 2 - 12
            else:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2 - 12
            lbl_w = self.draw.textlength(label, font=label_font)
            self.draw.text((mx - lbl_w/2, my), label, fill=label_color, font=label_font)

        # SVG Draw Line
        if curve:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2 - 50
            path_str = f"M {x1} {y1} Q {cx} {cy} {x2} {y2}"
            self.svg_elements.append(f'  <path d="{path_str}" fill="none" stroke="{color}" stroke-width="{width}" />')
        else:
            self.svg_elements.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" />')
            
        # SVG Arrow Head
        arrow_path_str = f"M {x2} {y2} L {x_a1} {y_a1} L {x_a2} {y_a2} Z"
        self.svg_elements.append(f'  <path d="{arrow_path_str}" fill="{color}" />')
        
        # SVG Label
        if label:
            if curve:
                mx = (x1 + x2) / 2
                my = ((y1 + y2) / 2 - 50 + (y1+y2)/2) / 2 - 5
            else:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2 - 5
            self.svg_elements.append(f'  <text x="{mx}" y="{my}" font-family="system-ui, -apple-system, sans-serif" font-size="9" font-weight="bold" fill="{label_color}" text-anchor="middle">{label}</text>')

    def save(self, filename_base):
        # Save PNG
        png_path = os.path.join(SCHEMAS_DIR, f"{filename_base}.png")
        self.img.save(png_path, "PNG")
        print(f"Saved PNG to {png_path}")
        
        # Save SVG
        self.svg_elements.append("</svg>")
        svg_path = os.path.join(SCHEMAS_DIR, f"{filename_base}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.svg_elements))
        print(f"Saved SVG to {svg_path}")

# ==========================================
# 1. ORIGINAL ARCHITECTURE DIAGRAM
# ==========================================
def draw_original():
    builder = DiagramBuilder("Arquitectura Base (Original)")
    
    # Add Nodes
    # Row 1 (Top)
    builder.add_node("query", 80, 100, 220, 110, "1. User Query", "Entrada de consulta", ["Consulta en lenguaje natural", "e.g., 'Dime escombreras en Huelva'"], "NL String", "slate")
    builder.add_node("nlu", 350, 100, 220, 110, "2. NLU Pipeline", "Extraccion de filtros", ["Identifica entidades por regex/LLM", "Clasifica intenciones basicas"], "LLM / Regex Rules", "indigo")
    builder.add_node("builder", 620, 100, 220, 110, "3. Query Builder", "Traduccion a BD", ["Mapea JSON de filtros", "Genera parametros de consulta Solr"], "Python", "amber")
    builder.add_node("solr", 890, 100, 220, 110, "4. Solr Database", "Recuperacion de registros", ["Busca en indice Solr (Mock API)", "Aplica query syntax (q, fq)"], "Apache Solr", "emerald")
    
    # Row 2 (Bottom)
    builder.add_node("nlg", 890, 340, 220, 110, "5. NLG Synthesizer", "Generacion de respuesta", ["Resume resultados en castellano", "Tono conversacional simple"], "LLM (OpenAI/Gemini)", "indigo")
    builder.add_node("output", 620, 340, 220, 110, "6. Final Response", "Visualizacion en Chat", ["Retorna respuesta de texto natural", "Pinta listado basico de minas"], "Chat UI", "slate")
    
    # Add Arrows
    builder.add_arrow(300, 155, 350, 155, "Raw Text")
    builder.add_arrow(570, 155, 620, 155, "Intent + Filters")
    builder.add_arrow(840, 155, 890, 155, "Solr Params (q, fq)")
    builder.add_arrow(1000, 210, 1000, 340, "DB Records JSON")
    builder.add_arrow(890, 395, 840, 395, "Synthesized Text")
    
    # Curved arrow from Query to NLG (providing query context)
    builder.add_arrow(190, 210, 890, 395, "Query Context", curve=True, label_color="#4F46E5")
    
    builder.save("original_architecture")

# ==========================================
# 2. V1 INTENT CLASSIFICATION DIAGRAM
# ==========================================
def draw_v1():
    builder = DiagramBuilder("Variante 1: Few-Shot Intent & Closed Schema")
    
    # Add Nodes
    builder.add_node("query", 80, 100, 220, 110, "1. User Query", "NL Query Input", ["e.g. 'Balsas sin restaurar en Galicia'", "Solicita datos del CRM o conversacion"], "NL String", "slate")
    builder.add_node("fewshot", 350, 100, 220, 110, "2. Few-Shot LLM Parser", "Clasificacion y Mapeo", ["Prompt con 5 ejemplos estructurados", "Clasifica 3 intents: filter, hybrid, qa", "Filtros limitados a esquema cerrado"], "LLM (Few-Shot)", "indigo")
    builder.add_node("val", 620, 100, 220, 110, "3. Normalizer & Validator", "Control de Contratos", ["Normaliza valores a claves BD", "Valida tipos y campos permitidos", "Salida JSON estructurada"], "Python Pipeline", "amber")
    builder.add_node("solr", 890, 100, 220, 110, "4. Solr Database", "Ejecucion de Consulta", ["Busca sitios en el CRM Data Space", "Retorna registros WARM coincidente"], "Apache Solr", "emerald")
    
    # Row 2 (Bottom)
    builder.add_node("nlg", 890, 340, 220, 110, "5. NLG Synthesizer", "Resumen de Resultados", ["Recibe DB JSON + Query original", "Genera respuesta en castellano", "Retorna vacio amable si 0 items"], "LLM / Python", "indigo")
    builder.add_node("output", 620, 340, 220, 110, "6. Final Output", "Presentacion Gradio", ["Muestra respuesta en el chat", "Pinta tarjetas de las minas"], "Chat UI", "slate")
    
    # Add Arrows
    builder.add_arrow(300, 155, 350, 155, "Raw Query")
    builder.add_arrow(570, 155, 620, 155, "Raw JSON output")
    builder.add_arrow(840, 155, 890, 155, "Validated Query")
    builder.add_arrow(1000, 210, 1000, 340, "CRM Sites JSON")
    builder.add_arrow(890, 395, 840, 395, "Text Response")
    
    # Bypass arrow for generic_qa (greetings, off-topic)
    builder.add_arrow(460, 210, 890, 370, "Bypass: generic_qa", curve=True, label_color="#DC2626", color="#EF4444")
    
    builder.save("v1_few_shot_intent")

# ==========================================
# 3. V2 HYBRID SEARCH & RERANK DIAGRAM
# ==========================================
def draw_v2():
    builder = DiagramBuilder("Variante 2: Hybrid Search & Context Curation", width=1250, height=550)
    
    # Nodes layout designed for split retrieval and merge
    builder.add_node("query", 50, 220, 180, 110, "1. User Query", "NL Query Input", ["e.g. '¿Qué dice el informe de'", "Penouta sobre la estabilidad?'"], "NL String", "slate")
    builder.add_node("nlu", 270, 220, 200, 110, "2. NLU Parser", "Intent & Filter Extraction", ["Procesa y clasifica intencion", "Detecta si requiere RAG (needs_rag)", "O activa por palabras clave de PDF"], "LLM Parser", "indigo")
    
    # Parallel Retrieval Branch
    builder.add_node("solr", 510, 100, 200, 110, "3A. Solr DB Query", "Structured Search", ["Busca metadatos de sitios", "Filtra por region/mineral/etc", "Retorna registros WARM"], "Apache Solr", "emerald")
    builder.add_node("faiss", 510, 340, 200, 110, "3B. FAISS Vector Search", "Semantic Search on PDFs", ["Embedding de query local", "Busca en indices de textos PDF", "Retorna K=10 fragmentos crudos"], "FAISS Index", "cyan")
    
    # Reranking after vector search
    builder.add_node("rerank", 750, 340, 200, 110, "4. Reranker & Curator", "Context Density Filter", ["Filtra por similitud (score >= 0.15)", "Ordena por relevancia desc", "Elige Top 3 parrafos de alta densidad"], "Python Logic", "amber")
    
    # Synthesizer merges both streams
    builder.add_node("nlg", 750, 100, 200, 110, "5. Hybrid NLG Synthesizer", "Narrative Fusion", ["Fusiona registros DB + PDFs curados", "Evita alucinaciones y ruido", "Localiza sintesis en castellano"], "LLM (OpenAI/Gemini)", "indigo")
    builder.add_node("output", 990, 220, 210, 110, "6. Final Output", "Structured UI Display", ["Pinta respuesta con citas", "Mapea fragmentos como 'evidencias'", "Muestra paginas/scores de origen"], "Chat / Gradio", "slate")
    
    # Add Arrows
    builder.add_arrow(230, 275, 270, 275, "Raw Text")
    builder.add_arrow(470, 230, 510, 155, "Filters JSON")
    builder.add_arrow(470, 320, 510, 395, "Text + needs_rag=True", color="#06B6D4")
    
    builder.add_arrow(710, 395, 750, 395, "10 Raw Chunks")
    builder.add_arrow(850, 340, 850, 210, "Top 3 Curated Chunks", color="#D97706")
    builder.add_arrow(710, 155, 750, 155, "WARM Sites JSON")
    
    builder.add_arrow(950, 155, 990, 230, "Response Context")
    builder.add_arrow(950, 395, 1095, 330, "Source Evidence Metadata", curve=True, color="#94A3B8")
    
    builder.save("v2_hybrid_search_rerank")

# ==========================================
# 4. V3 JSON SCHEMA DIAGRAM
# ==========================================
def draw_v3():
    builder = DiagramBuilder("Variante 3: Structured Responses & Schema Enforcement")
    
    # Add Nodes
    builder.add_node("query", 80, 100, 220, 110, "1. User Query", "NL Query Input", ["e.g. 'Dime escombreras de litio'", "Entrada interactiva del usuario"], "NL String", "slate")
    builder.add_node("nlu_schema", 350, 100, 220, 110, "2. Schema-Enforced Parser", "Strict NLU JSON Out", ["Fuerza parsing via responseSchema", "Especifica campos exactos de filtros", "Token-level validation en la API"], "LLM (responseSchema)", "indigo")
    builder.add_node("builder", 620, 100, 220, 110, "3. Query Builder", "Solr Translation", ["Normaliza valores de filtros", "Construye clausulas de consulta Solr"], "Python Pipeline", "amber")
    builder.add_node("solr", 890, 100, 220, 110, "4. Solr Database", "Database Retrieval", ["Ejecuta busqueda estructurada", "Retorna listado JSON de sitios CRM"], "Apache Solr", "emerald")
    
    # Row 2 (Bottom)
    builder.add_node("nlg_schema", 890, 340, 220, 110, "5. Schema-Enforced NLG", "Strict NLG Response Out", ["Fuerza output con responseSchema", "Campos: respuesta, hallazgos_clave, fuentes", "Garantiza estructura 100% parseable"], "LLM (responseSchema)", "indigo")
    builder.add_node("output", 620, 340, 220, 110, "6. Final Output", "Dynamic UI Mapping", ["Extrae campos del JSON tipado", "Carga datos directos en tablas/tarjetas"], "Chat / Frontend", "slate")
    
    # Add Arrows
    builder.add_arrow(300, 155, 350, 155, "Raw Text")
    builder.add_arrow(570, 155, 620, 155, "Strict NLU JSON")
    builder.add_arrow(840, 155, 890, 155, "Solr Params")
    builder.add_arrow(1000, 210, 1000, 340, "DB Records JSON")
    builder.add_arrow(890, 395, 840, 395, "Strict NLG JSON")
    
    builder.add_arrow(190, 210, 890, 395, "Strict Schema Context", curve=True, color="#4F46E5")
    
    builder.save("v3_json_schema")

# ==========================================
# 5. V4 STRICT GROUNDING & CITATIONS DIAGRAM
# ==========================================
def draw_v4():
    builder = DiagramBuilder("Variante 4: Strict Context Grounding & Citations")
    
    # Add Nodes
    builder.add_node("query", 80, 100, 220, 110, "1. User Query", "NL Query Input", ["e.g. 'Balsas de cobalto en Asturias'", "Solicita informacion factica del CRM"], "NL String", "slate")
    builder.add_node("nlu", 350, 100, 220, 110, "2. NLU Parser", "Intent & Filter Extraction", ["Detecta intencion de busqueda", "Aisla filtros del CRM"], "LLM Parser", "indigo")
    builder.add_node("solr", 620, 100, 220, 110, "3. Solr Database Query", "Context Retrieval", ["Ejecuta filtros en la BD Solr", "Retorna total de registros encontrados"], "Apache Solr", "emerald")
    builder.add_node("guard", 890, 100, 220, 110, "4. Early Exit Guard", "Hallucination Prevention", ["Chequea cantidad de resultados", "Si N=0: frena la ejecucion", "Bypassea llamada al LLM"], "Python Logic", "red")
    
    # Row 2 (Bottom)
    builder.add_node("nlg", 890, 340, 220, 110, "5. Grounded NLG Synthesizer", "Zero-Knowledge Synthesis", ["Prohibido usar conocimiento externo", "Fuerza JSON con citas exactas", "Campos: respuesta, fuentes (id, seccion)"], "LLM Grounded", "indigo")
    builder.add_node("output", 500, 340, 260, 110, "6. Final Output", "Traceable Response", ["Muestra texto redactado", "Pinta citas estructuradas en UI", "O devuelve error estandar ('Sin Datos')"], "Chat UI", "slate")
    
    # Add Arrows
    builder.add_arrow(300, 155, 350, 155, "Raw Text")
    builder.add_arrow(570, 155, 620, 155, "Solr Params")
    builder.add_arrow(840, 155, 890, 155, "Query Results JSON")
    
    # Guard branch A: Success (N > 0)
    builder.add_arrow(1000, 210, 1000, 340, "If Results > 0", color="#059669")
    
    # Guard branch B: Early Exit (N == 0)
    builder.add_arrow(890, 155, 760, 360, "If 0 Results: Direct Error JSON", curve=True, color="#DC2626")
    
    builder.add_arrow(890, 395, 760, 395, "Grounded JSON Response")
    
    builder.save("v4_strict_grounding_citations")


if __name__ == "__main__":
    print("Generating all variant diagrams...")
    draw_original()
    draw_v1()
    draw_v2()
    draw_v3()
    draw_v4()
    print("All diagrams generated successfully!")
