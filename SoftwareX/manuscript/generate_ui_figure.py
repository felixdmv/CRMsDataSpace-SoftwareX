import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams['font.family'] = 'sans-serif'
from pathlib import Path
out_path = Path(__file__).resolve().parent / "component4_gis_ui.png"

fig, ax = plt.subplots(figsize=(16, 9.8), dpi=300)
ax.set_xlim(0, 160)
ax.set_ylim(0, 98)
ax.axis('off')
fig.patch.set_facecolor('#040711')

# -------------------------------------------------------------
# 1. TOP HEADER BAR
# -------------------------------------------------------------
header = FancyBboxPatch((0, 90), 160, 8, boxstyle="square,pad=0",
                        facecolor='#0a0e1c', edgecolor='#1e293b', linewidth=1.2, zorder=2)
ax.add_patch(header)

# Title & Badge
ax.text(3.5, 94.8, "CRMsDataSpace Explorer", color='#F8FAFC', fontsize=12, fontweight='bold', va='center')
badge = FancyBboxPatch((30.5, 93.7), 28, 2.3, boxstyle="round,pad=0.2",
                       facecolor='#022c22', edgecolor='#059669', linewidth=0.8, zorder=3)
ax.add_patch(badge)
ax.text(44.5, 94.85, "SoftwareX Reference Architecture v1.0.0", color='#34D399', fontsize=7.5, fontweight='bold', ha='center', va='center', zorder=4)
ax.text(3.5, 92.0, "Conversational NLU & Solr Spatial Filtering for European Critical Raw Materials", color='#94A3B8', fontsize=8, va='center')

# Header Right Controls: Live GPU Telemetry & Solr Status
gpu_box = FancyBboxPatch((104, 91.2), 34, 5.2, boxstyle="round,pad=0.3",
                         facecolor='#0f172a', edgecolor='#8B5CF6', linewidth=1.2, zorder=3)
ax.add_patch(gpu_box)
circle_gpu = Circle((106.8, 93.8), 0.9, facecolor='#8B5CF6', edgecolor='none', zorder=4)
ax.add_patch(circle_gpu)
ax.text(109.0, 94.7, "GPU: NVIDIA A100-PCIE-40GB", color='#E2E8F0', fontsize=7.5, fontweight='bold', zorder=4)
ax.text(109.0, 92.7, "VRAM: 14.2 GB / 40.0 GB (35%) | FP16", color='#A78BFA', fontsize=7.0, fontweight='semibold', zorder=4)

solr_box = FancyBboxPatch((140, 91.2), 17.5, 5.2, boxstyle="round,pad=0.3",
                          facecolor='#022c22', edgecolor='#059669', linewidth=1, zorder=3)
ax.add_patch(solr_box)
circle_solr = Circle((142.2, 93.8), 0.7, facecolor='#10B981', edgecolor='none', zorder=4)
ax.add_patch(circle_solr)
ax.text(144.2, 94.7, "Solr Spatial Core", color='#F8FAFC', fontsize=7.2, fontweight='bold', zorder=4)
ax.text(144.2, 92.7, "100 Active Records", color='#34D399', fontsize=6.8, zorder=4)

# -------------------------------------------------------------
# 2. ACTIVE FILTERS SUB-BAR
# -------------------------------------------------------------
subbar = FancyBboxPatch((0, 85.0), 160, 5.0, boxstyle="square,pad=0",
                        facecolor='#0B1021', edgecolor='#1E293B', linewidth=1, zorder=2)
ax.add_patch(subbar)
ax.text(6.8, 87.5, "ACTIVE FILTERS:", color='#94A3B8', fontsize=7.8, fontweight='bold', va='center')

def draw_filter_pill(x, w, label, color_bg, color_border, color_text):
    pill = FancyBboxPatch((x, 85.8), w, 3.4, boxstyle="round,pad=0.2",
                          facecolor=color_bg, edgecolor=color_border, linewidth=1, zorder=3)
    ax.add_patch(pill)
    ax.text(x + w/2, 87.5, label, color=color_text, fontsize=7.2, fontweight='bold', ha='center', va='center', zorder=4)

