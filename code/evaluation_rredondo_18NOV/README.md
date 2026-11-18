# evaluation_rredondo: Banco de Pruebas Conversacional y Espacial en Clúster HPC

Este directorio contiene el banco de pruebas experimental desarrollado específicamente para evaluar las capacidades críticas descritas en el manuscrito de **SoftwareX**:
> *"A Modular NLU-Solr Architecture with Dynamic GIS Visual Synchronization for Conversational Spatial Search"* (2026).

El banco de pruebas evalúa de forma exhaustiva, cuantitativa y reproducible los tres pilares de robustez y razonamiento espacial-conversacional del sistema:

1. **Guardrails y Contención Fuera de Dominio (Anti-alucinación)**: Garantizar que el sistema rechaza y no responde consultas que quedan fuera del contexto del **European Critical Raw Materials Data Space (CRMsDataSpace)** (consultas no mineras, deportes, recetas, inyecciones de código, o países fuera de los 12 Estados miembros de la UE cubiertos).
2. **Agregación Booleana y Suma de Escombreras (AND vs OR vs Compuestas)**: Comprobar que el motor NLU y Solr es capaz de interpretar disyunciones (`OR` = unión o **suma matemática exacta** de escombreras entre diferentes países o materias primas), conjunciones (`AND` = co-ocurrencia simultánea en el mismo emplazamiento minero) y consultas compuestas con desambiguación interactiva ante cero resultados.
3. **Memoria Conversacional y Seguimiento del Estado del Diálogo (DST)**: Comprobar que el sistema mantiene la memoria a lo largo de turnos conversacionales sucesivos cuando el usuario utiliza perífrasis continuativas como *"y también..."*, *"y además..."*, acotaciones *"de esas solo..."*, exclusiones *"ahora quita..."* y órdenes de *"reiniciar"*.

---

## 🏗️ Estructura del Directorio

```bash
evaluation_rredondo/
├── benchmark_rredondo.py            # Motor principal de evaluación y benchmarking
├── test_battery_rredondo.json       # Batería de pruebas estructurada (55 evaluaciones)
├── test_suite.py                    # Suite de pruebas unitarias automatizadas (unittest/pytest)
├── run_cluster_gpu.sbatch           # Script Slurm para ejecución con GPU en clúster (Apptainer)
├── run_cluster_cpu.sbatch           # Script Slurm para ejecución ligera en nodos CPU
├── submit_cluster_benchmark.sh      # Lanzador interactivo y gestor de trabajos Slurm
├── run_local_mock.sh                # Ejecución instantánea en modo local/heurístico CPU (1 s)
├── scripts/
│   └── generate_battery_rredondo.py # Generador determinista de la batería de pruebas
├── results/                         # Salida de resultados en JSON, TXT y tablas LaTeX
│   ├── results_rredondo_mock.json
│   ├── summary_rredondo_mock.txt
│   └── table_rredondo_mock.tex
└── logs/                            # Trazas de ejecución y logs de trabajos Slurm (%j.log)
```

---

## 📊 Dimensiones y Taxonomía de las Pruebas

La batería de pruebas (`test_battery_rredondo.json`) se divide en tres suites complementarias:

### 1. Suite `guardrails_ood` (20 casos de prueba)
- **Consultas no mineras**: Deportes, cocina, cine, astronomía, programación general, previsión meteorológica, literatura.
- **Territorios no soportados fuera de la UE**: Países de gran relevancia minera global no integrados en el catálogo comunitario actual de 12 países (Chile, China, Rusia, Estados Unidos, Australia, Noruega, Suiza, Brasil, Reino Unido, Marruecos).
- **Inyecciones adversariales y ataques semánticos**: Intentos de elusión de instrucciones (*prompt injection*), inyecciones SQL (`DROP TABLE...`, `UNION SELECT...`), o peticiones de coordenadas militares secretas.
- **Criterio de éxito**: El sistema **debe retornar 0 documentos encontrados** (`num_found = 0`), clasificar la intención como `generic_qa` (o salida temprana), neutralizar caracteres Lucene y emitir un mensaje determinista de aclaración territorial/temática, garantizando una **tasa de alucinación del 0.0%**.

