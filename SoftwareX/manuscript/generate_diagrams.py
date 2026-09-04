import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

# Set global matplotlib styles
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

out_dir = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\manuscript"

def draw_rounded_box(ax, x, y, w, h, title, subtitle, bullets, box_color, header_color, title_color="white", tag=""):
    # Base card background
    card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                          facecolor="#FFFFFF", edgecolor=header_color, linewidth=2, zorder=2)
    ax.add_patch(card)
    
    # Header bar
    header_h = h * 0.24
    header_y = y + h - header_h
    header = FancyBboxPatch((x, header_y), w, header_h, boxstyle="round,pad=0.02,rounding_size=0.15",
                            facecolor=header_color, edgecolor=header_color, linewidth=0, zorder=3)
    ax.add_patch(header)
    
    # Header title
    full_title = f"[{tag}] {title}" if tag else title
    ax.text(x + w/2, header_y + header_h/2, full_title, color=title_color, fontsize=11, fontweight='bold',
            ha='center', va='center', zorder=4)
    
    # Subtitle
    ax.text(x + w/2, y + h - header_h - 0.18, subtitle, color="#0F172A", fontsize=9.5, fontweight='bold',
            ha='center', va='center', zorder=4)
    
    # Bullets
    start_y = y + h - header_h - 0.42
    line_spacing = 0.22
    for i, b in enumerate(bullets):
        ax.text(x + 0.15, start_y - i * line_spacing, f"• {b}", color="#334155", fontsize=8.5,
                ha='left', va='center', zorder=4)

def draw_arrow(ax, x1, y1, x2, y2, label="", color="#475569"):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->,head_width=6,head_length=8',
                            color=color, linewidth=2, zorder=5)
    ax.add_patch(arrow)
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(mid_x, mid_y + 0.12, label, color="#0F172A", fontsize=8.5, fontweight='bold',
                ha='center', va='center', bbox=dict(boxstyle="round,pad=0.2", facecolor="#F1F5F9", edgecolor=color, lw=1), zorder=6)

# -------------------------------------------------------------
# FIGURE 1: Main Simplified System Architecture
# -------------------------------------------------------------
def create_main_architecture():
    fig, ax = plt.subplots(figsize=(14, 5.8), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Title Banner
    banner = FancyBboxPatch((0.5, 6.1), 15.0, 0.7, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#0F172A", edgecolor="none")
    ax.add_patch(banner)
    ax.text(8.0, 6.45, "CRMsDataSpace: Modular Conversational NLU-Solr-GIS Architecture",
            color="white", fontsize=13, fontweight='bold', ha='center', va='center')
    
    # Stage 1: NLU & Schema
    draw_rounded_box(ax, 0.5, 1.2, 3.3, 4.4, "Stage 1: NLU & Schema", "Conversational Intent Parsing",
                     ["Multilingual NL Query", "Dual-Variant Strategy", "Few-Shot Domain Prompts", "OpenAPI Schema Contract", "Structured Intent Payload"],
                     "#FFFFFF", "#2563EB", tag="1")
    
    # Stage 2: Normalization & Query
    draw_rounded_box(ax, 4.3, 1.2, 3.3, 4.4, "Stage 2: Query Builder", "Canonical Parameter Mapping",
                     ["Multilingual Synonym Mapper", "WARM Domain Thesaurus", "Schema Validation Rules", "Search Parameter Generator", "Facet Request Configuration"],
                     "#FFFFFF", "#D97706", tag="2")
                     
    # Stage 3: Spatial Search & Vector RAG
    draw_rounded_box(ax, 8.1, 1.2, 3.3, 4.4, "Stage 3: Retrieval Engine", "Indexed & Semantic Search",
                     ["Apache Solr Spatial Index", "Geo-Bounding & Filtering", "Live Facet Distributions", "FAISS Vector Document DB", "RAG PDF Evidence Retrieval"],
                     "#FFFFFF", "#059669", tag="3")
                     
    # Stage 4: Synchronized GIS UI
    draw_rounded_box(ax, 11.9, 1.2, 3.3, 4.4, "Stage 4: Synchronized UI", "Interactive Map & Narrative",
                     ["Dynamic Leaflet GIS Map", "Active Visual Filter Badges", "Glowing Pulse Site Markers", "Grounded Text Synthesis", "Developer Inspection Drawer"],
                     "#FFFFFF", "#7C3AED", tag="4")
    
    # Connectors
    draw_arrow(ax, 3.8, 3.4, 4.3, 3.4, "Structured JSON", "#2563EB")
    draw_arrow(ax, 7.6, 3.4, 8.1, 3.4, "Search Criteria", "#D97706")
    draw_arrow(ax, 11.4, 3.4, 11.9, 3.4, "Geo-Data & Citations", "#059669")
    
    # Return loop arrow (Interactive Feedback)
    path = FancyArrowPatch((13.55, 1.2), (2.15, 1.2), arrowstyle='->,head_width=6,head_length=8',
                           connectionstyle="arc3,rad=0.35", color="#475569", linestyle="--", linewidth=1.5, zorder=5)
    ax.add_patch(path)
    ax.text(7.85, 0.15, "Continuous Visual Feedback & Conversational State Loop", color="#475569", fontsize=8.5, fontweight='bold',
            ha='center', va='center', bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="#94A3B8", lw=1), zorder=6)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "architecture_diagram.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created architecture_diagram.png")


