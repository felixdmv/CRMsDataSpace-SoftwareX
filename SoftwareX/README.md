# SoftwareX — Reference Software Implementation & Replication Package

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Elsevier SoftwareX](https://img.shields.io/badge/Elsevier-SoftwareX-orange.svg)](https://www.sciencedirect.com/journal/softwarex)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/felixdmv/CRMsDataSpace-SoftwareX)

This package contains the official source code, evaluation testbeds, and scientific manuscript files for the **Elsevier SoftwareX** article:

> **"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"**  
> *Félix de Miguel, Daniel Urda, Nuño Basurto*  
> **Grupo de Inteligencia Computacional Aplicada (GICAP)**, Departamento de Digitalización, Escuela Politécnica Superior, Universidad de Burgos, Spain.

---

## 📁 Package Directory Structure

- **[`code/`](code/)**: Complete software implementation of the 4-stage decoupled architecture:
  - `agent.py`: Pipeline orchestrator integrating NLU extraction, Apache Solr query generation, and response synthesis.
  - `nlu_pipeline.py`: Pluggable bilingual thesaurus normalizer, OpenAPI JSON validator, and Boolean Solr query constructor.
  - `mock_api.py`: Apache Solr spatial indexing simulator with live facet calculations.
  - `llm_client.py`: Multi-backend client supporting Standalone Deterministic Mock, local open-weight LLMs, and cloud APIs.
  - `run_app.py`: Standalone Python web application server (zero external dependencies).
  - `static/index.html`: Dynamic Single-Page Application (Leaflet.js + TailwindCSS) with real-time visual filter badges and glowing pulse marker rings.
  - `evaluation/`: Golden 100-query benchmark suite (`test_battery_100.json`, `evaluate_100_tests.py`, and multi-model benchmark).
  - `test_apis.py`: Automated multi-backend API and engine verification script.
- **[`manuscript/`](manuscript/)**: Elsevier SoftwareX manuscript files:
  - LaTeX source (`main.tex`, modular sections in `sections/`, references `references.bib`).
  - High-resolution figures, diagrams, and Graphical Abstract (300 DPI).

---

## 🚀 Quick Start for Reviewers

### Option 1: One-Click Cloud Execution (GitHub Codespaces)
Click the badge above or navigate to the repository on GitHub and select **Code $\to$ Codespaces $\to$ Create codespace on main**. The container automatically starts the web application on port `8080` and opens it in your browser.

### Option 2: Local Standalone Execution (Zero Setup, No GPU Required)
Reviewers can execute the complete web application locally on any computer (Linux, macOS, Windows) with standard Python 3.9+:

```bash
cd code
python run_app.py
```
Open your web browser at: **`http://localhost:8080`**.

### Option 3: Automated Verification & Golden Benchmark
To verify that all inference protocols and fail-safes operate with zero crashes:
```bash
cd code
python test_apis.py
```

To reproduce the 100-query benchmark metrics reported in Table 4 of the manuscript:
```bash
cd code/evaluation
python evaluate_100_tests.py
```

---

## 📄 License & Contact

This project is licensed under the **MIT License**. For technical inquiries or questions regarding replication, please contact the GICAP research team at Universidad de Burgos.