### 2. Suite `boolean_sum_and_or` (14 casos de prueba)
- **Disyunción geográfica (Suma de escombreras)**:
  - *"Escombreras en España o Portugal"* $\rightarrow$ Suma exacta: 3 (España) + 2 (Portugal) = **5 escombreras**.
  - *"Escombreras en España o Francia"* $\rightarrow$ Suma exacta: 3 (España) + 2 (Francia) = **5 escombreras**.
  - *"Balsas de relaves en Finlandia o Suecia"* $\rightarrow$ Suma exacta: 8 (Finlandia) + 10 (Suecia) = **18 balsas**.
  - *"Instalaciones en Austria o Chequia"* $\rightarrow$ Suma exacta: 8 (Austria) + 8 (Chequia) = **16 instalaciones**.
  - *"Escombreras en España, Portugal o Francia"* $\rightarrow$ 3 + 2 + 2 = **7 escombreras**.
- **Disyunción por materias primas**:
  - *"Escombreras con litio o wolframio"* $\rightarrow$ Suma disjunta: 7 (litio) + 7 (wolframio) = **14 escombreras**.
  - *"Escombreras con cobre o níquel"* $\rightarrow$ Unión con solapamiento = **5 escombreras**.
- **Conjunción (AND / Co-ocurrencia simultánea)**:
  - *"Escombreras con litio y cobalto"* $\rightarrow$ Co-ocurrencia verificada en 2 sitios (`EU-CRM-045` en Finlandia y `EU-CRM-097` en Extremadura, España).
  - *"Instalaciones con cobre y níquel juntos"* $\rightarrow$ 3 instalaciones (`EU-CRM-036`, `EU-CRM-081`, `EU-CRM-095`).
  - *"Escombreras en España con wolframio y manganeso"* $\rightarrow$ 1 instalación (`EU-CRM-017` en Castilla y León).
  - *"Balsas de relaves con litio y cobalto"* $\rightarrow$ 0 resultados (activa desambiguación interactiva AND vs OR).
- **Consultas compuestas parentizadas**:
  - *"Instalaciones con manganeso o (litio y cobalto)"* $\rightarrow$ 19 instalaciones.
  - *"Escombreras con wolframio o (platino y titanio)"* $\rightarrow$ 7 escombreras.

### 3. Suite `conversational_memory` (5 episodios, 21 turnos)
- **Episodio 1 (Corredor Ibérico con 'y también...', refinamiento y reset)**:
  - Turno 1: *"Muestra escombreras en España"* (`new_search`, España, 3 escombreras).
  - Turno 2: *"y también en Portugal"* (`expand`, España + Portugal, suma: 5 escombreras).
  - Turno 3: *"y de esas solo las que tienen wolframio"* (`refine`, 2 escombreras).
  - Turno 4: *"de esas, únicamente las que están en desarrollo"* (`refine`, 2 escombreras en desarrollo).
  - Turno 5: *"ahora quita Portugal"* (`remove`, España únicamente, 1 escombrera).
  - Turno 6: *"reiniciar búsqueda"* (`reset`, restablece los 100 sitios).
- **Episodio 2 (Balsas nórdicas con 'y también...' consecutivo)**:
  - Expansión territorial Finlandia + Suecia (18 balsas), refinamiento a níquel (2), expansión a níquel o cobalto (3), y acotación a inactivas (1).
- **Episodio 3 (Resolución de desambiguación y continuidad)**:
  - Detección de 0 resultados en conjunción, resolución a disyunción (`OR`, 23 sitios) y continuidad contextual con *"y también en Francia"* (2 sitios).
- **Episodio 4 (Centroeuropa con agregación y criterios ambientales)**:
  - Alemania (4) $\rightarrow$ *"y también en Austria"* (14) $\rightarrow$ *"de esas solo escombreras"* (4) $\rightarrow$ *"y también que tengan wolframio"* (2).
- **Episodio 5 (Preguntas elípticas y sustitución de entidad)**:
  - *"¿Hay escombreras de litio en España?"* (1) $\rightarrow$ *"¿Y en Portugal?"* (1) $\rightarrow$ *"¿Y en Finlandia?"* (2).

---

## 🚀 Ejecución en el Clúster HPC

