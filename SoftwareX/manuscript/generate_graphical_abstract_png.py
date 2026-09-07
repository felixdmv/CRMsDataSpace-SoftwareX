import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

out_path = "/home/felix.demiguel/contenido_computo03_felix/CRMsDataSpace/SoftwareX/manuscript/graphical_abstract.png"

fig, ax = plt.subplots(figsize=(18, 9.5), dpi=300)
ax.set_xlim(0, 180)
ax.set_ylim(0, 95)
ax.axis('off')
fig.patch.set_facecolor('#F8FAFC')

# Top Header Bar
banner = FancyBboxPatch((0, 89), 180, 6, boxstyle="square,pad=0",
                        facecolor='#0F172A', edgecolor='none', zorder=2)
ax.add_patch(banner)
ax.text(4, 92, "CRMsDataSpace: Conversational Spatial Discovery for European Critical Raw Materials",
        color='#FFFFFF', fontsize=13, fontweight='bold', va='center', zorder=3)
ax.text(125, 92, "|  Graphical Abstract — SoftwareX Submission",
        color='#94A3B8', fontsize=10, va='center', zorder=3)

# Helper function to draw cards
def draw_card(x, y, w, h, title, subtitle, bullets, header_color, tag="", border_color=None):
    b_color = border_color if border_color else header_color
    # Base card
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.8",
                          facecolor="#FFFFFF", edgecolor=b_color, linewidth=1.5, zorder=2)
    ax.add_patch(card)
    
    # Header strip
    strip_h = 2.8
    strip = FancyBboxPatch((x, y + h - strip_h), w, strip_h, boxstyle="round,pad=0.02,rounding_size=0.8",
                           facecolor=header_color, edgecolor=header_color, linewidth=0, zorder=3)
    ax.add_patch(strip)
    
    # Title in strip
    ax.text(x + 1.5, y + h - strip_h/2, title, color='#FFFFFF', fontsize=9.2, fontweight='bold', va='center', zorder=4)
    
    # Tag badge
    if tag:
        tag_w = len(tag) * 0.95 + 2.5
        tag_box = FancyBboxPatch((x + w - tag_w - 1.2, y + h - strip_h + 0.4), tag_w, 2.0, boxstyle="round,pad=0.2",
                                facecolor='#0F172A', edgecolor='none', zorder=4)
        ax.add_patch(tag_box)
        ax.text(x + w - tag_w/2 - 1.2, y + h - strip_h/2 + 0.4, tag, color='#FFFFFF', fontsize=7.2, fontweight='bold', ha='center', va='center', zorder=5)
        
    # Subtitle
    if subtitle:
        ax.text(x + 1.5, y + h - strip_h - 1.8, subtitle, color='#0F172A', fontsize=8.2, fontweight='bold', va='center', zorder=4)
        
    # Bullets
    start_y = y + h - strip_h - 4.0
    line_spacing = 2.05
    for i, b in enumerate(bullets):
        fontweight = 'bold' if 'Local Open LLMs' in b or 'Data Sovereignty' in b or 'NVIDIA A100' in b else 'normal'
        color = '#1E40AF' if 'Data Sovereignty' in b or 'Local Open LLMs' in b else '#334155'
        ax.text(x + 1.5, start_y - i * line_spacing, f"• {b}", color=color, fontsize=7.2, fontweight=fontweight, va='center', zorder=4)

# Section Headers
ax.text(5, 85.5, "1. CONVERSATIONAL USER INPUT", color='#1E293B', fontsize=10.5, fontweight='bold', va='center')
ax.text(62, 85.5, "2. DECOUPLED NLU-SOLR PIPELINE ENGINE", color='#1E293B', fontsize=10.5, fontweight='bold', va='center')
ax.text(123, 85.5, "3. SYNCHRONIZED GIS OUTPUT DASHBOARD", color='#1E293B', fontsize=10.5, fontweight='bold', va='center')

# Column 1
draw_card(5, 66, 52, 17, "Natural Language Free-Text Prompt", "Multilingual Conversational Queries (ES / EN)",
          ["'Muestra escombreras de litio y cobalto en España y Finlandia'",
           "'Balsas de wolframio sin restaurar en Alemania'",
           "Domain-specific terminology handling without manual Solr syntax"],
          "#3B82F6", tag="User Input")

draw_card(5, 47, 52, 16.5, "Reviewer Presets & Quick Testing", "Zero-Setup Interactive Evaluation",
          ["Preset 1: Geo-kNN Wolframio (Tungsten dumps in Galicia)",
           "Preset 2: Multilingual Lithium & Cobalt tailings in Spain & Finland",
           "Preset 3: Strategic Rare Earth Elements (REE) in Sweden & France",
           "Instant execution in Standalone Mock Mode without API key"],
          "#3B82F6", tag="Reviewer Friendly")