draw_filter_pill(23, 24, "Country: Spain, Finland", "#1E1B4B", "#4338CA", "#A5B4FC")
draw_filter_pill(49, 25, "Commodity: Lithium, Cobalt", "#022C22", "#059669", "#6EE7B7")
draw_filter_pill(76, 18, "Facility: Waste Dumps", "#2E1065", "#7C3AED", "#D8B4FE")
draw_filter_pill(96, 15, "Status: Active", "#14532D", "#15803D", "#86EFAC")

ax.text(113.5, 87.5, "Matches: 12 European Facilities Found", color='#38BDF8', fontsize=8, fontweight='bold', va='center')

# -------------------------------------------------------------
# 3. LEFT PANEL: INTERACTIVE LEAFLET GIS MAP
# -------------------------------------------------------------
map_bg = FancyBboxPatch((2, 19), 96, 64, boxstyle="round,pad=0.3",
                        facecolor='#070A14', edgecolor='#1E293B', linewidth=1.5, zorder=2)
ax.add_patch(map_bg)

# Simulated European Landmass outline (Stylized Vector Shapes)
# Iberian Peninsula
spain_poly = patches.Polygon([[8, 30], [24, 30], [27, 42], [18, 47], [10, 44], [7, 36]],
                             closed=True, facecolor='#0D1527', edgecolor='#1E293B', lw=1.2, zorder=3)
ax.add_patch(spain_poly)
ax.text(16, 37, "SPAIN", color='#334155', fontsize=8, fontweight='bold', zorder=4)

# France
france_poly = patches.Polygon([[23, 45], [35, 45], [37, 58], [26, 59], [21, 50]],
                              closed=True, facecolor='#0B1220', edgecolor='#1E293B', lw=1.2, zorder=3)
ax.add_patch(france_poly)
ax.text(28, 51, "FRANCE", color='#1E293B', fontsize=7.5, fontweight='bold', zorder=4)

# Central Europe (Germany / Poland)
germany_poly = patches.Polygon([[37, 52], [52, 52], [54, 64], [38, 65]],
                               closed=True, facecolor='#0B1220', edgecolor='#1E293B', lw=1.2, zorder=3)
ax.add_patch(germany_poly)
ax.text(44, 57, "GERMANY / POLAND", color='#1E293B', fontsize=7, fontweight='bold', zorder=4)

# Scandinavia & Finland
nordic_poly = patches.Polygon([[48, 66], [57, 66], [62, 80], [52, 81]],
                              closed=True, facecolor='#0D1527', edgecolor='#1E293B', lw=1.2, zorder=3)
ax.add_patch(nordic_poly)
ax.text(54, 74, "FINLAND", color='#334155', fontsize=8, fontweight='bold', zorder=4)

# Inactive/Dimmed Sites (small grey dots)
dimmed_sites = [(25, 48), (32, 55), (42, 58), (49, 60), (36, 49), (19, 41)]
for sx, sy in dimmed_sites:
    ax.add_patch(Circle((sx, sy), 0.6, facecolor='#334155', edgecolor='#1E293B', lw=0.5, alpha=0.4, zorder=5))

# Matching Active Sites with GLOWING PULSE RINGS (Emerald & Gold)
active_sites_spain = [(13, 35), (16, 39), (18, 34), (12, 40)]
for sx, sy in active_sites_spain:
    ax.add_patch(Circle((sx, sy), 2.8, facecolor='#059669', alpha=0.15, zorder=5))
    ax.add_patch(Circle((sx, sy), 1.8, facecolor='#10B981', alpha=0.35, zorder=6))
    ax.add_patch(Circle((sx, sy), 0.9, facecolor='#34D399', edgecolor='#FFFFFF', lw=1.2, zorder=7))

