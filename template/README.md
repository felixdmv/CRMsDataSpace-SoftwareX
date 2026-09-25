# General-Purpose GIS Architecture Template & Sandbox
## Elsevier *SoftwareX* Reference Implementation

[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Codespaces: Template Sandbox](https://img.shields.io/badge/Codespaces-GIS%20Template%20Sandbox-success.svg)](https://codespaces.new/felixdmv/CRMsDataSpace-SoftwareX?devcontainer_path=.devcontainer/generic-template/devcontainer.json)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Zero%20External%20(Stdlib)-brightgreen.svg)]()

> **Companion Template for the SoftwareX Article:**  
> *"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"*  
> *Félix de Miguel, Daniel Urda, Nuño Basurto* — **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Universidad de Burgos, Spain.

---

## 📌 Purpose & Generality Overview

While our primary real-world demonstrator maps European Critical Raw Materials (CRMs) waste deposits ([`../code/`](../code/)), the **underlying 4-stage architecture is domain-agnostic**.

This `/template` package provides a **clean, lightweight sandbox** designed for reviewers, researchers, and developers who wish to:
1. **Verify Architectural Generality**: Test the 4-stage pipeline on a completely distinct spatial domain (e.g., Global Renewable Energy & Environmental Infrastructure).
2. **Create & Customize Filters by Hand**: Dynamically add new filter dimensions, change facet types, or define multilingual thesaurus synonyms either via `filters_config.json` or live in the in-browser **Filter Studio**.
3. **Adapt to Custom GIS Problems**: Follow a 3-step recipe to instantiate the architecture on any geospatial dataset (urban sensors, biodiversity, wildfire monitoring, logistics, smart agriculture).

```
+--------------------------------------------------------------------------------------------------------+
|                                4-STAGE DOMAIN-AGNOSTIC PIPELINE                                        |
+--------------------------------------------------------------------------------------------------------+
| [1] Query & Intent Parser  --> [2] Schema Normalizer    --> [3] Boolean Solr Engine --> [4] Dynamic    |
|     - Free text / Prompts      - Declarative Thesaurus      - Range & In-List Rules     GIS UI         |
|     - Numeric Comparisons      - Synonyms Mapping           - Live Multidim. Facets     - Leaflet Sync |
|     - Intent Classification    - OpenAPI JSON Validation    - Spatial Bounding Box      - Pulse Rings  |
+--------------------------------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start for Reviewers

### Option 1: 1-Click Cloud Execution (GitHub Codespaces)
Click the badge above or navigate to the repository on GitHub and select the **GIS Architecture Template Sandbox** dev container configuration. Port `8085` opens automatically in your browser.

### Option 2: Local Standalone Execution (Zero Setup)
Runs out-of-the-box on standard Python 3.9+ without installing any pip packages:

```bash
# From within the template directory:
python run_template.py --port 8085

# Or using the bash launcher:
./run_template.sh
```

Then open your browser at: **`http://localhost:8085`**.

---

## 🛠️ How to Experiment & "Tinker" with Filters

The template offers two complementary ways to create and modify filters:

### Method A: Live In-Browser "Filter Studio" (No Code Editing)
1. Open the web interface at `http://localhost:8085`.
2. Click the **"🛠️ Filter Studio"** tab on the left sidebar.
3. Fill in the **"➕ Add New Custom Filter Field"** form (e.g., Key: `operator`, Label: `Operator`, Type: `multiselect`, Options: `Iberdrola, EDF, NextEra, Statkraft`).
4. Click **"Add Field to Live Configuration"** $\to$ the schema is saved, and the manual filter controls and NLU thesaurus update immediately!

### Method B: Declarative Schema (`filters_config.json`)
The filter architecture is configured declaratively in [`filters_config.json`](filters_config.json):

```json
{
  "key": "category",
  "label": "Facility Category",
  "type": "multiselect",
  "synonyms": {
    "solar": ["solar", "photovoltaic", "pv", "fotovoltaica", "sun"],
    "wind": ["wind", "eolica", "turbines", "aerogeneradores"],
    "hydro": ["hydro", "hydroelectric", "dam", "presa"]
  },
  "options": ["Solar", "Wind", "Hydro", "Geothermal", "Storage", "Biomass"]
}
```

Supported field types:
- `multiselect`: Multi-choice category tags with real-time facet counters and Solr `OR` clauses (`fq=category:("Solar" OR "Wind")`).
- `select`: Single-choice dropdown filter (`fq=status:"Operational"`).
- `range`: Numeric slider / min-max threshold with comparative parsing (`fq=capacity_mw:[100 TO *]`).

---

## 🗺️ How to Adapt to Your Own GIS Domain (in 3 Steps)

### Step 1: Provide Your Spatial Dataset
Place your JSON records in `data/facilities.json` (or any path). Each record must contain `id`, `name`, `latitude`, `longitude`, plus your custom domain attributes:

```json
[
  {
    "id": "STN-01",
    "name": "Air Quality Station Central",
    "latitude": 40.4168,
    "longitude": -3.7038,
    "sensor_type": "PM2.5",
    "status": "Active",
    "aqi_index": 42
  }
]
```

### Step 2: Declare Filter Fields in `filters_config.json`
Define which attributes should appear as interactive filters and specify synonyms for natural language keyword extraction.

### Step 3: Run the Server
Launch `python run_template.py`. The Leaflet map, facet counters, Solr query builder, and conversational search bar immediately reflect your custom domain!

---

## 🔬 4-Stage Architecture Trace in the Inspector Drawer

At the bottom of the template UI, an expandable inspector drawer reveals the live internal state of the 4 decoupled stages:
- **[1] NLU Parsing**: User text, detected intent (`filter_search` vs `generic_qa`), and extracted keyword tokens.
- **[2] Schema Validation**: Canonical filter structure compliant with JSON schema rules.
- **[3] Solr Query & Facets**: The exact Solr query URL parameters (`q=*:*&fq=...`) and real-time facet distributions.
- **[4] Dynamic GIS Sync**: List of matching spatial record IDs, animated pulsing rings, and map badge sync.
- **💬 Narrative**: Evidence-grounded natural language synthesis summarizing query findings.

---

## 📂 Template Directory Structure

```
template/
├── README.md               # This architectural guide and tutorial
├── filters_config.json     # Declarative filter definitions & thesaurus mapping
├── run_template.py         # Zero-dependency Python server & 4-stage orchestrator
├── run_template.sh         # Shell launcher script
├── requirements.txt        # Documentation of standard library dependencies
├── data/
│   └── facilities.json     # 30-facility domain-agnostic GIS dataset
└── static/
    ├── index.html          # Reactive Leaflet GIS UI with Live Filter Studio
    └── favicon.ico         # App icon
```
