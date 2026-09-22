import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Polygon
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
from pathlib import Path
out_png = Path(__file__).resolve().parent / "graphical_abstract.png"

fig, ax = plt.subplots(figsize=(18, 10), dpi=300)
ax.set_xlim(0, 180)
ax.set_ylim(0, 100)
ax.axis('off')
fig.patch.set_facecolor('#0B1329')  # Deep modern dark blue canvas

# Top Header Bar
header_bg = FancyBboxPatch((2, 91), 176, 7.5, boxstyle="round,pad=0.3",
                           facecolor='#1E293B', edgecolor='#3B82F6', linewidth=1.5, zorder=2)
ax.add_patch(header_bg)
ax.text(6, 95.5, "A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization",
        color='#FFFFFF', fontsize=15, fontweight='bold', va='center', zorder=3)
ax.text(6, 92.5, "Synchronized Conversational Spatial Discovery & Map Filtering with 100% European Data Sovereignty",
        color='#93C5FD', fontsize=10, fontweight='medium', va='center', zorder=3)
ax.text(174, 94.5, "SoftwareX",
        color='#F59E0B', fontsize=14, fontweight='bold', ha='right', va='center', zorder=3)

# -------------------------------------------------------------
# 1. PANEL LEFT: Conversational Chat Interface (x: 4 to 52, y: 6 to 88)
# -------------------------------------------------------------
chat_card = FancyBboxPatch((4, 6), 48, 82, boxstyle="round,pad=0.5",
                          facecolor='#0F172A', edgecolor='#38BDF8', linewidth=2.0, zorder=2)
ax.add_patch(chat_card)

# Window Title Bar
chat_bar = FancyBboxPatch((4, 82), 48, 6, boxstyle="round,pad=0.2",
                          facecolor='#1E293B', edgecolor='none', zorder=3)
ax.add_patch(chat_bar)
# Window dots
for idx, c in enumerate(['#EF4444', '#F59E0B', '#10B981']):
    ax.add_patch(Circle((6.5 + idx*2.2, 85), 0.7, color=c, zorder=4))
ax.text(15, 85, "1. Conversational Chat Interface", color='#FFFFFF', fontsize=11, fontweight='bold', va='center', zorder=4)

# Multilingual Badge
lang_pill = FancyBboxPatch((6, 76), 44, 4.2, boxstyle="round,pad=0.2",
                          facecolor='#1E3A8A', edgecolor='#60A5FA', linewidth=1.0, zorder=3)
ax.add_patch(lang_pill)
ax.text(28, 78.1, "Multilingual Support: English, Spanish, German, French", 
        color='#DBEAFE', fontsize=8.2, fontweight='bold', ha='center', va='center', zorder=4)

# User Message Bubble
user_bubble = FancyBboxPatch((8, 60), 40, 13.5, boxstyle="round,pad=0.4",
                            facecolor='#2563EB', edgecolor='#60A5FA', linewidth=1.2, zorder=3)
ax.add_patch(user_bubble)
ax.text(10, 70.5, "User Query (Natural Language):", color='#BFDBFE', fontsize=8.2, fontweight='bold', zorder=4)
ax.text(10, 65.5, "\"Show active lithium & cobalt\n waste dumps in Spain and Finland\"", 
        color='#FFFFFF', fontsize=10.5, fontweight='bold', style='italic', va='center', zorder=4)

# Dynamic Transition arrow down inside chat
ax.annotate('', xy=(28, 51), xytext=(28, 58),
            arrowprops=dict(arrowstyle="->", color='#38BDF8', lw=2.5), zorder=4)