active_sites_finland = [(53, 71), (56, 75), (54, 78)]
for sx, sy in active_sites_finland:
    ax.add_patch(Circle((sx, sy), 2.8, facecolor='#D97706', alpha=0.15, zorder=5))
    ax.add_patch(Circle((sx, sy), 1.8, facecolor='#F59E0B', alpha=0.35, zorder=6))
    ax.add_patch(Circle((sx, sy), 0.9, facecolor='#FCD34D', edgecolor='#FFFFFF', lw=1.2, zorder=7))

# Facility Detail Popup on San José Valdeflórez
popup = FancyBboxPatch((23, 31), 38, 16, boxstyle="round,pad=0.4",
                       facecolor='#0F172A', edgecolor='#10B981', linewidth=1.5, zorder=10)
ax.add_patch(popup)
ax.text(25, 44.2, "San José Valdeflórez (Cáceres, Spain)", color='#FFFFFF', fontsize=8, fontweight='bold', zorder=11)
ax.text(25, 41.7, "Commodities: Lithium (Li), Tin (Sn)", color='#34D399', fontsize=7.2, fontweight='bold', zorder=11)
ax.text(25, 39.5, "Storage Type: Extractive Waste Dump", color='#CBD5E1', fontsize=7, zorder=11)
ax.text(25, 37.3, "Status: Active | AMD Risk: Low | Restored: False", color='#94A3B8', fontsize=6.8, zorder=11)
ax.text(25, 35.1, "Coordinates: 39.462° N, 6.371° W | Solr ID: CRM-ES-014", color='#64748B', fontsize=6.5, fontfamily='monospace', zorder=11)
ax.plot([16, 23], [39, 39], color='#10B981', lw=1.2, linestyle='--', zorder=11)

# Map UI Controls (Zoom buttons & Legend)
zoom_box = FancyBboxPatch((4, 69), 4, 8, boxstyle="round,pad=0.1",
                          facecolor='#0F172A', edgecolor='#334155', linewidth=1, zorder=10)
ax.add_patch(zoom_box)
ax.text(6, 74.5, "+", color='#FFFFFF', fontsize=12, fontweight='bold', ha='center', va='center', zorder=11)
ax.plot([4.5, 7.5], [73, 73], color='#334155', lw=1, zorder=11)
ax.text(6, 71.0, "−", color='#FFFFFF', fontsize=14, fontweight='bold', ha='center', va='center', zorder=11)

# Map Legend
leg_box = FancyBboxPatch((4, 21), 33, 8.0, boxstyle="round,pad=0.2",
                         facecolor='#0B1021', edgecolor='#1E293B', linewidth=1, zorder=10)
ax.add_patch(leg_box)
ax.add_patch(Circle((6.5, 26.5), 0.7, facecolor='#34D399', edgecolor='#FFFFFF', lw=0.8, zorder=11))
ax.text(8.8, 26.5, "Active CRM Waste (Spain)", color='#E2E8F0', fontsize=6.8, fontweight='bold', va='center', zorder=11)
ax.add_patch(Circle((6.5, 23.3), 0.7, facecolor='#FCD34D', edgecolor='#FFFFFF', lw=0.8, zorder=11))
ax.text(8.8, 23.3, "Active CRM Waste (Finland)", color='#E2E8F0', fontsize=6.8, fontweight='bold', va='center', zorder=11)


# -------------------------------------------------------------
# 4. RIGHT PANEL: GROUNDED CONVERSATIONAL CHAT & RAG
# -------------------------------------------------------------
chat_bg = FancyBboxPatch((100, 19), 58, 64, boxstyle="round,pad=0.3",
                         facecolor='#0B1021', edgecolor='#1E293B', linewidth=1.5, zorder=2)
ax.add_patch(chat_bg)

# Chat Header
ax.text(103, 80, "Conversational Spatial Search", color='#F8FAFC', fontsize=10, fontweight='bold', zorder=4)
ax.text(103, 77.8, "Model: Qwen 2.5 7B Instruct (CUDA Local A100 | Zero Cloud Leakage)", color='#A78BFA', fontsize=7, fontweight='semibold', zorder=4)
ax.plot([102, 156], [76.5, 76.5], color='#1E293B', lw=1, zorder=4)

