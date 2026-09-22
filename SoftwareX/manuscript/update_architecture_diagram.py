import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams['font.family'] = 'sans-serif'
from pathlib import Path
out_dir = Path(__file__).resolve().parent

def draw_rounded_box(ax, x, y, w, h, title, subtitle, bullets, box_color, header_color, title_color="white", tag=""):
    # Base card background
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                          facecolor="#FFFFFF", edgecolor=header_color, linewidth=2, zorder=2)
    ax.add_patch(card)
    
    # Header bar
    header_h = h * 0.22
    header_y = y + h - header_h
    header = FancyBboxPatch((x, header_y), w, header_h, boxstyle="round,pad=0.02,rounding_size=0.15",
                            facecolor=header_color, edgecolor=header_color, linewidth=0, zorder=3)
    ax.add_patch(header)
    
    # Header title
    full_title = f"[{tag}] {title}" if tag else title
    ax.text(x + w/2, header_y + header_h/2, full_title, color=title_color, fontsize=10.5, fontweight='bold',
            ha='center', va='center', zorder=4)
    
    # Subtitle
    ax.text(x + w/2, y + h - header_h - 0.22, subtitle, color="#0F172A", fontsize=9.2, fontweight='bold',
            ha='center', va='center', zorder=4)
    
    # Bullets
    start_y = y + h - header_h - 0.50
    line_spacing = 0.26
    for i, b in enumerate(bullets):
        fontweight = 'bold' if b.startswith('  •') or 'Dual Engine' in b or 'Data Sovereignty' in b else 'normal'
        fontsize = 7.8 if len(b) > 30 else 8.2
        color = '#1E40AF' if 'Local GPU' in b else ('#059669' if 'Sovereignty' in b else '#334155')
        ax.text(x + 0.14, start_y - i * line_spacing, f"• {b}", color=color, fontsize=fontsize,
                fontweight=fontweight, ha='left', va='center', zorder=4)

def draw_step_arrow(ax, x1, y1, x2, y2, label="", color="#475569"):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->,head_width=5,head_length=7',
                            color=color, linewidth=2.2, zorder=5)
    ax.add_patch(arrow)
    if label:
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y1 + 0.38, label, color="#0F172A", fontsize=7.6, fontweight='bold',
                ha='center', va='bottom', bbox=dict(boxstyle="round,pad=0.22", facecolor="#F8FAFC", edgecolor=color, lw=1.1), zorder=6)

def create_main_architecture():
    fig, ax = plt.subplots(figsize=(16, 6.5), dpi=300)
    ax.set_xlim(0, 16.8)
    ax.set_ylim(0, 7.3)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Title Banner
    banner = FancyBboxPatch((0.5, 6.35), 15.8, 0.75, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#0F172A", edgecolor="none")
    ax.add_patch(banner)
    ax.text(8.4, 6.72, "CRMsDataSpace: Modular Conversational NLU-Solr-GIS Sovereign Architecture",
            color="white", fontsize=13, fontweight='bold', ha='center', va='center')
    
    box_y = 1.60
    box_h = 4.45
    box_w = 3.35
    
    # Stage 1: NLU & Schema
    draw_rounded_box(ax, 0.5, box_y, box_w, box_h, "Stage 1: NLU & Schema", "Conversational Intent Parsing",
                     ["Multilingual Natural Queries",
                      "Dual Inference Engine:",
                      "  Local GPU (NVIDIA A100 / Slurm)",
                      "  Zero-Setup Standalone Mock / API",
                      "Few-Shot Domain Context Prompts",
                      "Strict OpenAPI JSON Schema (T=0)",
                      "100% European Data Sovereignty"],
                     "#FFFFFF", "#2563EB", tag="1")
    
    # Stage 2: Normalization & Query
    draw_rounded_box(ax, 4.65, box_y, box_w, box_h, "Stage 2: Query Builder", "Canonical Parameter Mapping",
                     ["Multilingual Synonym Normalizer",
                      "WARM CRM Ontology Mapping",
                      "  e.g. 'wolframio' -> 'tungsten'",
                      "Schema Validation & Guards",
                      "Deterministic Solr Query Builder",
                      "Spatial Bounding Box Calculator",
                      "Facet Aggregation Configuration"],
                     "#FFFFFF", "#D97706", tag="2")
                     
    # Stage 3: Spatial Search & Vector RAG
    draw_rounded_box(ax, 8.80, box_y, box_w, box_h, "Stage 3: Retrieval Engine", "Indexed & Semantic Search",
                     ["Apache Solr Spatial Core",
                      "LatLonPointSpatialField Indexing",
                      "Sub-second Geospatial Filtering",
                      "Multi-attribute Facet Breakdown",
                      "FAISS Dense Vector Index",
                      "Top-3 PDF Chunk Reranking",
                      "Traceable Evidence Extraction"],
                     "#FFFFFF", "#059669", tag="3")
                     
    # Stage 4: Synchronized GIS UI
    draw_rounded_box(ax, 12.95, box_y, box_w, box_h, "Stage 4: Synchronized UI", "Interactive Map & Narrative",
                     ["Leaflet.js Dynamic Cartography",
                      "Visual Active Filter Badges Bar",
                      "Animated Glowing Pulse Markers",
                      "Live GPU Telemetry (A100 VRAM)",
                      "Interactive Multi-Attribute Widget",
                      "Grounded Narrative Synthesis",
                      "Developer Inspection Drawer"],
                     "#FFFFFF", "#7C3AED", tag="4")
    
    # Inter-stage Connectors (arrows with labels placed above cleanly)
    draw_step_arrow(ax, 3.85, 3.8, 4.65, 3.8, "Structured\nJSON", "#2563EB")
    draw_step_arrow(ax, 8.00, 3.8, 8.80, 3.8, "Search\nCriteria", "#D97706")
    draw_step_arrow(ax, 12.15, 3.8, 12.95, 3.8, "GeoJSON &\nCitations", "#059669")
    
    # Return loop arrow (curves cleanly DOWNWARDS through bottom margin y=0.5 to y=1.2)
    path = FancyArrowPatch((14.6, 1.50), (2.2, 1.50), arrowstyle='->,head_width=6,head_length=8',
                           connectionstyle="arc3,rad=-0.16", color="#475569", linestyle="--", linewidth=1.8, zorder=5)
    ax.add_patch(path)
    ax.text(8.4, 0.48, "Continuous Visual Cartographic Feedback & Conversational Loop", color="#1E293B", fontsize=9, fontweight='bold',
            ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFFFF", edgecolor="#94A3B8", lw=1.2), zorder=6)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "architecture_diagram.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Created clean architecture_diagram.png")

if __name__ == "__main__":
    create_main_architecture()