ax.text(28, 54.5, "Deterministic Intent & Spatial Filtering", color='#38BDF8', fontsize=7.8, ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#0F172A', edgecolor='#0284C7', lw=0.8), zorder=5)

# Assistant Response Bubble
bot_bubble = FancyBboxPatch((8, 10), 40, 39, boxstyle="round,pad=0.4",
                           facecolor='#1E293B', edgecolor='#10B981', linewidth=1.5, zorder=3)
ax.add_patch(bot_bubble)
ax.text(10, 46, "Assistant Response (Grounded GIS Feedback):", color='#34D399', fontsize=8.5, fontweight='bold', zorder=4)
ax.text(10, 39, "6 matching facilities discovered across\nSpain (4 sites) and Finland (2 sites).", 
        color='#F1F5F9', fontsize=9.2, fontweight='bold', zorder=4)
ax.text(10, 31, "Extracted CRMs: Lithium (Li), Cobalt (Co)\nFacility Class: Tailings & Waste Impoundment\nMap viewport synchronized to European bounds\nGlowing pulse markers activated in Leaflet GIS.", 
        color='#94A3B8', fontsize=8.0, zorder=4)

# Evidence card inside bubble
evid_card = FancyBboxPatch((10, 12), 36, 7.5, boxstyle="round,pad=0.2",
                          facecolor='#0F172A', edgecolor='#059669', linewidth=1.0, zorder=4)
ax.add_patch(evid_card)
ax.text(12, 17.0, "Traceable Geological Evidence (UNFC / NI 43-101):", color='#6EE7B7', fontsize=7.2, fontweight='bold', zorder=5)
ax.text(12, 14.0, "Penouta Sn-Ta-Li Project Report (4.8 Mt tailings, 0.12% Li2O)", color='#CBD5E1', fontsize=7.0, zorder=5)

# -------------------------------------------------------------
# 2. PANEL MIDDLE-TOP: Sovereign NLU Engine (x: 58 to 118, y: 50 to 88)
# -------------------------------------------------------------
nlu_card = FancyBboxPatch((58, 50), 60, 38, boxstyle="round,pad=0.5",
                         facecolor='#0F172A', edgecolor='#818CF8', linewidth=2.0, zorder=2)
ax.add_patch(nlu_card)

# NLU Header bar
nlu_bar = FancyBboxPatch((58, 82), 60, 6, boxstyle="round,pad=0.2",
                         facecolor='#312E81', edgecolor='none', zorder=3)
ax.add_patch(nlu_bar)
ax.text(61, 85, "2. Dual-Variant Sovereign NLU Engine", color='#FFFFFF', fontsize=11, fontweight='bold', va='center', zorder=4)

# Sovereignty Badge
sov_badge = FancyBboxPatch((85, 75.5), 31, 5, boxstyle="round,pad=0.3",
                          facecolor='#065F46', edgecolor='#34D399', linewidth=1.0, zorder=3)
ax.add_patch(sov_badge)
ax.text(100.5, 78, "100% European Data Sovereignty", color='#A7F3D0', fontsize=8.0, fontweight='bold', ha='center', va='center', zorder=4)

ax.text(61, 78, "On-Premises Local GPU LLMs (NVIDIA A100):\nQwen 2.5 7B  |  Llama 3.2 3B  |  Phi-3 Mini", 
        color='#E0E7FF', fontsize=7.8, fontweight='medium', va='center', zorder=4)

# JSON Schema Output Card
json_box = FancyBboxPatch((60, 52), 56, 21, boxstyle="round,pad=0.3",
                         facecolor='#030712', edgecolor='#6366F1', linewidth=1.2, zorder=3)
ax.add_patch(json_box)
ax.text(62, 70, "Strict OpenAPI JSON Schema Enforcement (Zero Hallucinations):", color='#818CF8', fontsize=7.8, fontweight='bold', zorder=4)

json_str = (
    '{\n'
    '  "intent": "search",\n'
    '  "countries": ["spain", "finland"],\n'
    '  "commodities": ["lithium", "cobalt"],\n'
    '  "storage_facility_types": ["waste_dump"],\n'
    '  "project_status": ["active"]\n'
    '}'
)
ax.text(64, 60.5, json_str, color='#38BDF8', fontsize=7.5, fontfamily='monospace', fontweight='medium', va='center', zorder=4)

# -------------------------------------------------------------
# 3. PANEL MIDDLE-BOTTOM: Apache Solr Spatial Engine (x: 58 to 118, y: 6 to 44)
# -------------------------------------------------------------
solr_card = FancyBboxPatch((58, 6), 60, 38, boxstyle="round,pad=0.5",
                          facecolor='#0F172A', edgecolor='#F59E0B', linewidth=2.0, zorder=2)
ax.add_patch(solr_card)

# Solr Header bar
solr_bar = FancyBboxPatch((58, 38), 60, 6, boxstyle="round,pad=0.2",
                          facecolor='#78350F', edgecolor='none', zorder=3)
ax.add_patch(solr_bar)
ax.text(61, 41, "3. Apache Solr Spatial Engine & Vector RAG", color='#FFFFFF', fontsize=11, fontweight='bold', va='center', zorder=4)

# Solr Filter Query Box
solr_box = FancyBboxPatch((60, 16), 56, 20, boxstyle="round,pad=0.3",
                          facecolor='#030712', edgecolor='#D97706', linewidth=1.2, zorder=3)
ax.add_patch(solr_box)
ax.text(62, 33, "Deterministic Boolean Spatial Filter Queries (fq):", color='#FBBF24', fontsize=8.0, fontweight='bold', zorder=4)

solr_code = (
    'fq = country_canonical_s:("spain" OR "finland")\n'
    'fq = commodities_ss:("lithium" OR "cobalt")\n'
    'fq = facility_type_s:("waste_dump")\n'
    'fq = status_s:("active")'
)
ax.text(64, 25.0, solr_code, color='#FDE68A', fontsize=7.8, fontfamily='monospace', fontweight='bold', va='center', zorder=4)

ax.text(61, 11, "100 European CRM Sites Spatial Core (LatLonPointSpatialField & Solr Facets)", 
        color='#CBD5E1', fontsize=7.5, fontweight='medium', zorder=4)

# -------------------------------------------------------------
# 4. PANEL RIGHT: Synchronized GIS Map (x: 124 to 176, y: 6 to 88)
# -------------------------------------------------------------
gis_card = FancyBboxPatch((124, 6), 52, 82, boxstyle="round,pad=0.5",
                         facecolor='#0F172A', edgecolor='#10B981', linewidth=2.0, zorder=2)
ax.add_patch(gis_card)

# GIS Header Bar
gis_bar = FancyBboxPatch((124, 82), 52, 6, boxstyle="round,pad=0.2",
                         facecolor='#064E3B', edgecolor='none', zorder=3)
ax.add_patch(gis_bar)
ax.text(127, 85, "4. Dynamic GIS Map Synchronization", color='#FFFFFF', fontsize=11, fontweight='bold', va='center', zorder=4)

# Active Filter Pills Sub-Bar
filter_bar = FancyBboxPatch((126, 74), 48, 6.5, boxstyle="round,pad=0.2",
                           facecolor='#022C22', edgecolor='#059669', linewidth=1.0, zorder=3)
ax.add_patch(filter_bar)
ax.text(127.5, 77.8, "Active GIS Filter Badges:", color='#34D399', fontsize=7.5, fontweight='bold', zorder=4)

ax.text(127.5, 75.2, "[Spain, Finland]  [Lithium, Cobalt]  [Waste Dump]  [Active]", 
        color='#A7F3D0', fontsize=7.0, fontweight='bold', fontfamily='monospace', zorder=4)

# Counter Badge
cnt_badge = FancyBboxPatch((126, 68), 48, 4.5, boxstyle="round,pad=0.2",
                          facecolor='#065F46', edgecolor='#10B981', linewidth=1.0, zorder=3)
ax.add_patch(cnt_badge)
ax.text(150, 70.2, "Visualizing 6 / 100 European CRM Facilities", color='#FFFFFF', fontsize=8.5, fontweight='bold', ha='center', va='center', zorder=4)

# Map Canvas (Stylized European Geographic Map)
map_canvas = FancyBboxPatch((126, 16), 48, 50, boxstyle="round,pad=0.2",
                           facecolor='#1E293B', edgecolor='#334155', linewidth=1.0, zorder=3)
ax.add_patch(map_canvas)

# Stylized Europe Landmasses (Polygons)
spain_poly = Polygon([[130, 24], [137, 24], [139, 32], [132, 34], [129, 29]], closed=True,
                     facecolor='#334155', edgecolor='#475569', linewidth=1.0, zorder=4)
ax.add_patch(spain_poly)

france_poly = Polygon([[136, 35], [144, 35], [146, 44], [137, 43]], closed=True,
                      facecolor='#1E293B', edgecolor='#475569', linewidth=0.8, zorder=4)
ax.add_patch(france_poly)

germany_poly = Polygon([[144, 38], [152, 38], [153, 49], [144, 48]], closed=True,
                       facecolor='#1E293B', edgecolor='#475569', linewidth=0.8, zorder=4)
ax.add_patch(germany_poly)

finland_poly = Polygon([[154, 52], [163, 52], [164, 63], [156, 64]], closed=True,
                       facecolor='#334155', edgecolor='#475569', linewidth=1.0, zorder=4)
ax.add_patch(finland_poly)

# Non-matching background sites (dimmed grey dots)
dimmed_sites = [(140, 39), (142, 42), (148, 43), (150, 46), (145, 30), (148, 33)]
for dx, dy in dimmed_sites:
    ax.add_patch(Circle((dx, dy), 0.7, facecolor='#64748B', edgecolor='#334155', linewidth=0.5, zorder=5))

# MATCHING SITES IN SPAIN (Glowing green pulse rings)
spain_sites = [(133, 27), (135, 29), (132, 31), (136, 26)]
for sx, sy in spain_sites:
    ax.add_patch(Circle((sx, sy), 2.4, facecolor='#10B981', alpha=0.25, zorder=5))
    ax.add_patch(Circle((sx, sy), 1.5, facecolor='#10B981', alpha=0.55, zorder=6))
    ax.add_patch(Circle((sx, sy), 0.7, facecolor='#FFFFFF', edgecolor='#059669', linewidth=1.0, zorder=7))

# MATCHING SITES IN FINLAND (Glowing green pulse rings)
finland_sites = [(158, 56), (160, 60)]
for fx, fy in finland_sites:
    ax.add_patch(Circle((fx, fy), 2.4, facecolor='#10B981', alpha=0.25, zorder=5))
    ax.add_patch(Circle((fx, fy), 1.5, facecolor='#10B981', alpha=0.55, zorder=6))
    ax.add_patch(Circle((fx, fy), 0.7, facecolor='#FFFFFF', edgecolor='#059669', linewidth=1.0, zorder=7))

# Interactive Popup Card over Spain
pop_box = FancyBboxPatch((128, 36), 28, 11, boxstyle="round,pad=0.2",
                         facecolor='#0F172A', edgecolor='#10B981', linewidth=1.2, zorder=8)
ax.add_patch(pop_box)
ax.text(129.5, 44.5, "Penouta Lithium Tailings (ES)", color='#34D399', fontsize=7.2, fontweight='bold', zorder=9)
ax.text(129.5, 41.5, "Storage: Waste Dump  |  Status: Active", color='#E2E8F0', fontsize=6.8, zorder=9)
ax.text(129.5, 38.5, "Lat: 42.18° N, Lon: -7.03° W  |  CRM: Li, Ta", color='#94A3B8', fontsize=6.5, zorder=9)

# Animated Pulse Legend badge inside map
leg_box = FancyBboxPatch((128, 18), 44, 4.5, boxstyle="round,pad=0.2",
                        facecolor='#064E3B', edgecolor='#34D399', linewidth=0.8, zorder=8)
ax.add_patch(leg_box)
ax.add_patch(Circle((130.5, 20.2), 1.1, facecolor='#10B981', alpha=0.4, zorder=9))
ax.add_patch(Circle((130.5, 20.2), 0.5, facecolor='#FFFFFF', zorder=10))
ax.text(133, 20.2, "Active Glowing Pulse Markers (Matching Sites)", color='#D1FAE5', fontsize=7.2, fontweight='bold', va='center', zorder=9)

# Live GPU Telemetry in GIS footer
gpu_foot = FancyBboxPatch((126, 8), 48, 6.5, boxstyle="round,pad=0.2",
                          facecolor='#1E1B4B', edgecolor='#818CF8', linewidth=1.0, zorder=3)
ax.add_patch(gpu_foot)
ax.text(128, 11.2, "Cluster GPU Telemetry: NVIDIA A100 | VRAM: 14.2 GB | Latency: 1.8s", 
        color='#C7D2FE', fontsize=7.0, fontweight='bold', va='center', zorder=4)

# -------------------------------------------------------------
# 5. CONNECTING DATA FLOW ARROWS (Thick, Prominent, Clear Labels)
# -------------------------------------------------------------

# Arrow 1: Chat -> NLU (top)
ax.annotate('', xy=(57, 72), xytext=(52.5, 72),
            arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8", color='#38BDF8', lw=4.0), zorder=10)
ax.text(54.7, 74.5, "Query", color='#38BDF8', fontsize=8.5, fontweight='bold', ha='center', zorder=11)

# Arrow 2: NLU -> Solr (down)
ax.annotate('', xy=(88, 44.5), xytext=(88, 49.5),
            arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8", color='#818CF8', lw=4.0), zorder=10)
ax.text(90, 47, "OpenAPI Slots", color='#818CF8', fontsize=8.5, fontweight='bold', va='center', zorder=11)

# Arrow 3: Solr -> GIS Map (bottom right)
ax.annotate('', xy=(123.5, 32), xytext=(118.5, 32),
            arrowprops=dict(arrowstyle="->,head_width=0.6,head_length=0.8", color='#F59E0B', lw=4.0), zorder=10)
ax.text(121, 34.5, "Spatial\nFilters", color='#F59E0B', fontsize=8.0, fontweight='bold', ha='center', va='bottom', zorder=11)

# Arrow 4: GIS Map -> Feedback to Chat (Loop at Bottom)
path_return = FancyArrowPatch((124, 12), (52.5, 12),
                              connectionstyle="arc3,rad=-0.15",
                              arrowstyle="->,head_width=0.7,head_length=0.9",
                              color='#10B981', lw=3.5, linestyle='--', zorder=10)
ax.add_patch(path_return)
ax.text(88, 2.5, "Synchronized Cartographic Feedback Loop & Evidence Citations", 
        color='#34D399', fontsize=9.2, fontweight='bold', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#064E3B', edgecolor='#10B981', lw=1.2), zorder=11)

plt.tight_layout()
plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='#0B1329')
plt.close()
print(f"Successfully generated new visual graphical abstract at: {out_png}")