# User Message Bubble
user_bubble = FancyBboxPatch((103, 66), 52, 8.5, boxstyle="round,pad=0.4",
                             facecolor='#1E1B4B', edgecolor='#4338CA', linewidth=1.2, zorder=4)
ax.add_patch(user_bubble)
ax.text(105, 72.2, "User Query (ES/EN):", color='#A5B4FC', fontsize=7.2, fontweight='bold', zorder=5)
ax.text(105, 69.5, '"Muestra escombreras de litio y cobalto en España y Finlandia', color='#FFFFFF', fontsize=7.8, fontweight='medium', zorder=5)
ax.text(105, 67.5, 'que estén activas"', color='#FFFFFF', fontsize=7.8, fontweight='medium', zorder=5)

# Assistant Synthesized Response Bubble
asst_bubble = FancyBboxPatch((103, 36), 52, 28, boxstyle="round,pad=0.4",
                             facecolor='#0F172A', edgecolor='#059669', linewidth=1.2, zorder=4)
ax.add_patch(asst_bubble)
ax.text(105, 61.8, "Grounded RAG Assistant (Solr + FAISS):", color='#34D399', fontsize=7.5, fontweight='bold', zorder=5)
ax.text(105, 59.2, "Se han localizado 12 instalaciones de residuos extractivos activas", color='#E2E8F0', fontsize=7.2, zorder=5)
ax.text(105, 57.2, "con presencia de Litio y Cobalto en España (7) y Finlandia (5).", color='#E2E8F0', fontsize=7.2, zorder=5)
ax.text(105, 54.8, "• España: Destacan los depósitos de San José Valdeflórez", color='#94A3B8', fontsize=7.0, zorder=5)
ax.text(105, 52.8, "  (Cáceres) y Penouta, con enriquecimiento en Li-Sn.", color='#94A3B8', fontsize=7.0, zorder=5)
ax.text(105, 50.4, "• Finlandia: Complejo Keliber en Kaustinen y escombreras", color='#94A3B8', fontsize=7.0, zorder=5)
ax.text(105, 48.4, "  asociadas al cinturón de esquistos de Kokkola.", color='#94A3B8', fontsize=7.0, zorder=5)

# Evidence Cards
card1 = FancyBboxPatch((105, 38), 23.5, 8.5, boxstyle="round,pad=0.2",
                       facecolor='#022C22', edgecolor='#059669', linewidth=0.8, zorder=6)
ax.add_patch(card1)
ax.text(106, 44.5, "[PDF] Tech. Report: Keliber Basin", color='#34D399', fontsize=6.5, fontweight='bold', zorder=7)
ax.text(106, 42.5, "Page 14 | Score: 0.94", color='#6EE7B7', fontsize=6.2, zorder=7)
ax.text(106, 40.0, "Tailings classification Li-Co", color='#94A3B8', fontsize=5.8, zorder=7)

card2 = FancyBboxPatch((130, 38), 23.5, 8.5, boxstyle="round,pad=0.2",
                       facecolor='#1E1B4B', edgecolor='#4338CA', linewidth=0.8, zorder=6)
ax.add_patch(card2)
ax.text(131, 44.5, "[PDF] Plan Restauración Minera", color='#A5B4FC', fontsize=6.5, fontweight='bold', zorder=7)
ax.text(131, 42.5, "Junta Extremadura | p. 8", color='#C7D2FE', fontsize=6.2, zorder=7)
ax.text(131, 40.0, "Environmental AMD survey", color='#94A3B8', fontsize=5.8, zorder=7)

# Prompt Input Bar
input_box = FancyBboxPatch((103, 21), 43, 6, boxstyle="round,pad=0.3",
                           facecolor='#070A14', edgecolor='#334155', linewidth=1, zorder=4)
ax.add_patch(input_box)
ax.text(105, 24.5, "Escribe una consulta espacial en lenguaje natural...", color='#64748B', fontsize=7, zorder=5)