# -------------------------------------------------------------
# FIGURE 2: Component 1 - NLU & Schema Enforcement
# -------------------------------------------------------------
def create_component1_nlu():
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Header
    banner = FancyBboxPatch((0.5, 5.2), 13.0, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#2563EB", edgecolor="none")
    ax.add_patch(banner)
    ax.text(7.0, 5.5, "Component 1: Conversational NLU & Schema Enforcement Detail",
            color="white", fontsize=12, fontweight='bold', ha='center', va='center')
            
    # Box A: Raw Input
    draw_rounded_box(ax, 0.5, 0.8, 3.6, 4.0, "User NL Query", "Free-Text Input",
                     ["Multilingual Prompts (ES/EN)", "Domain Spatial Intents", "Example: 'Active lithium waste", "dumps in Spain & Finland'"],
                     "#FFFFFF", "#1D4ED8", tag="A")
                     
    # Box B: Dual-Variant Prompting Strategy
    draw_rounded_box(ax, 4.9, 0.8, 4.2, 4.0, "Dual-Variant Strategy", "LLM Processing Engine",
                     ["Variant 1: Few-Shot Prompting", "  • 5 Exemplar Domain Mappings", "Variant 3: OpenAPI Schema", "  • Strict JSON Schema Enforcement", "  • Greedy Decoding (Temperature 0.0)", "Eliminates Schema Hallucinations"],
                     "#FFFFFF", "#4F46E5", tag="B")
                     
    # Box C: Structured Output
    draw_rounded_box(ax, 9.9, 0.8, 3.6, 4.0, "Structured Output", "Machine-Parseable JSON",
                     ["Validated Intent Category", "Country Filter Array", "Target Commodities Array", "Facility Type Classifications", "Operational Status Constraints"],
                     "#FFFFFF", "#1E40AF", tag="C")
                     
    draw_arrow(ax, 4.1, 2.8, 4.9, 2.8, "Raw Prompt", "#2563EB")
    draw_arrow(ax, 9.1, 2.8, 9.9, 2.8, "JSON Contract", "#4F46E5")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "component1_nlu_schema.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created component1_nlu_schema.png")


# -------------------------------------------------------------
# FIGURE 3: Component 2 - Term Normalization & Query Construction
# -------------------------------------------------------------
def create_component2_query_builder():
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Header
    banner = FancyBboxPatch((0.5, 5.2), 13.0, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#D97706", edgecolor="none")
    ax.add_patch(banner)
    ax.text(7.0, 5.5, "Component 2: Term Normalization & Search Query Generator Detail",
            color="white", fontsize=12, fontweight='bold', ha='center', va='center')
            
    # Box A: Raw Extracted JSON
    draw_rounded_box(ax, 0.5, 0.8, 3.6, 4.0, "Raw Extracted Entities", "Extracted JSON Slots",
                     ["Synonym Variation Inputs", "Multilingual Raw Terms", "Unvalidated Spatial Names", "Initial Parameter Dict"],
                     "#FFFFFF", "#B45309", tag="A")
                     
    # Box B: Thesaurus Normalizer & Validator
    draw_rounded_box(ax, 4.9, 0.8, 4.2, 4.0, "Normalizer & Validator", "Domain Thesaurus Mapper",
                     ["Multilingual Synonym Mapping", "  • 'wolframio' -> 'tungsten'", "  • 'balsa' -> 'tailings pond'", "WARM Ontology Alignment", "Constraint Enforcement", "Default Fallback Assignment"],
                     "#FFFFFF", "#D97706", tag="B")
                     
    # Box C: Search Parameter Generator
    draw_rounded_box(ax, 9.9, 0.8, 3.6, 4.0, "Search Query Builder", "Engine Parameter Array",
                     ["Structured Filter Clauses", "Disjunctive Boolean Arrays", "Text Search Query Strings", "Spatial Bounding Boxes", "Facet Aggregation Requests"],
                     "#FFFFFF", "#92400E", tag="C")
                     
    draw_arrow(ax, 4.1, 2.8, 4.9, 2.8, "Raw Slots", "#B45309")
    draw_arrow(ax, 9.1, 2.8, 9.9, 2.8, "Canonical Terms", "#D97706")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "component2_query_builder.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created component2_query_builder.png")


