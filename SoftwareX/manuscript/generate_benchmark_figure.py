import os
import matplotlib.pyplot as plt
import numpy as np

# Styling configuration
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#94A3B8'
plt.rcParams['axes.linewidth'] = 0.8

models = [
    'Deterministic\nBaseline (Mock)',
    'Llama 3.2\n(3B)',
    'Phi-3 Mini\n(3.8B)',
    'Qwen 2.5\n(7B)'
]

intent_acc = [80.0, 98.0, 100.0, 100.0]
country_f1 = [80.5, 86.0, 75.4, 94.5]
metal_f1 = [67.5, 71.0, 66.7, 90.1]
macro_f1 = [74.9, 75.9, 75.3, 93.1]

vram_gb = [0.0, 6.0, 7.1, 14.2]
latency_sec = [0.0004, 1.91, 2.92, 1.81]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.8), dpi=300)
fig.patch.set_facecolor('#FFFFFF')

# -------------------------------------------------------------
# Panel A: NLU Accuracy & Extraction F1-Score Comparison
# -------------------------------------------------------------
ax1.set_facecolor('#FAFAFA')
x = np.arange(len(models))
width = 0.19

c1 = '#2563EB'  # Royal blue: Intent Acc
c2 = '#059669'  # Emerald green: Country F1
c3 = '#D97706'  # Amber: Metal F1
c4 = '#7C3AED'  # Violet: Macro F1

r1 = ax1.bar(x - 1.5*width, intent_acc, width, label='Intent Accuracy (%)', color=c1, alpha=0.9, edgecolor='none')
r2 = ax1.bar(x - 0.5*width, country_f1, width, label='Country F1 (%)', color=c2, alpha=0.9, edgecolor='none')
r3 = ax1.bar(x + 0.5*width, metal_f1, width, label='CRM Metal F1 (%)', color=c3, alpha=0.9, edgecolor='none')
r4 = ax1.bar(x + 1.5*width, macro_f1, width, label='Overall Macro F1 (%)', color=c4, alpha=0.95, edgecolor='none')

ax1.set_ylabel('Extraction Accuracy & F1-Score (%)', fontsize=11, fontweight='bold', color='#1E293B')
ax1.set_title('(a) NLU Intent & Entity Extraction Fidelity across 100 Queries', fontsize=12, fontweight='bold', color='#0F172A', pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=9.5, fontweight='bold', color='#334155')
ax1.set_ylim(55, 110)
ax1.grid(axis='y', linestyle='--', alpha=0.5, color='#CBD5E1')
ax1.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=8.5)

# Value annotations for macro F1
for bar in r4:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0, f'{yval:.1f}%',
             ha='center', va='bottom', fontsize=8, fontweight='bold', color='#5B21B6')

# -------------------------------------------------------------
# Panel B: Resource Efficiency on NVIDIA A100 GPU (VRAM vs Latency)
# -------------------------------------------------------------
ax2.set_facecolor('#FAFAFA')
ax2_twin = ax2.twinx()

bar_width = 0.35
x_idx = np.arange(len(models))

# VRAM bars on ax2 (left Y)
bars_vram = ax2.bar(x_idx - bar_width/2, vram_gb, bar_width, label='Allocated VRAM (GB)', color='#6366F1', alpha=0.85)
# Latency bars on ax2_twin (right Y)
bars_lat = ax2_twin.bar(x_idx + bar_width/2, latency_sec, bar_width, label='Mean Latency (s)', color='#F59E0B', alpha=0.85)

ax2.set_ylabel('GPU VRAM Allocation (GB)', fontsize=11, fontweight='bold', color='#4338CA')
ax2_twin.set_ylabel('Mean Query Latency (seconds)', fontsize=11, fontweight='bold', color='#B45309')
ax2.set_title('(b) Compute Footprint & Inference Latency on NVIDIA A100', fontsize=12, fontweight='bold', color='#0F172A', pad=12)

ax2.set_xticks(x_idx)
ax2.set_xticklabels(models, fontsize=9.5, fontweight='bold', color='#334155')
ax2.set_ylim(0, 18)
ax2_twin.set_ylim(0, 3.8)

ax2.grid(axis='y', linestyle='--', alpha=0.4, color='#CBD5E1')

# Add text labels on bars
for bar in bars_vram:
    val = bar.get_height()
    if val > 0:
        ax2.text(bar.get_x() + bar.get_width()/2.0, val + 0.4, f'{val:.1f} GB',
                 ha='center', va='bottom', fontsize=8, fontweight='bold', color='#4338CA')
    else:
        ax2.text(bar.get_x() + bar.get_width()/2.0, 0.4, '0 (RAM)',
                 ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#475569')

for bar in bars_lat:
    val = bar.get_height()
    if val > 0.01:
        ax2_twin.text(bar.get_x() + bar.get_width()/2.0, val + 0.15, f'{val:.2f}s',
                      ha='center', va='bottom', fontsize=8, fontweight='bold', color='#B45309')
    else:
        ax2_twin.text(bar.get_x() + bar.get_width()/2.0, 0.15, '<1ms',
                      ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#B45309')

# Combine legends for ax2 and ax2_twin
lines_1, labels_1 = ax2.get_legend_handles_labels()
lines_2, labels_2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=8.5)

# A100 testbed badge placed cleanly at top center
ax2.text(0.50, 0.88, "Testbed: 1x NVIDIA A100-PCIE-40GB\nPrecision: FP16 | Slurm private cluster",
         transform=ax2.transAxes, fontsize=8, ha='center', va='center',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#EFF6FF', edgecolor='#BFDBFE', lw=1),
         color='#1E40AF', fontweight='medium')

plt.tight_layout()

out_path = "/home/felix.demiguel/contenido_computo03_felix/CRMsDataSpace/SoftwareX/manuscript/benchmark_evaluation_metrics.png"
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Successfully generated {out_path}")
