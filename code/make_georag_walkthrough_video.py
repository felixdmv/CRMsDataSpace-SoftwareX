#!/usr/bin/env python3
"""
Generate an improved walkthrough video of the Geo-RAG Explorer web application,
showing the active data and highlighting the data flow and active nodes in
both the webapp and the architecture diagram using neon boxes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
import socketserver
import threading

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Path configuration
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DIRECTORY = PROJECT_ROOT / "geo-rag-explorer"
OUTPUT_DIR = PROJECT_ROOT / "mp4" / "solr"
TEMP_DIR = Path(os.environ.get("TEMP", r"C:\Users\felix\AppData\Local\Temp"))

# Store frames in subdirectories
FRAMES_BASE_DIR = PROJECT_ROOT / "mp4" / "frames_solr"
RAW_DIR = FRAMES_BASE_DIR / "raw"
PROCESSED_DIR = FRAMES_BASE_DIR / "processed"

ARCHITECTURE_IMAGE = DIRECTORY / "georag_final.png"
VIDEO_PATH = OUTPUT_DIR / "georag_walkthrough.mp4"

PORT = 8085
FPS = 10

# Definition of states for the walkthrough with highlight boxes
STATES = [
    {
        "name": "welcome", 
        "duration_s": 4.5, 
        "step_active": 6, 
        "title": "Inicio del Espacio de Datos", 
        "desc": "Carga inicial de la plataforma Geo-RAG Explorer. El sistema inicializa el mapa interactivo de activos mineros y se conecta con el inspector de Apache Solr para auditoría.",
        "inputs": "Página de inicio / Carga de la web",
        "outputs": "Mapa de España con 6 activos mineros cargados",
        "highlights": []
    },
    {
        "name": "typing_1_1", 
        "duration_s": 1.2, 
        "step_active": 1, 
        "title": "Caso 1: Consulta del Investigador", 
        "desc": "El investigador escribe una pregunta sobre depósitos de Wolframio en Galicia para evaluar su potencial de reprocesamiento. Se activa el primer paso del pipeline.",
        "inputs": "Teclado del investigador",
        "outputs": "Pregunta: 'Buscar escombreras'",
        "highlights": [
            {"type": "arch", "box": [35, 160, 270, 370]}  # Card 1: Usuario
        ]
    },
    {
        "name": "typing_1_2", 
        "duration_s": 2.2, 
        "step_active": 1, 
        "title": "Caso 1: Consulta del Investigador", 
        "desc": "El investigador escribe una pregunta sobre depósitos de Wolframio en Galicia para evaluar su potencial de reprocesamiento. Se activa el primer paso del pipeline.",
        "inputs": "Teclado del investigador",
        "outputs": "Pregunta: 'Buscar escombreras con potencial de wolframio en Galicia cerca de explotaciones activas.'",
        "highlights": [
            {"type": "arch", "box": [35, 160, 270, 370]}  # Card 1: Usuario
        ]
    },
    {
        "name": "processing_1_1", 
        "duration_s": 2.0, 
        "step_active": 2, 
        "title": "Caso 1: Extracción NER en Solr", 
        "desc": "El API REST recibe la pregunta y llama al componente NER (OpenNLP) en Solr. En producción, la llamada HTTP/POST a la API REST '/api/chat' resolvería esto en milisegundos.",
        "inputs": "Texto: 'Buscar escombreras con potencial de wolframio en Galicia...'",
        "outputs": "Entidades extraídas: wolframio [MINERAL], Galicia [REGION], activas [STATUS]",
        "highlights": [
            {"type": "arch", "box": [380, 160, 270, 370]},  # Card 2: API REST
            {"type": "arch", "box": [725, 160, 270, 370]},  # Card 3: Apache Solr
            {"type": "webapp", "box": [10, 64, 620, 666]}  # Chat Feed Spinner
        ]
    },
    {
        "name": "processing_1_2", 
        "duration_s": 2.0, 
        "step_active": 3, 
        "title": "Caso 1: Búsqueda Vectorial (kNN)", 
        "desc": "Solr ejecuta una consulta vectorial densa (kNN) utilizando el operador '{!knn}'. Busca los 10 fragmentos de PDFs más similares en el espacio semántico de 1024-dim.",
        "inputs": "Vector de consulta (1024 dimensiones)",
        "outputs": "Top 10 fragmentos de PDFs con su puntuación de similitud (score)",
        "highlights": [
            {"type": "arch", "box": [740, 240, 105, 105]},  # Vector search icon inside Solr
            {"type": "webapp", "box": [10, 64, 620, 666]}  # Chat Feed Spinner
        ]
    },
    {
        "name": "processing_1_3", 
        "duration_s": 2.0, 
        "step_active": 4, 
        "title": "Caso 1: Filtro Geográfico y Facetado", 
        "desc": "Solr aplica el filtro espacial '{!geofilt}' usando el centroide y radio extraídos por el NER. Esto restringe físicamente la búsqueda de estériles a la región de Galicia.",
        "inputs": "Centroide: [42.575, -8.133], Radio d=100km",
        "outputs": "Resultados de Solr filtrados geográficamente en Galicia",
        "highlights": [
            {"type": "arch", "box": [865, 240, 105, 105]},  # Location map icon inside Solr
            {"type": "webapp", "box": [10, 64, 620, 666]}  # Chat Feed Spinner
        ]
    },
    {
        "name": "processing_1_4", 
        "duration_s": 2.0, 
        "step_active": 5, 
        "title": "Caso 1: Generación de Respuesta (LLM)", 
        "desc": "El pipeline recoge las evidencias estructuradas de Solr y las pasa como contexto junto con el prompt del sistema al modelo LLM (Gemini 3 Pro) para sintetizar la respuesta.",
        "inputs": "Prompt contextualizado + 3 fragmentos de PDFs de Solr",
        "outputs": "Procesando generación de lenguaje natural en Gemini...",
        "highlights": [
            {"type": "arch", "box": [1100, 160, 270, 370]},  # Card 4: Evidencias Documentales
            {"type": "arch", "box": [1055, 500, 280, 245]},  # Bottom right: Structured context
            {"type": "webapp", "box": [10, 64, 620, 666]}  # Chat Feed Spinner
        ]
    },
    {
        "name": "result_1_1", 
        "duration_s": 3.5, 
        "step_active": 6, 
        "title": "Caso 1: Respuesta Narrativa de la IA", 
        "desc": "El LLM genera la respuesta en lenguaje natural estructurado en HTML. El mapa se desplaza y enfoca automáticamente en el activo principal: Mina de Penouta (Ourense).",
        "inputs": "Respuesta en lenguaje natural del LLM",
        "outputs": "Mapeo interactivo enfocado y ficha técnica actualizada",
        "highlights": [
            {"type": "arch", "box": [1400, 160, 270, 370]},  # Card 5: Síntesis con LLM
            {"type": "webapp", "box": [640, 64, 640, 451]}  # Map focused on Penouta
        ]
    },
    {
        "name": "result_1_2", 
        "duration_s": 4.0, 
        "step_active": 6, 
        "title": "Caso 1: Evidencias Científicas de Solr", 
        "desc": "Se muestran las tarjetas de evidencias bibliográficas recuperadas de Solr. Cada tarjeta enlaza al PDF y detalla la página, score y entidades NER identificadas.",
        "inputs": "Metadatos y fragmentos de PDFs recuperados de Solr",
        "outputs": "3 Fichas de evidencias científicas mostradas en la web",
        "highlights": [
            {"type": "arch", "box": [640, 550, 395, 175]},  # Card JSON: Respuesta estructurada
            {"type": "webapp", "box": [10, 64, 620, 666]}  # Chat Feed Evidences Area
        ]
    },
    {
        "name": "result_1_3", 
        "duration_s": 3.0, 
        "step_active": 6, 
        "title": "Caso 1: Inspección de Facetas en Solr", 
        "desc": "El inspector del motor (Solr Engine Inspector) muestra la distribución facetada de los resultados calculada por Solr (conteo por regiones, minerales y estado de proyectos).",
        "inputs": "Pestaña 'Solr Facets' seleccionada en el inspector",
        "outputs": "Facetas JSON: galicia (2), tungsten (2), tin (2), active (1), inactive (1)",
        "highlights": [
            {"type": "arch", "box": [640, 550, 395, 175]},  # Card JSON: Respuesta estructurada
            {"type": "webapp", "box": [10, 786, 1260, 194]}  # Inspector panel (yellow highlight)
        ]
    },
    {
        "name": "result_1_4", 
        "duration_s": 3.0, 
        "step_active": 6, 
        "title": "Caso 1: Entidades NER Extraídas", 
        "desc": "El inspector del motor detalla el JSON de entidades extraídas de la pregunta original. Esto audita las decisiones que toma el pipeline para construir los filtros.",
        "inputs": "Pestaña 'NER Entities' seleccionada en el inspector",
        "outputs": "JSON NER: { entities: [ { text: 'wolframio', label: 'MINERAL' }, ... ] }",
        "highlights": [
            {"type": "arch", "box": [640, 550, 395, 175]},  # Card JSON: Respuesta estructurada
            {"type": "webapp", "box": [10, 786, 1260, 194]}  # Inspector panel (yellow highlight)
        ]
    },
    {
        "name": "typing_2", 
        "duration_s": 2.5, 
        "step_active": 1, 
        "title": "Caso 2: Consulta Normativa", 
        "desc": "El investigador escribe una segunda pregunta sobre la normativa ambiental aplicable a la valorización de estériles mineros en Castilla y León.",
        "inputs": "Teclado del investigador",
        "outputs": "Pregunta: 'Normativa ambiental aplicable a la valorización de estériles de mina en Castilla y León.'",
        "highlights": [
            {"type": "arch", "box": [35, 160, 270, 370]}  # Card 1: Usuario
        ]
    },
    {
        "name": "processing_2", 
        "duration_s": 2.0, 
        "step_active": 4, 
        "title": "Caso 2: Búsqueda Semántica en Solr", 
        "desc": "El pipeline ejecuta una consulta híbrida sobre textos legislativos en Solr, filtrando por la provincia de Salamanca y estado activo.",
        "inputs": "Palabras clave: normativa, reutilizacion, esteriles",
        "outputs": "Evidencias sobre RD 975/2009 y Ley 7/2022 de Residuos",
        "highlights": [
            {"type": "arch", "box": [725, 160, 270, 370]}  # Card 3: Solr
        ]
    },
    {
        "name": "result_2_1", 
        "duration_s": 3.0, 
        "step_active": 6, 
        "title": "Caso 2: Respuesta y Geolocalización", 
        "desc": "El LLM explica el marco legal (RD 975/2009) y el estatuto de subproducto. El mapa se desplaza y enfoca en el Proyecto Barruecopardo (Salamanca).",
        "inputs": "Respuesta normativa de la IA",
        "outputs": "Ficha técnica de Barruecopardo en Salamanca",
        "highlights": [
            {"type": "arch", "box": [1400, 160, 270, 370]},  # Card 5: LLM
            {"type": "webapp", "box": [640, 64, 640, 451]}  # Map zoomed on Barruecopardo
        ]
    },
    {
        "name": "result_2_2", 
        "duration_s": 3.5, 
        "step_active": 6, 
        "title": "Caso 2: Evidencias y Facetas", 
        "desc": "Se cargan las evidencias de normativas mineras en la web. El inspector muestra el facetado de leyes (RD 975/2009 es el más referenciado).",
        "inputs": "Pestaña 'Solr Facets' seleccionada en el inspector",
        "outputs": "Fichas de normativas + conteo de leyes referenciadas",
        "highlights": [
            {"type": "arch", "box": [640, 550, 395, 175]},  # Card JSON: Respuesta estructurada
            {"type": "webapp", "box": [10, 64, 620, 666]},  # Chat evidences
            {"type": "webapp", "box": [10, 786, 1260, 194]}  # Inspector facets panel (yellow highlight)
        ]
    },
    {
        "name": "typing_3", 
        "duration_s": 2.5, 
        "step_active": 1, 
        "title": "Caso 3: Subproductos Críticos", 
        "desc": "El investigador busca balsas de residuos con presencia de materias primas críticas como el cobalto o tierras raras.",
        "inputs": "Teclado del investigador",
        "outputs": "Pregunta: 'Localizar balsas de residuos con presencia de cobalto o tierras raras.'",
        "highlights": [
            {"type": "arch", "box": [35, 160, 270, 370]}  # Card 1: Usuario
        ]
    },
    {
        "name": "processing_3", 
        "duration_s": 2.0, 
        "step_active": 5, 
        "title": "Caso 3: Procesamiento LLM", 
        "desc": "El modelo de IA sintetiza las evidencias encontradas para Penouta (tierras raras en micas) y Las Cruces (cobalto en pirita) y responde.",
        "inputs": "Pregunta de subproductos críticos",
        "outputs": "Generación de respuesta agregada para múltiples activos",
        "highlights": [
            {"type": "arch", "box": [1400, 160, 270, 370]}  # Card 5: LLM
        ]
    },
    {
        "name": "result_3_1", 
        "duration_s": 3.0, 
        "step_active": 6, 
        "title": "Caso 3: Respuesta del Agente", 
        "desc": "La IA detalla los depósitos. El mapa vuela automáticamente a Cobre Las Cruces (Sevilla), la primera coincidencia del listado.",
        "inputs": "Respuesta de subproductos + mapa",
        "outputs": "Actualización de ficha de Cobre Las Cruces",
        "highlights": [
            {"type": "arch", "box": [1400, 160, 270, 370]},  # Card 5: LLM
            {"type": "webapp", "box": [640, 64, 640, 451]}  # Map zoomed on Las Cruces
        ]
    },
    {
        "name": "result_3_2", 
        "duration_s": 4.5, 
        "step_active": 6, 
        "title": "Caso 3: Evidencias Finales del Espacio", 
        "desc": "El inspector muestra las entidades NER extraídas en formato JSON. Se comprueba el flujo de datos completo del prototipo.",
        "inputs": "Pestaña 'NER Entities' seleccionada",
        "outputs": "Entidades: cobalto [MINERAL], tierras raras [MINERAL_GROUP]",
        "highlights": [
            {"type": "arch", "box": [640, 550, 395, 175]},  # Card JSON
            {"type": "webapp", "box": [10, 786, 1260, 194]}  # Inspector NER panel (yellow highlight)
        ]
    }
]

class MyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), MyHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()

def draw_multiline_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font: ImageFont.ImageFont, max_width: int, fill: str) -> int:
    paragraphs = text.split('\n')
    current_y = y
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            # For empty lines, just add vertical spacing
            current_y += int(draw.textbbox((0, 0), "A", font=font)[3] * 1.3)
            continue
            
        words = paragraph.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            line_str = ' '.join(current_line)
            if draw.textlength(line_str, font=font) <= max_width:
                pass
            else:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
            
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=fill)
            current_y += int(draw.textbbox((0, 0), "A", font=font)[3] * 1.3)
            
    return current_y

def draw_neon_box(draw: ImageDraw.ImageDraw, box: list[int], color: str, width: int = 3):
    x1, y1, x2, y2 = box
    draw.rectangle((x1, y1, x2, y2), outline=color, width=width)

def scale_arch_box(box: list[int]) -> list[int]:
    x, y, w, h = box
    scale_x = 600 / 1672
    scale_y = 338 / 941
    new_x = 1300 + (x * scale_x)
    new_y = 130 + (y * scale_y)
    new_w = w * scale_x
    new_h = h * scale_y
    return [int(new_x), int(new_y), int(new_x + new_w), int(new_y + new_h)]

def scale_webapp_box(box: list[int]) -> list[int]:
    x, y, w, h = box
    new_y = 80 + y
    return [int(x), int(new_y), int(x + w), int(new_y + h)]

def make_intro_frame() -> Image.Image:
    canvas = Image.new("RGB", (1920, 1080), "#070a13")
    draw = ImageDraw.Draw(canvas)
    
    font_large = load_font(44, bold=True)
    font_sub = load_font(24, bold=False)
    font_desc = load_font(15, bold=False)
    font_watermark = load_font(11, bold=True)
    
    # Glow panel background
    draw.rounded_rectangle((100, 200, 1820, 880), radius=16, fill="#0d1322", outline="#1e2942", width=2)
    
    # Title & Line separator
    draw.text((150, 320), "DEMOSTRACIÓN DE PIPELINE DE DATOS", fill="#10b981", font=font_large)
    draw.text((150, 390), "Geo-RAG Explorer: Espacio de Datos de Materias Primas Críticas", fill="white", font=font_sub)
    draw.line((150, 460, 1770, 460), fill="#1e2942", width=2)
    
    desc_text = (
        "Esta simulación ilustra el flujo completo de datos en nuestro pipeline híbrido:\n\n"
        "  1. Consulta en Lenguaje Natural  -->  Entrada del usuario al chat.\n"
        "  2. Extracción de Entidades NER  -->  Reconocimiento de minerales, regiones y filtros con OpenNLP.\n"
        "  3. Búsqueda Vectorial (kNN)     -->  Comparación semántica en Solr sobre dense_vector (1024-dim).\n"
        "  4. Restricción Geoespacial      -->  Filtrado de coordenadas dentro del radio de estudio ({!geofilt}).\n"
        "  5. Síntesis y Citas RAG (LLM)   -->  Generación de respuestas basadas en evidencias reales por Gemini.\n\n"
        "El video demuestra el funcionamiento del flujo con datos ficticios/api simulada antes del ajuste con la infraestructura real."
    )
    draw_multiline_text(draw, desc_text, 150, 490, font_desc, 1500, "#94a3b8")
    
    # Watermark info
    draw.text((150, 820), "PROTOTIPO DE VALIDACIÓN  |  CONSORCIO CRM DATA SPACE  |  2026", fill="#475569", font=font_watermark)
    
    return canvas

def compose_frame(
    screenshot_path: Path,
    architecture_img: Image.Image,
    state_info: dict
) -> Image.Image:
    # 1. Create base canvas 1920x1080
    canvas_w, canvas_h = 1920, 1080
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#070a13")
    draw = ImageDraw.Draw(canvas)

    # 2. Draw Header Banner
    draw.rectangle((0, 0, canvas_w, 80), fill="#0d1322")
    draw.line((0, 80, canvas_w, 80), fill="#1e2942", width=1)
    
    font_title = load_font(22, bold=True)
    draw.text((30, 24), "Geo-RAG Explorer · Demo del Pipeline de Datos", fill="white", font=font_title)
    
    # Prototipo badge
    badge_x1, badge_y1 = 1580, 22
    badge_x2, badge_y2 = 1890, 58
    draw.rounded_rectangle((badge_x1, badge_y1, badge_x2, badge_y2), radius=6, fill="#022c22", outline="#047857", width=1)
    font_badge = load_font(10, bold=True)
    draw.text((badge_x1 + 18, badge_y1 + 10), "PROTOTIPO ACADÉMICO SOLR + LLM", fill="#34d399", font=font_badge)

    # 3. Paste Webapp Screenshot (1280x1000)
    if screenshot_path.exists():
        screenshot = Image.open(screenshot_path)
        canvas.paste(screenshot, (0, 80))

    # 4. Draw Right Column (640px wide, from x=1280)
    draw.line((1280, 80, 1280, canvas_h), fill="#1e2942", width=1)

    # Title "ARQUITECTURA DEL PIPELINE"
    font_section = load_font(15, bold=True)
    draw.text((1300, 100), "ARQUITECTURA DEL PIPELINE", fill="#94a3b8", font=font_section)

    # Paste Architecture Diagram (600x338)
    arch_resized = architecture_img.resize((600, 338), Image.Resampling.LANCZOS)
    canvas.paste(arch_resized, (1300, 130))
    draw.rectangle((1300, 130, 1900, 468), outline="#1e2942", width=2)

    # Title "ESTADO DE PROCESAMIENTO"
    draw.text((1300, 485), "ESTADO DE PROCESAMIENTO", fill="#94a3b8", font=font_section)

    # Draw vertical timeline
    steps = [
        "1. Consulta del Usuario",
        "2. Extracción NER (OpenNLP)",
        "3. Búsqueda Vectorial (kNN)",
        "4. Búsqueda Geográfica (Spatial)",
        "5. Síntesis de Respuesta (LLM)",
        "6. Visualización e Inspección"
    ]
    step_active = state_info["step_active"]
    draw.line((1325, 520, 1325, 710), fill="#1e2942", width=3)
    
    font_timeline = load_font(12, bold=False)
    font_timeline_bold = load_font(12, bold=True)
    
    for idx, step_name in enumerate(steps, start=1):
        step_y = 520 + (idx - 1) * 38
        
        if idx == step_active:
            circle_color = "#10b981"
            circle_outline = "#34d399"
            text_color = "white"
            font_to_use = font_timeline_bold
            circle_width = 2
        elif idx < step_active:
            circle_color = "#047857"
            circle_outline = "#047857"
            text_color = "#94a3b8"
            font_to_use = font_timeline
            circle_width = 1
        else:
            circle_color = "#1e2942"
            circle_outline = "#1e2942"
            text_color = "#475569"
            font_to_use = font_timeline
            circle_width = 1
            
        r = 6
        draw.ellipse((1325 - r, step_y - r, 1325 + r, step_y + r), fill=circle_color, outline=circle_outline, width=circle_width)
        draw.text((1345, step_y - 8), step_name, fill=text_color, font=font_to_use)

    # Explanation card
    card_x1, card_y1 = 1300, 755
    card_x2, card_y2 = 1900, 1055
    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=10, fill="#0d1322", outline="#1e2942", width=2)

    font_card_title = load_font(14, bold=True)
    draw.text((card_x1 + 20, card_y1 + 15), state_info["title"].upper(), fill="#10b981", font=font_card_title)

    font_field_lbl = load_font(11, bold=True)
    font_field_val = load_font(11, bold=False)
    font_desc = load_font(10.5, bold=False)
    
    draw.text((card_x1 + 20, card_y1 + 45), "ENTRADA:", fill="#fbbf24", font=font_field_lbl)
    draw.text((card_x1 + 95, card_y1 + 45), state_info["inputs"], fill="#f1f5f9", font=font_field_val)

    draw.text((card_x1 + 20, card_y1 + 70), "SALIDA:", fill="#34d399", font=font_field_lbl)
    draw_multiline_text(draw, state_info["outputs"], card_x1 + 95, card_y1 + 70, font_field_val, 480, "#f1f5f9")

    draw.line((card_x1 + 20, card_y1 + 125, card_x2 - 20, card_y1 + 125), fill="#1e2942", width=1)
    draw_multiline_text(draw, state_info["desc"], card_x1 + 20, card_y1 + 138, font_desc, 560, "#94a3b8")

    # 5. Draw Highlights
    for hl in state_info["highlights"]:
        if hl["type"] == "arch":
            scaled_box = scale_arch_box(hl["box"])
            draw_neon_box(draw, scaled_box, color="#22c55e", width=3)  # Green for architecture
        elif hl["type"] == "webapp":
            scaled_box = scale_webapp_box(hl["box"])
            # Color yellow for JSON inspector highlights, green for others
            color = "#FFFF00" if hl["box"][1] >= 750 else "#22c55e"
            draw_neon_box(draw, scaled_box, color=color, width=4)

    return canvas

def main():
    print("=" * 60)
    print("  Improved Geo-RAG Explorer Walkthrough Video Generator")
    print("=" * 60)
    
    # Ensure directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean old processed frames
    for f in PROCESSED_DIR.glob("*.png"):
        f.unlink()

    # Load architecture diagram
    if not ARCHITECTURE_IMAGE.exists():
        print(f"[ERROR] Architecture image not found at {ARCHITECTURE_IMAGE}")
        return
    arch_img = Image.open(ARCHITECTURE_IMAGE).convert("RGB")

    # Start HTTP Server on background thread
    print("[INFO] Starting local HTTP server on port 8085...")
    httpd = start_server()
    time.sleep(1.5)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        print(f"[ERROR] Chrome path not found: {chrome_path}")
        httpd.shutdown()
        return

    # Loop through states and capture screenshots
    print("[INFO] Capturing webapp screenshots (saved in raw/ subdirectory)...")
    temp_screenshots = []
    
    for idx, state in enumerate(STATES, start=1):
        state_name = state["name"]
        raw_img_path = RAW_DIR / f"{state_name}.png"
        
        # Capture raw screenshot if it doesn't exist, to avoid recapture if raw frames already exist
        if not raw_img_path.exists():
            print(f" -> Capturing state {idx}/{len(STATES)}: {state_name}...")
            url = f"http://localhost:{PORT}/index_video.html?state={state_name}"
            
            cmd = [
                f'"{chrome_path}"',
                "--headless=old",
                "--disable-gpu",
                "--window-size=1280,1000",
                "--virtual-time-budget=3000",
                f'--screenshot="{raw_img_path}"',
                f'"{url}"'
            ]
            subprocess.run(" ".join(cmd), shell=True, capture_output=True)
            
            # Simple fallback if virtual budget fails
            if not raw_img_path.exists():
                cmd_simple = [
                    f'"{chrome_path}"',
                    "--headless=old",
                    "--disable-gpu",
                    "--window-size=1280,1000",
                    f'--screenshot="{raw_img_path}"',
                    f'"{url}"'
                ]
                subprocess.run(" ".join(cmd_simple), shell=True, capture_output=True)
        else:
            print(f" -> Reusing raw screenshot for state {idx}/{len(STATES)}: {state_name}...")

        if raw_img_path.exists():
            temp_screenshots.append((raw_img_path, state))
        else:
            print(f" [ERROR] Hard failure capturing state {state_name}!")

    # Compose frames
    print("[INFO] Composing video frames (saved in processed/ subdirectory)...")
    frame_idx = 1
    frame_paths = []
    
    # 1. Add Intro scene (2 seconds at 10 FPS = 20 frames)
    print(" -> Creating and rendering Intro slide...")
    intro_img = make_intro_frame()
    for _ in range(20):
        intro_path = PROCESSED_DIR / f"frame_{frame_idx:04d}.png"
        intro_img.save(intro_path)
        frame_paths.append(intro_path)
        frame_idx += 1
        
    # 2. Add composed screenshots
    for screenshot_path, state_info in temp_screenshots:
        print(f" -> Composing frames for state: {state_info['name']}...")
        frame_image = compose_frame(screenshot_path, arch_img, state_info)
        
        # Duplicate frame to match duration in seconds
        duration_s = state_info["duration_s"]
        num_dups = max(1, round(duration_s * FPS))
        
        for _ in range(num_dups):
            dup_path = PROCESSED_DIR / f"frame_{frame_idx:04d}.png"
            frame_image.save(dup_path)
            frame_paths.append(dup_path)
            frame_idx += 1

    # Compile frames to MP4
    print(f"[INFO] Joining {len(frame_paths)} frames into video: {VIDEO_PATH}...")
    
    images = [Image.open(fp).convert("RGB") for fp in frame_paths]
    
    # Ensure dimensions are multiples of 16 (H.264 requirement)
    max_w = ((1920 + 15) // 16) * 16
    max_h = ((1080 + 15) // 16) * 16
    
    normalized = []
    for img in images:
        canvas = Image.new("RGB", (max_w, max_h), "black")
        canvas.paste(img, (0, 0))
        normalized.append(canvas)

    # Render video
    with imageio.get_writer(str(VIDEO_PATH), fps=FPS, codec="libx264", quality=9, macro_block_size=16) as writer:
        for img in normalized:
            writer.append_data(np.array(img))
            
    print(f"[SUCCESS] Video successfully generated and saved at: {VIDEO_PATH}")

    # Shutdown HTTP server
    print("[INFO] Shutting down HTTP server...")
    httpd.shutdown()
    httpd.server_close()
    
    # Clean up processed frames (but keeping raw screenshots in raw/)
    print("[INFO] Cleaning up temporary processed frames...")
    for f in PROCESSED_DIR.glob("*.png"):
        try:
            f.unlink()
        except:
            pass
    try:
        PROCESSED_DIR.rmdir()
    except:
        pass
        
    print("=" * 60)
    print("  Generation complete. Walkthrough video is ready!")
    print("=" * 60)

if __name__ == "__main__":
    main()