send_btn = FancyBboxPatch((147.5, 21), 7.5, 6, boxstyle="round,pad=0.3",
                          facecolor='#059669', edgecolor='none', zorder=4)
ax.add_patch(send_btn)
ax.text(151.2, 24.5, "Send", color='#FFFFFF', fontsize=7.5, fontweight='bold', ha='center', va='center', zorder=5)


# -------------------------------------------------------------
# 5. BOTTOM DRAWER: DEVELOPER INSPECTION PANEL (Solr & NLU Audit)
# -------------------------------------------------------------
drawer_bg = FancyBboxPatch((2, 2.0), 156, 15.0, boxstyle="round,pad=0.3",
                           facecolor='#090D1A', edgecolor='#3B82F6', linewidth=1.2, zorder=3)
ax.add_patch(drawer_bg)

ax.text(7.5, 14.5, "DEVELOPER PIPELINE INSPECTION DRAWER (Real-time Pipeline State & Execution Audit)", color='#60A5FA', fontsize=8.2, fontweight='bold', zorder=4)

# Box Left: NLU Extracted Slots
nlu_box = FancyBboxPatch((4.5, 3.5), 72, 9.5, boxstyle="round,pad=0.2",
                         facecolor='#030712', edgecolor='#1F2937', linewidth=0.8, zorder=4)
ax.add_patch(nlu_box)
ax.text(6.0, 11.2, "Stage 1 & 2: Extracted NLU Slots (OpenAPI JSON)", color='#93C5FD', fontsize=7.0, fontweight='bold', zorder=5)
ax.text(6.0, 9.0, '{"intent": "spatial_search", "country": ["Spain", "Finland"], "commodities": ["Lithium", "Cobalt"],',
        color='#A5F3FC', fontsize=6.6, fontfamily='monospace', zorder=5)
ax.text(6.0, 7.0, ' "facility_type": ["waste_dump"], "status": ["Active"], "amd_risk": null, "confidence": 0.985}',
        color='#A5F3FC', fontsize=6.6, fontfamily='monospace', zorder=5)

# Box Right: Solr Spatial Parameters
solr_box2 = FancyBboxPatch((80.5, 3.5), 75.5, 9.5, boxstyle="round,pad=0.2",
                          facecolor='#030712', edgecolor='#1F2937', linewidth=0.8, zorder=4)
ax.add_patch(solr_box2)
ax.text(82.0, 11.2, "Stage 3: Generated Solr Spatial Query Parameters", color='#86EFAC', fontsize=7.0, fontweight='bold', zorder=5)
ax.text(82.0, 9.0, 'q=*:* & fq=country:("Spain" OR "Finland") AND commodities:("Lithium" OR "Cobalt") AND status:"Active"',
        color='#BBF7D0', fontsize=6.6, fontfamily='monospace', zorder=5)
ax.text(82.0, 7.0, '& facet=true & facet.field=commodities & facet.field=country & rows=100 & wt=json [Latency: 1.2ms]',
        color='#BBF7D0', fontsize=6.6, fontfamily='monospace', zorder=5)


# -------------------------------------------------------------
# 6. ELEGANT ANNOTATION CALLOUT CIRCLES (A, B, C, D, E)
# -------------------------------------------------------------
def draw_corner_badge(cx, cy, letter):
    ax.add_patch(Circle((cx, cy), 1.9, facecolor='#DC2626', edgecolor='#FFFFFF', lw=1.6, zorder=30))
    ax.text(cx, cy, letter, color='#FFFFFF', fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=31)

# A: Near GPU badge
draw_corner_badge(100.5, 93.8, "A")
# B: Near active filter label
draw_corner_badge(3.2, 87.5, "B")
# C: Upper map corner
draw_corner_badge(6.0, 80.5, "C")
# D: Upper-right chat corner
draw_corner_badge(154.5, 80.0, "D")
# E: Upper drawer corner
draw_corner_badge(3.8, 14.5, "E")

plt.tight_layout()
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Successfully generated clean annotated UI figure: {out_path}")
