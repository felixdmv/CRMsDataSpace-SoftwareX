# SoftwareX Code Base: CRMs Data Space Architecture Demonstrator

This directory contains the reference software implementation submitted to **SoftwareX** for the paper:
*"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"*.

---

## 🌟 Key Features

1. **Synthetic Anonymized Dataset (100 European Sites)**:
   - Contains 100 realistic synthetic tailings storage facilities, waste dumps, and mineral stockpiles across 12 European countries (Spain, Portugal, Germany, France, Sweden, Finland, Poland, Italy, Greece, Ireland, Austria, Czechia).
   - Covers 12 Critical Raw Materials (Lithium, Cobalt, Tungsten, REE, Nickel, Copper, Tin, Tantalum, Graphite, Titanium, PGE, Manganese).
   - Complies with data protection and confidentiality standards while demonstrating complete functional capability.

2. **Dual-Variant NLU Architecture**:
   - **Variant 1 (Few-Shot Intent Parsing)**: Uses targeted prompt engineering to accurately extract canonical search fields without hallucinating database schemas.
   - **Variant 3 (Structured JSON Schema)**: Enforces OpenAPI / Gemini `responseSchema` for 100% parseable structured output between pipeline nodes.

3. **Interactive GIS Map Filter Synchronization**:
   - Extracted NLU filters (commodities, countries, facility types, statuses) are dynamically rendered as visual filter badges above the interactive Europe Leaflet map.
   - Matching markers glow with active pulse animations, while non-matching markers fade, allowing scientific reviewers to visually verify extraction accuracy.

4. **Zero-Setup Reviewer Execution**:
   - Supports **Standalone Mock Mode** out of the box with zero external API key requirements.
   - Reviewers can also optionally connect live Gemini or OpenAI keys via the web interface.

---

## 🚀 Quick Start for Reviewers (Run in 1 Command)

### Prerequisites
- Python 3.9+ (No third-party packages required for Standalone Mock Mode!)

### Step-by-Step Execution

1. **Clone & Navigate to Code Directory**:
   ```bash
   git clone https://github.com/your-org/CRMsDataSpace-SoftwareX.git
   cd SoftwareX/code
   ```

2. **Launch Web Server**:
   ```bash
   python run_app.py
   ```

3. **Open Application**:
   Navigate your web browser to:
   ```
   http://localhost:8080
   ```

---

## 🧪 Preset Test Queries for Reviewers

In the web interface, click any of the preset reviewer query buttons or type your own:

- **Query 1 (Multi-Country & Multi-Element)**:
  `"Muestra escombreras de litio y cobalto en España y Finlandia que estén activas"`
  *Expected Result*: Extracted filters `[Commodity: Lithium, Cobalt]`, `[Country: Spain, Finland]`, `[Status: Active]`. Map highlights matching markers across Spain and Finland.

- **Query 2 (Environmental Risk & Country Filter)**:
  `"Balsas de wolframio sin restaurar en Alemania"`
  *Expected Result*: Extracted filters `[Commodity: Tungsten]`, `[Country: Germany]`, `[Facility: Pond, TSF]`, `[Restored: false]`.

- **Query 3 (Strategic Tech Metals)**:
  `"Depósitos de tierras raras en Suecia y Francia"`
  *Expected Result*: Extracted filters `[Commodity: Rare Earth Elements]`, `[Country: Sweden, France]`.

---

## 📁 Repository Structure

```
SoftwareX/code/
├── data/
│   └── synthetic_escombreras_europe.json   # 100 Synthetic European CRM sites dataset
├── static/
│   └── index.html                          # Single-Page Application (Leaflet GIS + Tailwind CSS)
├── agent.py                                # Hybrid architecture orchestrator
├── llm_client.py                           # LLM client supporting Gemini responseSchema & Mock parser
├── mock_api.py                             # Solr engine simulator with facet computation
├── nlu_pipeline.py                         # Normalizer, Validator, QueryBuilder (v1 + v3)
├── run_app.py                              # Standalone Python web server (port 8080)
├── requirements.txt                        # Optional LLM dependencies
└── .env.example                            # Example API key configuration
```

---

## 📄 License & Citation

Distributed under the MIT License. See `LICENSE` for details.
If using this codebase in scientific research, please cite our SoftwareX paper.
