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

While our primary real-world demonstrator maps European Critical Raw Materials (CRMs) waste deposits ([`../code/`](../code/)), the **underlying 4-stage architecture is completely domain-agnostic**.

This `/template` package provides an **interactive, pedagogical sandbox** designed for reviewers, researchers, and developers to experience firsthand how conversational spatial search adapts dynamically to **any GIS domain**:

1. **Simple Geographic Territory**: Instead of a scattered world map, the sandbox focuses on a compact, visually rich regional territory: **Archipiélago Avalon** (divided into 5 sectors: *Costa Norte*, *Tierras Altas*, *Bahía Sur*, *Valle Esmeralda*, *Sector Oriental*).
2. **Open User-Defined Filters (Zero Hardcoded Restrictions)**: The user has full freedom to create whatever filter dimensions and categories they want (*Tipo de Lugar*, *Facción*, *Peligro*, *Clima*, *Equipamiento*, etc.), or choose from 1-click domain presets.
3. **Procedural Spatial Point Generator**: When filters are defined, the system procedurally generates objects distributed across the archipelago, assigning random combinations of the active filter values.
4. **Conversational Search & Dynamic Cartographic Sync**: The user queries the map in free natural language (*"castillos con peligro crítico"*, *"puertos de los mercaderes en Bahía Sur"*). The dynamic NLU tokenizer, Solr Boolean filter builder ($fq$), and Leaflet visual engine synchronize in real time.

```
+--------------------------------------------------------------------------------------------------------+
|                                4-STAGE DOMAIN-AGNOSTIC PIPELINE                                        |
+--------------------------------------------------------------------------------------------------------+
| [1] Query & Intent Parser  --> [2] Schema Normalizer    --> [3] Boolean Solr Engine --> [4] Dynamic    |
|     - Free text / Prompts      - Declarative Thesaurus      - Range & In-List Rules     GIS UI         |
|     - Dynamic Word Stemming    - User Filter Attributes     - Live Multidim. Facets     - Leaflet Sync |
|     - Spatial Zone Matching    - JSON Schema Validation     - Bounding Box & fq         - Pulse Rings  |
+--------------------------------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start for Reviewers

### Option 1: 1-Click Cloud Execution (GitHub Codespaces)
Click the badge above or navigate to the repository on GitHub and select the **GIS Architecture Template Sandbox** dev container configuration.
Both applications are orchestrated automatically in the background:
- 🇪🇺 **Port 8080**: CRMsDataSpace European Demonstrator (`http://localhost:8080`)
- 🌍 **Port 8085**: General GIS Architecture Template Sandbox (`http://localhost:8085`)

### Option 2: Local Standalone Execution (Zero Setup)
Runs out-of-the-box on standard Python 3.9+ without installing any external pip packages:

```bash
# From within the template directory:
python run_template.py --port 8085

# Or using the root launcher:
python run_template.py --port 8085
```

Open your browser at: **`http://localhost:8085`**.

---

## 🎮 How the Sandbox Demonstrator Works (3 Steps)

### Paso 1: Define tus Filtros o Elige un Preset
- **1-Click Presets**:
  - 🏰 **Aventura y Rol**: *Tipo de Lugar* (Castillo, Mina abandonada, Templo místico, Puerto pirata, Refugio), *Facción*, *Nivel de Peligro*.
  - 🏙️ **Smart City**: *Tipo de Equipamiento* (Hospital, Parque Verde, Metro, Escuela, Comisaría), *Estado del Servicio*, *Prioridad*.
  - ⚡ **Energía e Infraestructura**: *Tecnología* (Solar, Eólica, Hidroeléctrica, Baterías), *Conexión a Red*, *Calificación ESG*.
  - ✨ **En blanco**: Empieza desde cero creando tus propios filtros.
- **Creación Abierta de Filtros**: Haz clic en **"➕ Añadir Filtro"**, escribe el nombre del atributo y sus categorías separadas por coma. El sistema le asigna colores y sinónimos automáticamente.

### Paso 2: Poblar el Territorio Geográfico
- Selecciona la cantidad deseada (25, 40 u 80 objetos).
- Haz clic en **"🎲 Generar Puntos en el Mapa"**.
- El generador procedimental distribuye los puntos por los sectores del archipiélago (*Costa Norte*, *Tierras Altas*, *Bahía Sur*, etc.), combinando aleatoriamente los valores de todos los filtros activos.

### Paso 3: Búsqueda Conversacional y Sincronización GIS
- Escribe preguntas o filtros en lenguaje natural en la barra de búsqueda:
  - *"castillos con peligro crítico"*
  - *"templos o refugios de los guardianes"*
  - *"instalaciones en Bahía Sur"*
  - *"mostrar todo"*
- O haz clic directamente en las píldoras de facetas manuales en la barra lateral.
- Observa cómo:
  - Los marcadores coincidentes se iluminan y muestran **anillos de pulso luminosos**.
  - Los no coincidentes se atenúan o se ocultan según tu preferencia.
  - La barra superior muestra etiquetas dinámicas con contador en tiempo real.
  - El **Inspector de 4 Etapas** en el cajón inferior desglosa la tokenización NLU, el esquema validado, la consulta Solr ($fq$) y la narrativa natural sintetizada.

---

## 🏗️ Technical Architecture & Decoupling

The template relies entirely on standard Python modules (`http.server`, `json`, `re`, `random`, `pathlib`):

- [`run_template.py`](run_template.py): High-performance HTTP server and REST API handler (`/api/config`, `/api/facilities`, `/api/generate_points`, `/api/query`, `/api/add_filter`, `/api/preset`).
- [`filters_config.json`](filters_config.json): Declarative schema storing current territory coordinates, active filter dimensions, options, and color palettes.
- [`data/facilities.json`](data/facilities.json): Current procedurally generated points distributed across the archipelago.
- [`static/index.html`](static/index.html): Interactive single-page GIS frontend with Leaflet.js and Tailwind CSS.
