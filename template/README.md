# General-Purpose GIS Architecture Template & Sandbox
## Elsevier *SoftwareX* Reference Implementation

[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Codespaces: Template Sandbox](https://img.shields.io/badge/Codespaces-GIS%20Template%20Sandbox-success.svg)](https://codespaces.new/felixdmv/CRMsDataSpace-SoftwareX?devcontainer_path=.devcontainer/generic-template/devcontainer.json)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Zero%20External%20(Stdlib)-brightgreen.svg)]()
[![100% Offline Map](https://img.shields.io/badge/Map%20Tiles-100%25%20Offline%20Vector-success.svg)]()

> **Companion Template for the SoftwareX Article:**  
> *"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"*  
> *Félix de Miguel, Daniel Urda, Nuño Basurto* — **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Universidad de Burgos, Spain.

---

## 📌 Purpose & Role in the SoftwareX Paper

While our primary real-world demonstrator maps European Critical Raw Materials (CRMs) waste deposits ([`../code/`](../code/)), the **underlying 4-stage architecture is completely domain-agnostic**.

This `/template` package provides an **interactive, pedagogical sandbox** designed for reviewers, researchers, and developers to experience firsthand how conversational spatial search adapts dynamically to **any GIS domain**:

1. **Custom Vector Basemap (Zero External Tile Server / Zero API Keys)**: The sandbox renders a stylized fictional island nation (**Avalon Republic**) with distinct landmass, continental shelf, and 5 regional sectors (*North Coast*, *Central Highlands*, *South Bay*, *Emerald Valley*, *Eastern Archipelago*). It runs 100% offline without third-party tile APIs.
2. **Empty Initial State & On-Demand Population**: On startup, the map starts with **0 facilities**. The user is guided to choose a preset or customize filter dimensions first, and only when clicking **"🎲 Generate Points"** are facilities procedurally scattered across the territory.
3. **Open User-Defined Filters (Zero Hardcoded Restrictions)**: The user has full freedom to create whatever filter dimensions they want (*Generation Technology*, *Operational Status*, *Capacity Scale*, *Priority Tier*, etc.), or choose from 1-click domain presets (**Renewable Energy**, **Smart City**, or **Custom Blank Canvas**).
4. **Conversational Search & Dynamic Cartographic Sync**: Users query the map in free natural language (*"solar and wind farms with grade a"*, *"operational battery storage in North Coast"*, *"hospitals with critical tier 1"*). The dynamic NLU tokenizer, Solr Boolean filter builder ($fq$), and Leaflet visual engine synchronize in real time.

```
+--------------------------------------------------------------------------------------------------------+
|                                4-STAGE DOMAIN-AGNOSTIC PIPELINE                                        |
+--------------------------------------------------------------------------------------------------------+
| [1] Dynamic NLU Parser     --> [2] Schema Normalizer    --> [3] Boolean Solr Engine --> [4] Dynamic    |
|     - Free text / Prompts      - Declarative Thesaurus      - Range & In-List Rules     GIS UI         |
|     - Dynamic Word Stemming    - User Filter Attributes     - Live Multidim. Facets     - Leaflet Sync |
|     - Spatial Zone Matching    - JSON Schema Validation     - Bounding Box & fq         - Pulse Rings  |
+--------------------------------------------------------------------------------------------------------+
```

---

## ❓ Architectural Design: Rule-Based NLU vs. LLM

### What is the purpose of the template?
In our research paper, the central contribution is the **decoupling of the conversational layer from the spatial index**:
`Conversational Input -> Structured JSON Schema -> Apache Solr Search -> Dynamic Cartographic Sync`.

In the main demonstrator (`code/`), we demonstrate this architecture with full multi-LLM backends (Gemini, OpenAI, Claude, Qwen) for European mining deposits.

In this **template package**, the purpose is **portability, instant evaluation, and inspectability**:
1. **Zero External Dependencies / 100% Reproducibility**: Runs on Python 3.9+ standard library (`http.server`, `re`, `json`, `random`). A reviewer or adopter does not need GPUs, CUDA drivers, Ollama daemons, or paid API keys.
2. **Transparent 4-Stage Traceability**: The declarative rule-based NLU engine builds dynamic tokenizers directly from the active user-defined schema. Reviewers can open the bottom **4-Stage Inspector** to observe deterministically how natural language queries map to the JSON schema, Solr `$fq` rules, and Leaflet marker animations.
3. **Plug-and-Play LLM Extension**: Because Stage 1 has a standard interface (outputting a validated JSON filter dictionary), any LLM prompt can be substituted in place of the rule parser, while Stages 2, 3, and 4 function identically.

---

## 🚀 Quick Start for Reviewers

### Option 1: 1-Click Cloud Execution (GitHub Codespaces)
Click the badge above or launch the devcontainer in GitHub Codespaces.
Both applications are orchestrated automatically in parallel in separate browser tabs:
- 🇪🇺 **Port 8080**: CRMsDataSpace European Demonstrator (`http://localhost:8080`)
- 🌍 **Port 8085**: General GIS Architecture Template Sandbox (`http://localhost:8085`)

### Option 2: Local Standalone Execution (Zero Setup)
Runs out-of-the-box on standard Python 3.9+ without installing any external packages:

```bash
# From within the template directory:
python run_template.py --port 8085

# Or using the root launcher:
python run_template.py --port 8085
```

Open your browser at: **`http://localhost:8085`**.

---

## 🎮 How the Sandbox Demonstrator Works (3 Steps)

### Step 1: Choose a Domain Preset or Define Custom Filters
- **1-Click Domain Presets**:
  - ⚡ **Renewable Energy & Power Grid**: *Generation Technology* (Solar Photovoltaic, Onshore Wind, Offshore Wind, Hydroelectric Dam, Battery Storage BESS, Geothermal Plant), *Operational Status*, *Capacity Scale*, *ESG Grade*.
  - 🏙️ **Smart City & Municipal Services**: *Municipal Infrastructure* (General Hospital, Public School, Metro Transit Hub, Urban Green Park, Police Station, Fire & Rescue), *Service Status*, *Response Priority*.
  - ✨ **Blank / Custom**: Start from scratch by adding your own custom dimensions and categories.
- **Open Filter Creator**: Click **"➕ Add Custom Filter"**, specify the dimension name and comma-separated options. The system automatically assigns distinct color palettes and morphological stemming variants.

### Step 2: Populate the Geographic Territory
- Select the desired quantity (25, 40, or 80 facilities).
- Click **"🎲 Generate Points"**.
- The procedural generator scatters points across the 5 sectors of Avalon Republic (*North Coast*, *Central Highlands*, *South Bay*, *Emerald Valley*, *Eastern Archipelago*), assigning random combinations of the active filter dimensions.

### Step 3: Conversational Spatial Search & GIS Synchronization
- Type free-form natural language queries in the search bar:
  - *"solar and wind farms with grade a"*
  - *"operational battery storage in North Coast"*
  - *"hospitals with critical tier 1"*
  - *"show all facilities"*
- Or click directly on the manual facet pill badges in the sidebar.
- Observe real-time synchronization:
  - Matching markers highlight with **pulsing radar rings** (`marker-pulse-active`).
  - Non-matching markers dim or hide based on the visibility toggle (*Dim / Hide*).
  - The top floating bar displays active filter tags with live counters.
  - The **4-Stage Inspector Drawer** at the bottom reveals the complete pipeline trace (NLU tokenization $\to$ Validated Schema $\to$ Solr Boolean query $\to$ Grounded narrative).

---

## 🏗️ Technical Architecture & Decoupling

The template relies entirely on standard Python modules (`http.server`, `json`, `re`, `random`, `pathlib`):

- [`run_template.py`](run_template.py): High-performance HTTP server and REST API handler (`/api/config`, `/api/facilities`, `/api/generate_points`, `/api/query`, `/api/add_filter`, `/api/preset`, `/api/territory_geojson`).
- [`filters_config.json`](filters_config.json): Declarative schema storing current territory coordinates, active filter dimensions, options, and color palettes.
- [`data/facilities.json`](data/facilities.json): Current procedurally generated points distributed across the territory (starts empty until populated).
- [`static/territory.geojson`](static/territory.geojson): Vector geometry of the fictional island nation (shelf, mainland, mountains, satellite isles).
- [`static/index.html`](static/index.html): Interactive single-page GIS frontend with Leaflet.js (vector mode) and Tailwind CSS.