El clúster institucional cuenta con el gestor de colas **Slurm** y el entorno de contenedores **Apptainer/Singularity** con aceleración GPU (`--nv`).

### 1. Envío de trabajos GPU vía Slurm

Para enviar la evaluación de un modelo a la partición de GPUs (`computo` con NVIDIA A100):

```bash
# Opción A: Utilizando el asistente unificado submit_cluster_benchmark.sh
./evaluation_rredondo/submit_cluster_benchmark.sh qwen      # Qwen 2.5 7B Instruct (Recomendado)
./evaluation_rredondo/submit_cluster_benchmark.sh mistral   # Mistral 7B Instruct v0.2
./evaluation_rredondo/submit_cluster_benchmark.sh llama     # Llama 3.2 3B Instruct
./evaluation_rredondo/submit_cluster_benchmark.sh deepseek  # DeepSeek R1 Distill Qwen 7B

# Opción B: Enviar toda la batería de modelos de forma automatizada
./evaluation_rredondo/submit_cluster_benchmark.sh all

# Opción C: Invocar directamente sbatch
sbatch evaluation_rredondo/run_cluster_gpu.sbatch qwen
```

### 2. Monitorización de trabajos en el clúster

```bash
# Ver el estado de la cola
./evaluation_rredondo/submit_cluster_benchmark.sh status

# O directamente mediante Slurm
squeue -u $USER

# Inspeccionar la traza en tiempo real de un trabajo
tail -f evaluation_rredondo/logs/slurm_gpu_<JOB_ID>.log
```

### 3. Ejecución ligera en nodos CPU del clúster

Para evaluar el baseline heurístico determinista sin consumir cuota de GPU:

```bash
./evaluation_rredondo/submit_cluster_benchmark.sh cpu
# O mediante: sbatch evaluation_rredondo/run_cluster_cpu.sbatch
```

---

## 💻 Ejecución Local / Estación de Trabajo (Sin Slurm)

Para verificación rápida durante desarrollo o integración continua (CI/CD) sin necesidad de GPU:

```bash
# Ejecutar todas las 55 pruebas del baseline determinista en 1 segundo:
./evaluation_rredondo/run_local_mock.sh

# O mediante Python directamente:
python3 evaluation_rredondo/benchmark_rredondo.py --provider mock --verbose

# Ejecutar únicamente una suite específica:
python3 evaluation_rredondo/benchmark_rredondo.py --provider mock --suite guardrails_ood
python3 evaluation_rredondo/benchmark_rredondo.py --provider mock --suite boolean_sum
python3 evaluation_rredondo/benchmark_rredondo.py --provider mock --suite conversational_memory

# Ejecutar la suite de pruebas unitarias automatizada:
python3 evaluation_rredondo/test_suite.py
```

---

## 📈 Resultados y Métricas de Salida

Cada ejecución genera automáticamente tres artefactos en `evaluation_rredondo/results/`:

1. **`results_rredondo_<provider>.json`**: Registro estructurado completo con latencias detalladas por turno, telemetría de memoria VRAM GPU, métricas F1 por dimensión y trazas de fallos.
2. **`summary_rredondo_<provider>.txt`**: Informe textual legible formateado en tablas ASCII para lectura rápida.
3. **`table_rredondo_<provider>.tex`**: Tabla lista para publicación en formato LaTeX/SoftwareX para actualizar directamente el manuscrito.

### Resumen del Baseline Determinista (Heurísticas CPU):

| Suite de Evaluación | Unidades Evaluadas | Tasa de Éxito (%) | Métrica Clave | Latencia Media |
| :--- | :---: | :---: | :---: | :---: |
| **1. Guardrails Fuera de Dominio** | 20 consultas | **100.0%** | Tasa Alucinación: 0.0% | 0.7 ms |
| **2. Agregación Booleana y Suma** | 14 consultas | **100.0%** | Acierto de Suma: 100.0% | 0.9 ms |
| **3. Memoria Conversacional (DST)** | 5 episodios (21 turnos) | **100.0%** | Precisión 'y también': 100.0% | 1.0 ms |
| **Puntuación Global Consolidada** | **55 unidades** | **100.0%** | **Macro F1: 100.0%** | **0.9 ms** |
