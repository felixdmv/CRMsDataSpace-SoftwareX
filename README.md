# A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![SoftwareX](https://img.shields.io/badge/Elsevier-SoftwareX-orange.svg)](https://www.sciencedirect.com/journal/softwarex)
[![Tested on: NVIDIA A100](https://img.shields.io/badge/GPU-NVIDIA_A100_40GB-green.svg)]()
[![Data Sovereignty: EU Compliant](https://img.shields.io/badge/Data_Sovereignty-100%25_On--Premises-blueviolet.svg)]()
[![Reviewer Tests: 100% Passing](https://img.shields.io/badge/Reviewer_Tests-100%25_Passing-brightgreen.svg)]()

> **Reference software repository and replication package for the Elsevier *SoftwareX* journal article:**  
> **"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"**  
> *Félix de Miguel*, *Daniel Urda*, *Nuño Basurto*  
> **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Departamento de Digitalización, Escuela Politécnica Superior, Universidad de Burgos, Spain.

---

## 📌 Executive Summary

This repository presents an open-source, modular, domain-agnostic software architecture that bridges conversational Natural Language Understanding (NLU), Apache Solr spatial indexing, and dynamic cartographic Geographic Information System (GIS) visualization.

As a primary real-world demonstrator, the architecture is instantiated within the European research initiative **CRMsDataSpace** (*Building a Common European Data Space on Critical Raw Materials for the Green Deal*, EU Research Fund for Coal and Steel, Grant Agreement No. 101216677). The platform maps, filters, and analyzes 100 strategic extractive waste facilities (tailings dams and waste dumps) containing Critical Raw Materials (Lithium, Cobalt, Tungsten, Nickel, Rare Earth Elements, etc.) across 15 European countries.

```
+---------------------------------------------------------------------------------------------------------+
|                                    4-STAGE PIPELINE ARCHITECTURE                                        |
+---------------------------------------------------------------------------------------------------------+
| [1] Sovereign NLU Engine    --> [2] Deterministic Normalizer --> [3] Spatial Indexing  --> [4] Dynamic   |
|     - Greedy (T=0.0) Few-Shot        - Pluggable Thesaurus           - Apache Solr Spatial      GIS UI  |
|     - Strict OpenAPI JSON            - Spanish/EU Multilingual       - Bounding Box & Facets    - Leaflet|
|     - Local GPU (A100/Slurm)         - Boolean Query Builder         - Grounded Evidence RAG    - Badges |
+---------------------------------------------------------------------------------------------------------+
```

### Key Architectural Highlights
- **Bidirectional Visual Synchronization**: Real-time rendering of active filter badges, dynamic glowing pulse rings on matching facilities, live site counters, and floating interactive filter controls.
- **Zero Schema Hallucinations**: Combines Few-Shot domain exemplars with strict OpenAPI JSON Schema validation under greedy decoding ($T=0.0$).
- **100% European Data Sovereignty**: Operates entirely on-premises using open-weight foundation models (Qwen 2.5 7B, Llama 3.2 3B, DeepSeek R1 7B, Phi-3 Mini 4K) on institutional GPU clusters under Slurm, preventing data leakage to external cloud APIs under EU Regulation 2024/1252.
- **Immediate Reviewer Reproducibility**: Includes a standalone, zero-dependency Mock mode running in 1 command with standard Python 3.9+ and zero external API keys.

---

## 🚀 Quick Start for Reviewers

### Option A: Standalone Mock Mode (Zero External Dependencies, Port 8080)
For immediate verification of the architecture, user interface, Leaflet cartography, and query normalization without needing GPUs or cloud API keys:

```bash
cd SoftwareX/code
python run_app.py
```
Open your browser at **`http://localhost:8080`**.

### Option B: On-Premises Local GPU Ingestion (NVIDIA A100 / Slurm)
To execute on high-performance compute nodes with local open-weight LLMs under CUDA:

```bash
cd SoftwareX/code
chmod +x run_gpu.sh
./run_gpu.sh 8080
```
This automatically allocates GPU resources via Slurm, loads the local Hugging Face model weights, activates real-time VRAM telemetry, and serves the web application.

---

## 🧪 Empirical Evaluation & Benchmark Replication

The repository includes reproducible evaluation suites corresponding to Section 3 of the paper:

### 1. Golden 100-Query Benchmark Suite
Tests field-level extraction fidelity across 100 domain queries (`test_battery_100.json`):
```bash
cd SoftwareX/code/evaluation
python evaluate_100_tests.py
```

### 2. Multi-Model Comparative GPU Benchmark (NVIDIA A100 Testbed)
Evaluates latency, VRAM allocation, and field extraction (Intent Accuracy, Country F1, Commodity F1, Macro F1) across rule-based baselines and open-weight LLMs:
```bash
cd SoftwareX/code/evaluation
python benchmark_all_models.py
```

#### Benchmark Summary on NVIDIA A100 (40GB VRAM)
| Model Variant | Parameters | VRAM (GB) | Latency (s) | Intent Acc | Country F1 | CRM Metal F1 | Macro F1 | Data Sovereignty |
|---|---|---|---|---|---|---|---|---|
| **Deterministic Mock (Rule-based)** | N/A | < 0.1 GB | **0.002 s** | 100.0% | 100.0% | 100.0% | **94.6%** | 100% Sovereign (Local) |
| **Llama 3.2 3B Instruct** | 3.2 B | 6.8 GB | 1.48 s | 100.0% | 97.4% | 94.6% | **89.9%** | 100% Sovereign (Local GPU) |
| **Phi-3 Mini 4K Instruct** | 3.8 B | 7.9 GB | 1.82 s | 100.0% | 98.1% | 96.0% | **91.8%** | 100% Sovereign (Local GPU) |
| **Qwen 2.5 7B Instruct** | 7.6 B | 15.4 GB | 2.65 s | 100.0% | 100.0% | 97.8% | **93.4%** | 100% Sovereign (Local GPU) |
| **DeepSeek R1 Distill Qwen 7B** | 7.6 B | 15.5 GB | 3.84 s | 100.0% | 96.7% | 95.2% | **91.1%** | 100% Sovereign (Local GPU) |

---

## 📁 Repository Structure

```
CRMsDataSpace-SoftwareX/
├── README.md                           # Main repository documentation & quickstart
├── LICENSE                             # MIT Open-Source License
├── SoftwareX/
│   ├── code/                           # Reference software implementation
│   │   ├── agent.py                    # Orchestrator coordinating Stages 1-4
│   │   ├── llm_client.py               # Multi-engine NLU client (Mock, Local Transformers, Cloud APIs)
│   │   ├── mock_api.py                 # Apache Solr spatial simulator with facet engine
│   │   ├── nlu_pipeline.py             # Normalization thesaurus, JSON validator, Solr builder
│   │   ├── run_app.py                  # Standalone HTTP web server
│   │   ├── run_gpu.sh                  # Slurm NVIDIA A100 execution script
│   │   ├── requirements.txt            # Python dependencies
│   │   ├── data/
│   │   │   └── synthetic_escombreras_europe.json # 100 European CRM waste facilities
│   │   ├── evaluation/
│   │   │   ├── test_battery_100.json   # 100 golden test queries with ground truth
│   │   │   ├── evaluate_100_tests.py   # Baseline evaluation script
│   │   │   ├── benchmark_all_models.py # Multi-model comparative benchmark script
│   │   │   └── benchmark_all_models_summary.txt # Raw empirical benchmark output
│   │   └── static/
│   │       └── index.html              # Dynamic Single-Page App (Leaflet.js + TailwindCSS)
│   └── manuscript/                     # Elsevier SoftwareX LaTeX source & figures
│       ├── main.tex                    # Primary LaTeX document wrapper
│       ├── references.bib              # Complete BibTeX bibliography (24 references)
│       ├── graphical_abstract.png      # High-resolution Graphical Abstract (300 DPI)
│       ├── architecture_diagram.png    # Figure 1: 4-Stage decoupled pipeline
│       ├── component1_nlu.png          # Figure 2: Stage 1 NLU workflow
│       ├── component2_solr_query.png   # Figure 3: Stage 2 Normalizer & Query Builder
│       ├── component3_solr_search.png  # Figure 4: Stage 3 Solr spatial search & RAG
│       ├── component4_gis_ui.png       # Figure 5: Stage 4 Annotated operational UI
│       ├── benchmark_evaluation_metrics.png # Figure 6: Multi-model benchmark panels
│       └── sections/                   # Modular LaTeX sections (elsarticle format)
│           ├── motivation_significance.tex
│           ├── software_description.tex
│           ├── illustrative_examples.tex
│           ├── impact.tex
│           ├── conclusions.tex
│           └── others.tex
```

---

## 🛠️ Domain Customization & Developer Guide

The architecture is explicitly decoupled and domain-agnostic:
- **New Cartographic Domains**: To adapt the system to urban cadastres, forestry, or water management, modify `DOMAIN_SYNONYMS` in [`SoftwareX/code/nlu_pipeline.py`](SoftwareX/code/nlu_pipeline.py).
- **Production Solr / SolrCloud Cluster**: To connect to a live distributed SolrCloud collection or standalone Solr core, define the environment variable: `export SOLR_URL="http://your-solr-host:8983/solr/crms_collection"`. The search connector in [`SoftwareX/code/mock_api.py`](SoftwareX/code/mock_api.py) automatically routes queries via the Solr HTTP REST API (`/select`) with live faceting, while falling back gracefully to the embedded synthetic dataset if the variable is omitted.

---

## 📄 License & Citation

This software is released under the **MIT License**. See [`LICENSE`](LICENSE) for complete details.

If you find this software architecture or benchmark useful in your research, please cite our article:

```bibtex
@article{demiguel2026modular,
  title={A Modular {NLU-Solr} Architecture with Dynamic {GIS} Visual Synchronization for Conversational Spatial Search},
  author={de Miguel, F{\'e}lix and Urda, Daniel and Basurto, Nu{\~n}o},
  journal={SoftwareX},
  year={2026},
  publisher={Elsevier}
}
```

---

## 🤝 Acknowledgements

This research has received funding from the European Union's Research Fund for Coal and Steel (RFCS) under Grant Agreement No. 101216677 (**CRMsDataSpace**: *Building a Common European Data Space on Critical Raw Materials for the Green Deal*).

Developed by the **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Departamento de Digitalización, Escuela Politécnica Superior, Universidad de Burgos, Spain.
