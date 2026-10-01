# A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![SoftwareX](https://img.shields.io/badge/Elsevier-SoftwareX-orange.svg)](https://www.sciencedirect.com/journal/softwarex)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/felixdmv/CRMsDataSpace-SoftwareX)
[![Reviewer Tests: 100% Passing](https://img.shields.io/badge/Reviewer_Tests-100%25_Passing-brightgreen.svg)]()
[![Data Sovereignty: EU Compliant](https://img.shields.io/badge/Data_Sovereignty-100%25_On--Premises-blueviolet.svg)]()

> **Reference software repository and replication package for the Elsevier *SoftwareX* journal article:**  
> **"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"**  
> *Félix de Miguel*, *Daniel Urda*, *Nuño Basurto*  
> **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Departamento de Digitalización, Escuela Politécnica Superior, Universidad de Burgos, Spain.

---

## 📌 Executive Summary

This repository presents an open-source, modular, domain-agnostic software architecture that bridges conversational Natural Language Understanding (NLU), Apache Solr spatial indexing, and dynamic cartographic Geographic Information System (GIS) visualization.

As a primary real-world demonstrator, the architecture is instantiated within the European research initiative **CRMsDataSpace** (*Building a Common European Data Space on Critical Raw Materials for the Green Deal*, EU Research Fund for Coal and Steel, Grant Agreement No. 101216677). The platform maps, filters, and analyzes 100 strategic extractive waste facilities (tailings dams and waste dumps) containing Critical Raw Materials (Lithium, Cobalt, Tungsten, Nickel, Rare Earth Elements, etc.) across 15 European countries.

Additionally, to allow reviewers and developers to test the **generality and reusability** of the framework beyond European mining, this repository includes a **General-Purpose GIS Template Sandbox** ([`template/`](template/)), featuring a domain-agnostic renewable infrastructure dataset and an in-browser **Filter Studio** to create custom filters by hand.

```
+---------------------------------------------------------------------------------------------------------+
|                                    4-STAGE PIPELINE ARCHITECTURE                                        |
+---------------------------------------------------------------------------------------------------------+
| [1] Sovereign NLU Engine    --> [2] Deterministic Normalizer --> [3] Spatial Indexing  --> [4] Dynamic   |
|     - Greedy (T=0.0) Few-Shot        - Pluggable Thesaurus           - Apache Solr Spatial      GIS UI  |
|     - Strict OpenAPI JSON            - Spanish/EU Multilingual       - Bounding Box & Facets    - Leaflet|
|     - Local GPU / CPU Standalone     - Boolean Query Builder         - Grounded Evidence RAG    - Badges |
+---------------------------------------------------------------------------------------------------------+
```

### Key Architectural Highlights
- **Bidirectional Visual Synchronization**: Real-time rendering of active filter badges, dynamic glowing pulse rings on matching facilities, live site counters, and floating interactive filter controls.
- **Zero Schema Hallucinations**: Combines Few-Shot domain exemplars with strict OpenAPI JSON Schema validation under greedy decoding ($T=0.0$).
- **Zero-Dependency Standalone Mode (Reviewer Ready)**: Runs entirely out-of-the-box on standard Python 3.9+ without needing GPU hardware, external cloud accounts, or third-party database servers.
- **100% European Data Sovereignty**: Designed for institutional on-premises deployment using open-weight foundation models (Qwen 2.5 7B, Llama 3.1 8B, Mistral 7B Instruct v0.2, Phi-3 Mini 4K) under Slurm, preventing data leakage under EU Regulation 2024/1252.

---

## 🚀 Reviewer Access & Quick Start Guide

Reviewers can access and evaluate the software through three complementary modalities:

### Method 1: One-Click Cloud Execution (GitHub Codespaces)

Reviewers can launch the entire replication environment in the cloud with zero setup. Clicking the button provisions a single unified Codespace running both applications simultaneously:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/felixdmv/CRMsDataSpace-SoftwareX)

Both web applications are automatically orchestrated in parallel in the background:
- 🇪🇺 **Port 8080**: **CRMsDataSpace WebApp** — Official European Critical Raw Materials demonstrator (100 facilities across 15 countries, multi-model NLU).
- 🌍 **Port 8085**: **General GIS Template Sandbox** — Domain-agnostic sandbox with in-browser **Filter Studio** to create custom filters by hand and test framework generality.

> **Note on Automatic Port Forwarding**: Ports `8080` and `8085` forward automatically upon container startup and will open in separate browser tabs.
>
> **Note on Direct Web Access**: If you prefer an instant zero-editor web preview without VS Code, you can also explore the static deployment directly at: **[https://felixdmv.github.io/CRMsDataSpace-SoftwareX/](https://felixdmv.github.io/CRMsDataSpace-SoftwareX/)**.

---

### Method 2: Local Standalone Execution (Zero Setup, No GPU Required)

Both applications run locally on any machine with standard Python 3.9+:

```bash
# Option A: Launch European Critical Raw Materials Demonstrator (Port 8080)
python run_app.py --port 8080
# Open: http://localhost:8080

# Option B: Launch General-Purpose GIS Architecture Template (Port 8085)
python run_template.py --port 8085
# Open: http://localhost:8085
```

For reviewers running on their personal laptop or desktop (Windows, macOS, Linux) with standard Python 3.9+ and **no GPU required**:

```bash
# 1. Clone the repository
git clone https://github.com/felixdmv/CRMsDataSpace-SoftwareX.git
cd CRMsDataSpace-SoftwareX

# 2. Launch the standalone application (zero external dependencies)
python run_app.py
```

Open your web browser at:
```
http://localhost:8080
```
*(Alternatively, execute `python run_app.py` inside `code/` for identical behavior).*

---

### Method 3: HPC Cluster with GPU Acceleration (NVIDIA A100 / Slurm)
For institutional environments equipped with compute nodes and NVIDIA CUDA GPUs:

```bash
cd code
chmod +x run_gpu.sh
./run_gpu.sh 8080
```
This automatically allocates a GPU node via Slurm inside Apptainer, exposes local open-weight LLMs (Qwen 2.5 7B, Llama 3.1 8B, Mistral 7B Instruct v0.2, Phi-3 Mini 4K), and sets up reverse proxy routing.

---

## 🖥️ Step-by-Step Manual Testing Instructions

Once the web application is loaded in your browser at `http://localhost:8080`:

### 1. Test Preset Benchmark Queries (Reviewer Test Bench)
At the top-left of the chat panel, click any of the preset test scenario buttons:
- **Test 1 (`Test 1: Active Li & Co`)**:
  - *Query*: *"Show active lithium and cobalt waste dumps in Spain and Finland"*
  - *Observed Feedback*:
    - Active Filter Badges: `[Countries: Spain, Finland]`, `[CRM Metal: Lithium, Cobalt]`, `[Status: Active]`.
    - Map View: Automatically pans to Western and Northern Europe; matching facilities display **emerald glowing pulse rings**.
    - Site Counter: Updates to show matching facilities (e.g., `Showing 1 / 100 European Sites`).
    - Assistant Narrative: Generates a factual summary citing deposit names, locations, and operational status.
    - PDF Evidence Cards: Shows grounded citations from technical reports with mineral and country tags.

- **Test 2 (`Test 2: Tungsten Ponds`)**:
  - *Query*: *"Unrestored tungsten tailings ponds in Germany"*
  - *Observed Feedback*: Filters for German facilities containing Tungsten with `restored=false`.

- **Test 3 (`Test 3: REE Deposits`)**:
  - *Query*: *"Rare Earth Elements (REE) facilities in Sweden and France"*
  - *Observed Feedback*: Synchronizes multi-country spatial filters for Critical Raw Materials across Sweden and France.

### 2. Test Free-Text Natural Language Queries
Type your own queries into the input bar at the bottom:
- Try colloquial phrasing or typos: *"escombreras de golfranio en galiza"* $\to$ The thesaurus maps *golfranio* $\to$ *Tungsten* and *galiza* $\to$ *Galicia, Spain*.
- Try negative constraints: *"balsas de mineral que no esten restauradas"* $\to$ maps to `restored=false`.

### 3. Inspect Solr Engine & OpenAPI Schema Telemetry
Click the bottom expandable bar **"Solr Engine Inspector & Telemetry"**:
- **Solr Filter Query (`fq`)**: Displays the deterministic Boolean query generated for Apache Solr.
- **Solr Dynamic Facets**: Real-time facet distributions calculated across the 100-site dataset.
- **Extracted JSON Schema**: The strict OpenAPI JSON object validated by Stage 2.

---

## 🧪 Automated Verification & Benchmark Reproduction

The repository includes fully automated test scripts corresponding to Section 3 of the manuscript:

### 1. Automated API & Engine Verification Suite
Validates request formatting, authentication handlers, and zero-crash fallbacks across Mock, Gemini, GPT-4o, and Claude:
```bash
python code/test_apis.py
```

### 2. Golden 100-Query Benchmark Reproduction
Evaluates intent classification accuracy and field-level F1-scores across all 100 ground-truth queries in `code/evaluation/test_battery_100.json`:
```bash
cd code/evaluation
python evaluate_100_tests.py
```

### 3. Multi-Turn Conversational DST Benchmark (NVIDIA A100 Testbed)
Evaluates expected filter accuracy (Macro F1) across 6 conversational test categories over 132 sequential turns and 30 dialogue episodes:
```bash
sbatch code/evaluation/run_dst_benchmark.sbatch
# Or execute locally with python:
python code/evaluation/benchmark_conversational_dst.py --models mock phi3 mistral llama qwen
```

#### Benchmark Summary on NVIDIA A100 (40GB VRAM) across 132 Conversational Turns
| Inference Model | Family / Vendor | Parameters | VRAM (GB) | Latency | Search | Expand | Refine | Remove | Context | Reset | Global Macro F1 | Data Sovereignty |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Deterministic Baseline (Mock)** | Rule-based | N/A | 0.0 GB | 0.9 ms | 86.0% | 49.8% | 58.8% | 29.9% | 64.8% | 40.0% | **58.5%** | 100% On-Premises (Air-gapped) |
| **Phi-3 Mini 4K Instruct** | Microsoft | 3.82 B | 7.13 GB | 3.73 s | 61.4% | 36.5% | 32.2% | 13.3% | 30.6% | 90.0% | **36.9%** | 100% On-Premises (Private GPU) |
| **Mistral 7B Instruct v0.2** | Mistral AI | 7.24 B | 13.49 GB | 3.65 s | **96.2%** | 92.6% | 80.0% | 64.2% | 86.7% | **100.0%** | **80.7%** | 100% Sovereign (European LLM) |
| **Llama 3.1 8B Instruct** | Meta | 8.03 B | 14.96 GB | 2.47 s | 96.0% | 94.1% | 93.4% | 78.2% | 78.7% | **100.0%** | **88.8%** | 100% On-Premises (Private GPU) |
| **Qwen 2.5 7B Instruct** | Alibaba | 7.61 B | 14.19 GB | 2.02 s | 93.1% | **96.0%** | **97.5%** | **95.3%** | **90.2%** | **100.0%** | **95.0%** | 100% On-Premises (Private GPU) |


---

## 📁 Repository Structure

```
CRMsDataSpace-SoftwareX/
├── .devcontainer/
│   └── devcontainer.json           # Unified Codespaces configuration (auto-forwards 8080 & 8085)
├── run_codespace.py                 # Codespaces background orchestrator for both web applications
├── code/                               # Reference software implementation (European CRMs)
│   ├── agent.py                        # Orchestrator coordinating Stages 1-4
│   ├── llm_client.py                   # Multi-engine NLU client (Mock, Local Transformers, Cloud APIs)
│   ├── mock_api.py                     # Apache Solr spatial simulator with facet engine
│   ├── nlu_pipeline.py                 # Normalization thesaurus, JSON validator, Solr builder
│   ├── run_app.py                      # Standalone HTTP web server (Port 8080)
│   ├── run_gpu.sh                      # Slurm execution script
│   ├── run_gpu_app.py                  # Slurm launcher & reverse proxy
│   ├── test_apis.py                    # Automated verification suite for all engines
│   ├── requirements.txt                # Python dependencies
│   ├── data/
│   │   └── synthetic_escombreras_europe.json # 100 European CRM waste facilities
│   ├── evaluation/
│   │   ├── test_battery_100.json       # 100 golden test queries with ground truth
│   │   ├── test_battery_conversational_dst.json # 132-turn sequential conversational benchmark
│   │   ├── evaluate_100_tests.py       # Baseline evaluation script
│   │   ├── benchmark_conversational_dst.py # Multi-model conversational DST benchmark suite
│   │   ├── benchmark_dst_results.json  # Granular JSON metrics across 5 distinct model families
│   │   ├── benchmark_dst_summary.txt   # Tabulated empirical DST benchmark output
│   │   ├── benchmark_all_models.py     # 100-query single-turn comparative benchmark script
│   │   └── benchmark_all_models_summary.txt # Raw single-turn benchmark output
│   └── static/
│       ├── favicon.ico                 # Application favicon
│       └── index.html                  # Dynamic Single-Page App (Leaflet.js + TailwindCSS)
├── template/                           # General-Purpose GIS Architecture Template & Sandbox
│   ├── README.md                       # Architectural guide & 3-step adaptation recipe
│   ├── filters_config.json             # Declarative filter definitions & thesaurus mapping
│   ├── run_template.py                 # Zero-dependency HTTP server & 4-stage orchestrator
│   ├── run_template.sh                 # Convenient shell launcher
│   ├── requirements.txt                # Zero-dependency specification (Python stdlib)
│   ├── data/
│   │   └── facilities.json             # 30-facility domain-agnostic GIS dataset
│   └── static/
│       ├── favicon.ico                 # App icon
│       └── index.html                  # Reactive Leaflet GIS UI with Live Filter Studio
├── docs/
│   └── index.html                      # Standalone GitHub Pages web demonstrator
├── .gitignore                          # Git exclude rules
├── LICENSE                             # MIT Open-Source License
├── README.md                           # Main documentation & quickstart
├── run_app.py                          # Root standalone launcher for CRMs WebApp (Port 8080)
├── run_demo.sh                         # 1-Click shell launcher for CRMs WebApp
├── run_template.py                     # Root standalone launcher for GIS Template (Port 8085)
├── run_template.sh                     # 1-Click shell launcher for GIS Template
└── run_gpu_app.py                      # Slurm GPU launcher & reverse proxy
```

---

## 🛠️ General-Purpose GIS Template & Filter Customization Studio

The package in [`template/`](template/) (also mirrored at [`SoftwareX/template/`](SoftwareX/template/)) allows reviewers to evaluate the framework's adaptability to **any geospatial domain**:

1. **Interactive In-Browser Filter Studio**:
   - Launch `python run_template.py --port 8085` and open the **"🛠️ Filter Studio"** tab.
   - Add new filter fields (multiselect, select, or numeric range) and define synonyms live.
   - The changes are instantly applied to the running application and reflected on the Leaflet map without restarting the server!

2. **Declarative Configuration ([`filters_config.json`](template/filters_config.json))**:
   - Define custom facets, validation types, and thesaurus synonyms declaratively in JSON.

3. **Adapting to Custom Datasets in 3 Steps**:
   - Replace or edit [`template/data/facilities.json`](template/data/facilities.json) with your own GeoJSON/JSON spatial records containing `latitude`, `longitude`, and your domain attributes.
   - Declare your filter fields in [`template/filters_config.json`](template/filters_config.json).
   - Run `python run_template.py` to explore your new GIS dashboard with conversational search and dynamic facet badges.

---

## 🛠️ Domain Customization & Developer Guide (CRMs Demonstrator)

- **Adapting to Other Domains**: Update the canonical dictionary in [`code/nlu_pipeline.py`](code/nlu_pipeline.py) under `DOMAIN_SYNONYMS` for your domain (e.g., cadastres, environmental hazards, forestry).

- **Connecting a Production Apache Solr / SolrCloud Cluster**: To connect to a live distributed SolrCloud collection or standalone Solr core, define the environment variable: `export SOLR_URL="http://your-solr-host:8983/solr/crms_collection"`. The search connector in [`code/mock_api.py`](code/mock_api.py) automatically routes queries via the Solr HTTP REST API (`/select`) with live faceting, falling back gracefully to the embedded synthetic dataset if omitted.

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
