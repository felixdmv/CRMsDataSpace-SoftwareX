RAG prototype (local)
=====================

Resumen
-------
Pequeño prototipo de RAG para hacer preguntas sobre PDFs locales. Procesa PDFs desde la carpeta `pdfs/`, extrae texto (OCR fallback), crea chunks, genera embeddings con `sentence-transformers`, indexa con FAISS y permite preguntar con `ask.py`.

Archivos clave
-------------
- `code/extract_text.py` — extracción de texto por página (OCR fallback).
- `code/build_index.py` — chunking + embeddings + FAISS index.
- `code/search.py` — cargador del índice y función `search(query, k)`.
- `code/ask.py` — CLI: `python code/ask.py "your question"`.
- `code/index.faiss`, `code/index_meta.json` — generados por `build_index.py`.

Requisitos del sistema
----------------------
- Python 3.8+
- Poppler (para `pdf2image`) — instalar desde su paquete para tu OS. En Windows, descargar y configurar `POPPLER_PATH`.
- Tesseract OCR — instalar y añadir al `PATH`.

Instalación (pip)
------------------
```bash
python -m pip install -r code/requirements.txt
```

Uso
---
1. Poner los PDFs en la carpeta `pdfs/` (raíz del workspace).
2. Construir el índice:

```bash
python code/build_index.py
```

3. Preguntar (ejemplo):

```bash
python code/ask.py "What materials are present in the waste facility?"
```

Notas sobre el LLM local
------------------------
- `ask.py` usa `transformers` (+ `accelerate`) y por defecto intenta cargar `microsoft/phi-3-mini-4k-instruct` (puedes cambiar el modelo poniendo `HF_MODEL` en el entorno).
- El modelo se descargará automáticamente desde Hugging Face si no existe localmente; la inferencia se ejecuta en CPU por defecto (puede ser lenta para modelos grandes).
- Si prefieres usar un modelo local ya descargado, coloca la carpeta del modelo en `models/` y `transformers` la usará.
- Si en el futuro quieres usar una versión quantizada con `llama-cpp-python`, házmelo saber y lo adapto.

Comandos útiles (Windows PowerShell)
----------------------------------
```powershell
# instalar poppler (descargar binarios) y añadir POPPLER_PATH si es necesario
# instalar tesseract (desde installer) y añadirlo al PATH
python -m pip install -r code/requirements.txt
python code/build_index.py
python code/ask.py "What materials are present in the waste facility?"
```

Limitaciones
------------
- Este es un prototipo minimal. No hay fine-tuning, ni optimizaciones FAISS avanzadas.
- OCR y descarga automática de modelos requieren herramientas externas y espacio en disco.