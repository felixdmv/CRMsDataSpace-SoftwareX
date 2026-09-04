# A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![SoftwareX](https://img.shields.io/badge/Elsevier-SoftwareX-orange.svg)](https://www.sciencedirect.com/journal/softwarex)
[![Status: Passing](https://img.shields.io/badge/Reviewer_Tests-100%25_Passing-brightgreen.svg)]()

Reference software implementation for the **SoftwareX** paper:  
> **"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"**  
> *Félix de Miguel, Daniel Urda, Nuño Basurto* — **Grupo de Inteligencia Computacional Aplicada (GICAP), Universidad de Burgos**.

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Key Architectural Innovations](#-key-architectural-innovations)
- [Quick Start for Reviewers (Zero-Setup in 1 Command)](#-quick-start-for-reviewers-zero-setup-in-1-command)
- [Preset Benchmark Test Queries](#-preset-benchmark-test-queries)
- [Running Empirical Evaluations](#-running-empirical-evaluations)
- [Repository Structure](#-repository-structure)
- [Developer Guide & Domain Customization](#-developer-guide--domain-customization)
- [License & Citation](#-license--citation)
- [Acknowledgements](#-acknowledgements)

---

## 🌟 Overview

This repository provides an open-source, domain-agnostic software architecture connecting conversational Natural Language Understanding (NLU), Apache Solr spatial search indexing, and interactive Geographic Information System (GIS) mapping. 

As a primary real-world demonstrator and case study, the architecture is instantiated within the European research initiative **CRMsDataSpace** (Research Fund for Coal and Steel, Grant Agreement No.~101216677), which builds a Common European Data Space for Critical Raw Materials (CRMs) and closed extractive facilities.

Navigating complex geospatial data spaces typically requires mastering rigid query syntax or interacting with dozens of nested dropdown filters. While raw Large Language Models (LLMs) enable conversational search, they frequently suffer from **database schema hallucinations**, non-deterministic outputs, and a total lack of cartographic feedback. 

Our architecture solves these limitations through a **4-stage decoupled pipeline**:
1. **Stage 1 (NLU & Schema Enforcement)**: Enforces strict OpenAPI JSON Schemas under greedy decoding ($T=0.0$) alongside Few-Shot domain exemplars.
2. **Stage 2 (Normalization & Query Building)**: Normalizes vocabulary via a pluggable domain thesaurus and deterministically constructs Boolean filter queries.
3. **Stage 3 (Spatial Search & Vector RAG)**: Queries Apache Solr spatial cores and retrieves technical documentation snippets via dense vector indexing (FAISS).
4. **Stage 4 (Dynamic GIS Map Synchronization)**: Updates interactive Leaflet.js maps in real time, rendering active filter badges, animating glowing pulse rings on matching facilities, and updating live site counters.

---

## 🚀 Quick Start for Reviewers (Zero-Setup in 1 Command)

The software is engineered for **immediate reviewer reproducibility**. No external API keys, database installations, or third-party dependencies are required to run the full application in **Standalone Mock Mode**.

### Prerequisites
- Python 3.9+ (Cross-platform: Windows, Linux, macOS).

### Step-by-Step Execution

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/felixdmv/CRMsDataSpace-SoftwareX.git
   cd CRMsDataSpace-SoftwareX
   ```

2. **Launch the Standalone Web Server**:
   ```bash
   python run_app.py
   ```

3. **Open the Web Application**:
   Navigate your web browser to:
   ```
   http://localhost:8080
   ```

*(Optional)*: To use live frontier LLM inference, copy `.env.example` to `.env` and configure your `GEMINI_API_KEY` or `OPENAI_API_KEY`.

---

## 🧪 Preset Benchmark Test Queries

Inside the web interface, click any of the preset test buttons or enter custom free-text queries:

| Query Type | Example Natural Language Query | Expected Behavioral Output |
|---|---|---|
| **Multi-Country & Multi-Commodity** | *"Muestra escombreras de litio y cobalto en España y Finlandia que estén activas"* | Badges: `[Country: Spain, Finland]`, `[Commodity: Lithium, Cobalt]`, `[Status: Active]`. Glowing pulse markers across Spain and Finland. |
| **Environmental Risk & Negation** | *"Balsas de wolframio sin restaurar en Alemania"* | Badges: `[Country: Germany]`, `[Commodity: Tungsten]`, `[Restored: False]`. Map focuses on German tailings dams. |
| **Domain Slang & Typos** | *"escombreras de golfranio en galiza"* | The normalizer handles typos (*golfranio* $\to$ *tungsten*, *galiza* $\to$ *Galicia, Spain*) and maps to Solr fields. |
| **Grounded Guard Exit** | *"Dime balsas de cobalto en Asturias"* | If zero records match, the grounded guard outputs a traceable *no results* message without hallucinating fictional sites. |

---

## 📊 Running Empirical Evaluations

To reproduce the benchmark accuracy evaluation reported in the paper (Section 3, Table 4):

```bash
cd evaluation
python evaluate_100_tests.py
```

This executes the automated test suite across 100 domain queries in `evaluation/test_battery_100.json`, verifying field-level precision, recall, and macro F1-score across all attributes.

---

## 📁 Repository Structure

```
CRMsDataSpace-SoftwareX/
├── data/
│   └── synthetic_escombreras_europe.json   # 100 Synthetic European facilities dataset
├── evaluation/
│   ├── test_battery_100.json               # 100 Golden test queries with ground truth
│   ├── evaluate_100_tests.py               # Benchmark execution & evaluation script
│   └── benchmark_results_summary.txt       # Field-level accuracy results
├── static/
│   └── index.html                          # Single-Page App (Leaflet.js + TailwindCSS UI)
├── agent.py                                # Hybrid architecture orchestrator
├── llm_client.py                           # Multi-provider LLM client with OpenAPI schema
├── mock_api.py                             # Apache Solr spatial simulator with facet engine
├── nlu_pipeline.py                         # Thesaurus normalizer, validator, and Solr query builder
├── run_app.py                              # Standalone Python HTTP server (port 8080)
├── requirements.txt                        # Optional cloud dependencies
├── LICENSE                                 # MIT License
├── .env.example                            # Example API configuration
└── README.md                               # Project documentation
```

---

## 🛠️ Developer Guide & Domain Customization

- **Adapting to Other Domains**: Update the canonical dictionary in [`nlu_pipeline.py`](nlu_pipeline.py) under `DOMAIN_SYNONYMS` for your domain (e.g., cadastres, environmental hazards, forestry).
- **Modifying the OpenAPI Schema**: Adjust `SEARCH_INTENT_SCHEMA` in [`llm_client.py`](llm_client.py) to add or replace filter dimensions.
- **Connecting a Production Apache Solr Cluster**: Replace the simulation endpoints in [`mock_api.py`](mock_api.py) with standard Solr HTTP queries using `pysolr` or the Solr JSON Request API.

---

## 📄 License & Citation

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for complete terms.

If you use this software architecture in your research, please cite our SoftwareX paper:

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

This research has received funding from the European Union's Research Fund for Coal and Steel (RFCS) under Grant Agreement No.~101216677 (**CRMsDataSpace**: *Building a Common European Data Space on Critical Raw Materials for the Green Deal*).

Developed by the **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Departamento de Digitalización, Escuela Politécnica Superior, Universidad de Burgos, Spain.