draw_card(5, 4, 52, 40.5, "CRMsDataSpace Case Study Dataset", "100 Synthetic European Extractive Waste Facilities",
          ["Scope: 12 European Countries (ES, PT, DE, FR, SE, FI, PL, IT)",
           "12 Critical Raw Materials (Lithium, Cobalt, Tungsten, REE, etc.)",
           "Storage Types: Tailings Ponds, Waste Dumps, Slime Lagoons",
           "Project Status: Active, Inactive, Abandoned, Reprocessing",
           "Environmental Parameters: Acid Mine Drainage (AMD), Restoration",
           "Complies with EU Critical Raw Materials Act guidelines",
           "100% full reproducibility for scientific software benchmark"],
          "#059669", tag="100 Sites DB")

# Column 2
draw_card(62, 62, 57, 21, "Dual-Engine Sovereign NLU Engine", "Hallucination-Free Semantic Intent & Deterministic JSON",
          ["Local Open LLMs: Llama 3.2 3B, Qwen 2.5 7B, Phi-3, DeepSeek R1",
           "100% European Data Sovereignty: Zero cloud leakage to APIs",
           "Strict OpenAPI JSON Schema + Few-Shot Prompts (T=0.0)",
           "Dual Inference: Local GPU (A100 / Slurm) + Standalone Mock",
           "Eliminates database schema hallucinations and invalid fields"],
          "#6366F1", tag="A100 + Slurm + Mock")

draw_card(62, 39.5, 57, 19.5, "Multilingual Normalizer & Solr QueryBuilder", "Standardization & Structured Query Translation",
          ["Normalizer: Maps regional slang ('wolframio' -> 'tungsten')",
           "Validator: Enforces canonical WARM schema constraints",
           "QueryBuilder: Constructs Solr filter queries: fq=['country:(...)']",
           "Calculates disjunctions and spatial bounding boxes for Solr"],
          "#D97706", tag="Python Pipeline")

draw_card(62, 4, 57, 32.5, "Apache Solr Spatial Engine & Facet Aggregator", "Sub-Second Geospatial Search & Categorical Breakdown",
          ["Filters 100 European CRM facilities using spatial bounding boxes",
           "Computes live categorical facets: country, commodities, status",
           "Generates geo-coordinate pairs for interactive web map rendering",
           "Returns structured JSON site records for downstream synthesis",
           "Includes optional FAISS vector search over PDF report chunks"],
          "#059669", tag="Apache Solr + FAISS")

# Column 3
draw_card(123, 58, 52, 25, "Dynamic GIS Leaflet Map", "Visual Cartography & Marker Feedback",
          ["Active visual filter badges over dedicated sub-bar",
           "Matching facilities highlight with glowing pulse rings",
           "Non-matching sites automatically dimmed for visual clarity",
           "Real-time GPU VRAM Telemetry badge (NVIDIA A100)",
           "Interactive markers with detailed popup metadata cards"],
          "#8B5CF6", tag="Leaflet.js GIS")

draw_card(123, 31, 52, 24, "Solr Engine Inspector Drawer", "Developer & Auditor Transparency Panel",
          ["Side-by-side inspection of raw extracted NLU JSON",
           "Real-time display of Solr query parameters (q, fq, rows)",
           "Live facet count distribution tables",
           "Enables complete technical pipeline audit for reviewers"],
          "#8B5CF6", tag="Pipeline Inspector")

draw_card(123, 4, 52, 24, "Grounded Narrative Summary", "Evidence-Based Chat Response UI",
          ["Concise, scientific response summary in Spanish or English",
           "Strict context grounding: zero external hallucinated knowledge",
           "PDF evidence cards with page numbers & relevance scores",
           "Seamless two-way integration between Chat and Map"],
          "#10B981", tag="NLG Synthesis UI")

# Connecting Arrows between Columns
def draw_connector(x1, y1, x2, y2, label, color):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->,head_width=5,head_length=7',
                            color=color, linewidth=2, zorder=6)
    ax.add_patch(arrow)
    mid_x = (x1 + x2) / 2
    ax.text(mid_x, y1 + 1.2, label, color='#0F172A', fontsize=7.0, fontweight='bold',
            ha='center', va='bottom', bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor=color, lw=1), zorder=7)

draw_connector(57, 74, 62, 74, "NL Prompt", "#475569")
draw_connector(119, 74, 123, 74, "Filter Badges & GeoJSON", "#059669")
draw_connector(119, 48, 123, 48, "Solr Params & Facets", "#D97706")
draw_connector(119, 18, 123, 18, "Records & Evidence", "#10B981")

plt.tight_layout()
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Successfully generated clean {out_path}")