# -------------------------------------------------------------
# FIGURE 4: Component 3 - Search Engine Indexing & RAG Retrieval
# -------------------------------------------------------------
def create_component3_search_rag():
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Header
    banner = FancyBboxPatch((0.5, 5.2), 13.0, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#059669", edgecolor="none")
    ax.add_patch(banner)
    ax.text(7.0, 5.5, "Component 3: Search Engine Indexing & Vector Retrieval Detail",
            color="white", fontsize=12, fontweight='bold', ha='center', va='center')
            
    # Box A: Search Criteria Input
    draw_rounded_box(ax, 0.5, 0.8, 3.4, 4.0, "Incoming Parameters", "Query Criteria Payload",
                     ["Structured Filter Arrays", "Free-Text Search Query", "RAG Natural Prompt Text", "Spatial Coordinates"],
                     "#FFFFFF", "#047857", tag="A")
                     
    # Box B1: Solr Engine
    draw_rounded_box(ax, 4.7, 2.9, 4.6, 1.9, "Apache Solr Spatial Index", "Database Index Node",
                     ["Executes Structured Filter Queries", "Calculates Live Facet Counts & Distributions", "Returns 100 European CRM Geo-Records"],
                     "#FFFFFF", "#059669", tag="B1")
                     
    # Box B2: FAISS Vector Index
    draw_rounded_box(ax, 4.7, 0.8, 4.6, 1.9, "FAISS Vector Evidence DB", "Technical Document RAG",
                     ["Vector Similarity Search (kNN)", "Retrieves Technical Report PDF Snippets", "Information Density Score Reranker (Top-3)"],
                     "#FFFFFF", "#0891B2", tag="B2")
                     
    # Box C: Unified Payload
    draw_rounded_box(ax, 10.1, 0.8, 3.4, 4.0, "Unified Evidence Store", "Consolidated Payload",
                     ["Matching Site Records", "Geo-Coordinates & Metadata", "Facet Breakdown Summary", "PDF Document Citations"],
                     "#FFFFFF", "#065F46", tag="C")
                     
    draw_arrow(ax, 3.9, 3.8, 4.7, 3.8, "Filters", "#047857")
    draw_arrow(ax, 3.9, 1.8, 4.7, 1.8, "RAG Query", "#047857")
    draw_arrow(ax, 9.3, 3.8, 10.1, 3.8, "Records", "#059669")
    draw_arrow(ax, 9.3, 1.8, 10.1, 1.8, "Citations", "#0891B2")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "component3_search_rag.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created component3_search_rag.png")


# -------------------------------------------------------------
# FIGURE 5: Component 4 - Synchronized GIS Map & Web UI
# -------------------------------------------------------------
def create_component4_gis_ui():
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('#F8FAFC')
    
    # Header
    banner = FancyBboxPatch((0.5, 5.2), 13.0, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                            facecolor="#7C3AED", edgecolor="none")
    ax.add_patch(banner)
    ax.text(7.0, 5.5, "Component 4: Synchronized GIS Map & Web Application UI Detail",
            color="white", fontsize=12, fontweight='bold', ha='center', va='center')
            
    # Box A: Incoming Evidence
    draw_rounded_box(ax, 0.5, 0.8, 3.4, 4.0, "Consolidated Payload", "Geo & Text Input",
                     ["Filtered Facility Records", "GeoJSON Site Coordinates", "Facet Distribution Counts", "Retrieved PDF Snippets"],
                     "#FFFFFF", "#6D28D9", tag="A")
                     
    # Box B1: Leaflet GIS Map
    draw_rounded_box(ax, 4.7, 2.9, 4.6, 1.9, "Leaflet.js GIS Map Engine", "Interactive Spatial View",
                     ["Renders Visual Active Filter Badges", "Triggers Glowing Pulse Ring Markers", "Dims Non-Matching European Facilities"],
                     "#FFFFFF", "#7C3AED", tag="B1")
                     
    # Box B2: Grounded Chat & Drawer
    draw_rounded_box(ax, 4.7, 0.8, 4.6, 1.9, "Grounded Chat & Inspector", "Conversational Front-End",
                     ["Zero-Knowledge Text Synthesis", "Interactive Inspection Drawer (NLU/Solr)", "Structured Evidence & Citation Cards"],
                     "#FFFFFF", "#4C1D95", tag="B2")
                     
    # Box C: Final User Interface State
    draw_rounded_box(ax, 10.1, 0.8, 3.4, 4.0, "Synchronized Web UI", "User Experience State",
                     ["Visually Aligned Map & Chat", "Real-Time Site Counter", "Detailed Facility Popups", "Inspectable System Audit"],
                     "#FFFFFF", "#5B21B6", tag="C")
                     
    draw_arrow(ax, 3.9, 3.8, 4.7, 3.8, "GeoJSON", "#6D28D9")
    draw_arrow(ax, 3.9, 1.8, 4.7, 1.8, "Narrative", "#6D28D9")
    draw_arrow(ax, 9.3, 3.8, 10.1, 3.8, "Map State", "#7C3AED")
    draw_arrow(ax, 9.3, 1.8, 10.1, 1.8, "Chat State", "#4C1D95")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "component4_gis_ui.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created component4_gis_ui.png")

# Execute all
create_main_architecture()
create_component1_nlu()
create_component2_query_builder()
create_component3_search_rag()
create_component4_gis_ui()
