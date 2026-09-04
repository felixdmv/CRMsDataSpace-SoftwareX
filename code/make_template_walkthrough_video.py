#!/usr/bin/env python3
"""
Create a walkthrough video from the expert template workbook by automating Excel,
editing cells step by step, capturing ranges as images, and joining them into MP4.
"""
from __future__ import annotations

import shutil
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import pywintypes
import pythoncom
import win32com.client


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
OUTPUT_ROOT = PROJECT_ROOT / "mp4"
FRAMES_DIR = OUTPUT_ROOT / "frames_es"
WORKBOOK_COPY = OUTPUT_ROOT / "plantilla_expertos_unfc_es_demo.xlsx"
VIDEO_PATH = OUTPUT_ROOT / "plantilla_expertos_unfc_es_demo.mp4"
SOURCE_WORKBOOK = ROOT / "templates" / "es" / "plantilla_expertos_unfc_es.xlsx"
FPS = 10
TYPING_DURATION_S = 1.0


@dataclass
class EditAction:
    cell: str
    value: str
    overlay: str
    duration_s: float = 2.2
    highlight_range: str | None = None
    as_text: bool = False


@dataclass
class Step:
    sheet: str
    range_addr: str
    caption: str
    duration_s: float
    edits: list[EditAction] = field(default_factory=list)
    highlight_range: str | None = None


@dataclass
class CaptureResult:
    image: Image.Image
    base_left: float
    base_top: float
    base_width: float
    base_height: float


STEPS = [
    Step(
        sheet="LEEME",
        range_addr="A1:D8",
        caption="Hoja 1. LEEME. Esta hoja explica el contenido de cada pestaña, que deben rellenar los expertos y desde que fila deben empezar.",
        duration_s=4.5,
    ),
    Step(
        sheet="registro_informes",
        range_addr="A16:O23",
        caption="Hoja 2. registro_informes. Una fila por PDF. Aqui se registran los metadatos basicos del informe y del activo asociado.",
        duration_s=4.0,
    ),
    Step(
        sheet="registro_informes",
        range_addr="A18:O22",
        caption="La fila EXPERTOS se rellena paso a paso para que se vea claramente como avanza el registro.",
        duration_s=3.0,
        highlight_range="A22:O22",
        edits=[
            EditAction("B22", "Aguablanca_demo_expertos.pdf", "Se añade el nombre del PDF en B22.", highlight_range="B22", as_text=True),
            EditAction("C22", "Informe tecnico resumido para validacion de plantilla", "Se añade el titulo del informe en C22.", highlight_range="C22", as_text=True),
            EditAction("D22", "Consorcio CRM Data Space", "Se añade la empresa o entidad responsable en D22.", highlight_range="D22", as_text=True),
            EditAction("E22", "España", "Se añade el pais principal del activo en E22.", highlight_range="E22", as_text=True),
            EditAction("F22", "Extremadura", "Se añade la region geografica o administrativa en F22.", highlight_range="F22", as_text=True),
        ],
    ),
    Step(
        sheet="registro_informes",
        range_addr="A18:O22",
        caption="Despues completamos la descripcion del activo para que el documento quede bien contextualizado.",
        duration_s=3.0,
        edits=[
            EditAction("G22", "mina", "Se añade el tipo de fuente en G22: mina.", highlight_range="G22", as_text=True),
            EditAction("H22", "Aguablanca", "Se añade el nombre del activo en H22.", highlight_range="H22", as_text=True),
            EditAction("I22", "deposito mineral de niquel-cobre", "Se describe el material o fuente en I22.", highlight_range="I22", as_text=True),
            EditAction("J22", "niquel|cobre", "Se listan los elementos observados en J22.", highlight_range="J22", as_text=True),
            EditAction("K22", "PFS", "Se añade el nivel de estudio reportado en K22.", highlight_range="K22", as_text=True),
        ],
    ),
    Step(
        sheet="registro_informes",
        range_addr="A18:O22",
        caption="Cerramos la fila con trazabilidad de revision y una nota opcional.",
        duration_s=3.0,
        edits=[
            EditAction("L22", "2026", "Se añade el año o fecha efectiva en L22.", highlight_range="L22", as_text=True),
            EditAction("M22", "Experto ejemplo", "Se añade el nombre del experto en M22.", highlight_range="M22", as_text=True),
            EditAction("N22", "en_progreso", "Se añade el estado de revision en N22.", highlight_range="N22", as_text=True),
            EditAction("O22", "Fila demostrativa para el video.", "Se añade una nota opcional en O22.", highlight_range="O22", as_text=True),
        ],
    ),
    Step(
        sheet="evaluacion_unfc",
        range_addr="A16:N21",
        caption="Hoja 3. evaluacion_unfc. Aqui se registra una unica clasificacion UNFC para el activo completo, no una por elemento.",
        duration_s=4.0,
    ),
    Step(
        sheet="evaluacion_unfc",
        range_addr="A17:N21",
        caption="La fila EXPERTOS se rellena tambien paso a paso para mostrar que la clasificacion es del conjunto del activo.",
        duration_s=3.0,
        highlight_range="A21:N21",
        edits=[
            EditAction("B21", "Aguablanca_demo_expertos.pdf", "Se añade el PDF de referencia en B21.", highlight_range="B21", as_text=True),
            EditAction("C21", "Aguablanca", "Se añade el nombre del activo en C21.", highlight_range="C21", as_text=True),
            EditAction("D21", "E1;F2;G2", "Se añade el codigo UNFC final del activo en D21.", highlight_range="D21", as_text=True),
            EditAction("E21", "E1", "Se añade la categoria E final en E21.", highlight_range="E21", as_text=True),
            EditAction("F21", "F2", "Se añade la categoria F final en F21.", highlight_range="F21", as_text=True),
            EditAction("G21", "G2", "Se añade la categoria G final en G21.", highlight_range="G21", as_text=True),
            EditAction("H21", "1", "Se añade el codigo de base de cantidad en H21.", highlight_range="H21"),
            EditAction("I21", "18500", "Se añade la cantidad medida en I21.", highlight_range="I21"),
            EditAction("J21", "24300", "Se añade la cantidad indicada en J21.", highlight_range="J21"),
            EditAction("K21", "9100", "Se añade la cantidad inferida en K21.", highlight_range="K21"),
            EditAction("L21", "t", "Se añade la unidad comun en L21.", highlight_range="L21", as_text=True),
            EditAction("M21", "12-14,31-33", "Se añaden las paginas clave en M21.", highlight_range="M21", as_text=True),
            EditAction("N21", "Ejemplo de clasificacion del activo en su conjunto.", "Se añade la justificacion del experto en N21.", highlight_range="N21", as_text=True),
        ],
    ),
    Step(
        sheet="evidencia_ejes",
        range_addr="A1:I35",
        caption="Hoja 4. evidencia_ejes. La parte superior explica las variables sugeridas y sus escalas para justificar cada eje.",
        duration_s=4.0,
    ),
    Step(
        sheet="evidencia_ejes",
        range_addr="A50:I57",
        caption="Debajo, la fila EXPERTOS se rellena con una variable concreta que justifica la clasificacion en el eje E.",
        duration_s=3.0,
        highlight_range="A55:I55",
        edits=[
            EditAction("B55", "Aguablanca_demo_expertos.pdf", "Se añade el PDF de referencia en B55.", highlight_range="B55", as_text=True),
            EditAction("C55", "Aguablanca", "Se añade el activo en C55.", highlight_range="C55", as_text=True),
            EditAction("D55", "E", "Se indica que la evidencia afecta al eje E en D55.", highlight_range="D55", as_text=True),
            EditAction("E55", "viabilidad_economica", "Se añade la variable usada para justificar E en E55.", highlight_range="E55", as_text=True),
            EditAction("F55", "3", "Se añade el valor numerico asignado a la variable en F55.", highlight_range="F55"),
            EditAction("G55", "12-14", "Se añaden las paginas de evidencia en G55.", highlight_range="G55", as_text=True),
            EditAction("H55", "La prefactibilidad apoya viabilidad alta.", "Se añade un extracto o resumen breve en H55.", highlight_range="H55", as_text=True),
            EditAction("I55", "Variable clave para E1.", "Se añade el comentario experto en I55.", highlight_range="I55", as_text=True),
        ],
    ),
    Step(
        sheet="evidencia_ejes",
        range_addr="A50:I59",
        caption="Seguimos con mas evidencias. Un G2 puede justificarse con varias variables complementarias y por eso añadimos tantas filas como haga falta.",
        duration_s=3.0,
        edits=[
            EditAction("B56", "Aguablanca_demo_expertos.pdf", "Nueva fila de evidencia: mismo PDF en B56.", highlight_range="B56", as_text=True),
            EditAction("C56", "Aguablanca", "Nueva fila de evidencia: mismo activo en C56.", highlight_range="C56", as_text=True),
            EditAction("D56", "G", "Se indica que esta evidencia afecta al eje G en D56.", highlight_range="D56", as_text=True),
            EditAction("E56", "muestreo", "Se añade la variable muestreo en E56.", highlight_range="E56", as_text=True),
            EditAction("F56", "2", "Se añade el valor numerico del muestreo en F56.", highlight_range="F56"),
            EditAction("G56", "31-33", "Se añaden paginas de apoyo para muestreo en G56.", highlight_range="G56", as_text=True),
            EditAction("H56", "Cobertura intermedia del muestreo.", "Se resume la evidencia de muestreo en H56.", highlight_range="H56", as_text=True),
            EditAction("I56", "Contribuye a G2.", "Se explica la contribucion de esta variable en I56.", highlight_range="I56", as_text=True),
            EditAction("B57", "Aguablanca_demo_expertos.pdf", "Otra evidencia adicional: PDF en B57.", highlight_range="B57", as_text=True),
            EditAction("C57", "Aguablanca", "Otra evidencia adicional: activo en C57.", highlight_range="C57", as_text=True),
            EditAction("D57", "G", "La nueva evidencia tambien afecta al eje G en D57.", highlight_range="D57", as_text=True),
            EditAction("E57", "criticidad", "Se añade la variable criticidad en E57.", highlight_range="E57", as_text=True),
            EditAction("F57", "2", "Se añade el valor numerico de criticidad en F57.", highlight_range="F57"),
            EditAction("G57", "5-6", "Se añaden paginas de apoyo para criticidad en G57.", highlight_range="G57", as_text=True),
            EditAction("H57", "Material con relevancia estrategica media.", "Se resume la evidencia de criticidad en H57.", highlight_range="H57", as_text=True),
            EditAction("I57", "Variable adicional para justificar G.", "Se explica la utilidad de esta variable en I57.", highlight_range="I57", as_text=True),
        ],
    ),
    Step(
        sheet="pares_qa",
        range_addr="A13:K18",
        caption="Hoja 5. pares_qa. Aqui se guardan preguntas en ingles y respuestas gold para evaluar despues los modelos.",
        duration_s=4.0,
        highlight_range="A18:K18",
        edits=[
            EditAction("B18", "Aguablanca_demo_expertos.pdf", "Se añade el PDF de referencia en B18.", highlight_range="B18", as_text=True),
            EditAction("C18", "Aguablanca", "Se añade el activo consultado en C18.", highlight_range="C18", as_text=True),
            EditAction("D18", "UNFC", "Se añade el tipo de pregunta en D18.", highlight_range="D18", as_text=True),
            EditAction("E18", "What is the overall UNFC code assigned to the Aguablanca asset?", "Se añade la pregunta en ingles en E18.", highlight_range="E18", as_text=True),
            EditAction("F18", "E1;F2;G2.", "Se añade la respuesta gold corta en F18.", highlight_range="F18", as_text=True),
            EditAction("G18", "The expert classifies the Aguablanca asset as E1;F2;G2 based on project viability, project maturity, and geological confidence.", "Se añade la respuesta gold larga en G18.", highlight_range="G18", as_text=True),
            EditAction("H18", "E1;F2;G2|Aguablanca", "Se añaden terminos obligatorios en H18.", highlight_range="H18", as_text=True),
            EditAction("I18", "E1 F2 G2", "Se añaden alternativas aceptables en I18.", highlight_range="I18", as_text=True),
            EditAction("J18", "12-14,31-33", "Se añaden paginas fuente en J18.", highlight_range="J18", as_text=True),
            EditAction("K18", "Ejemplo de respuesta gold para evaluacion automatica.", "Se añade la nota del revisor en K18.", highlight_range="K18", as_text=True),
        ],
    ),
    Step(
        sheet="LEEME",
        range_addr="A1:D8",
        caption="Resultado final. Hemos recorrido desde el LEEME hasta la ultima hoja, mostrando como se completa la plantilla paso a paso.",
        duration_s=4.5,
    ),
]


def ensure_dirs() -> None:
    OUTPUT_ROOT.mkdir(exist_ok=True)
    FRAMES_DIR.mkdir(exist_ok=True)


def clear_frames() -> None:
    for file in FRAMES_DIR.glob("*.png"):
        file.unlink()


def copy_workbook() -> None:
    shutil.copy2(SOURCE_WORKBOOK, WORKBOOK_COPY)


def grab_clipboard_image(retries: int = 20, delay: float = 0.25) -> Image.Image:
    for _ in range(retries):
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        time.sleep(delay)
    raise RuntimeError("No se pudo capturar la imagen desde el portapapeles de Excel.")


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def capture_range(sheet, range_addr: str) -> CaptureResult:
    com_retry(lambda: sheet.Activate())
    base_range = com_retry(lambda: sheet.Range(range_addr))
    com_retry(lambda: base_range.CopyPicture(Format=2))
    time.sleep(0.5)
    return CaptureResult(
        image=grab_clipboard_image(),
        base_left=float(base_range.Left),
        base_top=float(base_range.Top),
        base_width=float(base_range.Width),
        base_height=float(base_range.Height),
    )


def com_retry(fn, retries: int = 20, delay: float = 0.5):
    last_error = None
    for _ in range(retries):
        try:
            return fn()
        except pywintypes.com_error as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def range_rect(sheet, base_capture: CaptureResult, target_range_addr: str) -> tuple[float, float, float, float]:
    target = com_retry(lambda: sheet.Range(target_range_addr))
    x = (float(target.Left) - base_capture.base_left) / max(base_capture.base_width, 1.0)
    y = (float(target.Top) - base_capture.base_top) / max(base_capture.base_height, 1.0)
    w = float(target.Width) / max(base_capture.base_width, 1.0)
    h = float(target.Height) / max(base_capture.base_height, 1.0)
    return x, y, w, h


def prepare_cell(sheet, cell_addr: str, as_text: bool = False) -> None:
    target = com_retry(lambda: sheet.Range(cell_addr))
    row = target.Row
    col = target.Column
    source = com_retry(lambda: sheet.Cells(max(1, row - 1), col))
    target.NumberFormat = source.NumberFormat
    target.HorizontalAlignment = source.HorizontalAlignment
    target.VerticalAlignment = source.VerticalAlignment
    target.WrapText = source.WrapText
    if as_text:
        target.NumberFormat = "@"


def draw_sheet_tabs(draw: ImageDraw.ImageDraw, canvas_width: int, canvas_height: int, sheet_names: list[str], active_sheet: str) -> None:
    tab_y = canvas_height - 88
    tab_x = 60
    tab_gap = 10
    tab_font = load_font(24, bold=False)
    for name in sheet_names:
        text_width = int(draw.textlength(name, font=tab_font))
        tab_width = max(150, text_width + 36)
        is_active = name == active_sheet
        fill = "#FFFFFF" if is_active else "#E5E7EB"
        outline = "#2563EB" if is_active else "#CBD5E1"
        text = "#0F172A" if is_active else "#475569"
        draw.rounded_rectangle((tab_x, tab_y, tab_x + tab_width, tab_y + 42), radius=10, fill=fill, outline=outline, width=3 if is_active else 1)
        draw.text((tab_x + 18, tab_y + 8), name, fill=text, font=tab_font)
        tab_x += tab_width + tab_gap


def compose_frame(
    capture: CaptureResult,
    title: str,
    subtitle: str,
    active_sheet: str,
    sheet_names: list[str],
    highlight_text: str | None = None,
    highlight_box: tuple[float, float, float, float] | None = None,
) -> Image.Image:
    canvas_w, canvas_h = 1920, 1080
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#F3F6FA")
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(34, bold=True)
    body_font = load_font(26, bold=False)
    strong_font = load_font(40, bold=True)

    draw.rectangle((0, 0, canvas_w, 96), fill="#0F172A")
    draw.text((56, 26), title, fill="white", font=title_font)

    viewport = (60, 120, 1860, 780)
    draw.rounded_rectangle(viewport, radius=16, fill="#FFFFFF", outline="#CBD5E1", width=2)

    image = capture.image
    inner_left, inner_top = viewport[0] + 24, viewport[1] + 24
    inner_width, inner_height = viewport[2] - viewport[0] - 48, viewport[3] - viewport[1] - 48
    scale = min(inner_width / image.width, inner_height / image.height)
    render_w = int(image.width * scale)
    render_h = int(image.height * scale)
    offset_x = inner_left + (inner_width - render_w) // 2
    offset_y = inner_top + (inner_height - render_h) // 2
    resized = image.resize((render_w, render_h), Image.Resampling.LANCZOS)
    canvas.paste(resized, (offset_x, offset_y))

    if highlight_box:
        rx, ry, rw, rh = highlight_box
        x1 = int(offset_x + rx * render_w)
        y1 = int(offset_y + ry * render_h)
        x2 = int(x1 + rw * render_w)
        y2 = int(y1 + rh * render_h)
        draw.rounded_rectangle((x1 - 6, y1 - 6, x2 + 6, y2 + 6), radius=10, outline="#F97316", width=6)

    subtitle_box = (60, 812, 1860, 980)
    draw.rounded_rectangle(subtitle_box, radius=16, fill="#FFFFFF", outline="#CBD5E1", width=2)
    wrapped = textwrap.fill(subtitle, width=88)
    draw.text((88, 836), wrapped, fill="#111827", font=body_font)
    if highlight_text:
        draw.text((88, 904), highlight_text, fill="#B45309", font=strong_font)

    draw_sheet_tabs(draw, canvas_w, canvas_h, sheet_names, active_sheet)
    return canvas


def render_video(frame_paths: list[Path], output_path: Path, fps: int = FPS) -> None:
    images = [Image.open(frame_path).convert("RGB") for frame_path in frame_paths]
    max_width = max(image.width for image in images)
    max_height = max(image.height for image in images)
    max_width = ((max_width + 15) // 16) * 16
    max_height = ((max_height + 15) // 16) * 16

    normalized = []
    for image in images:
        canvas = Image.new("RGB", (max_width, max_height), "white")
        offset = ((max_width - image.width) // 2, (max_height - image.height) // 2)
        canvas.paste(image, offset)
        normalized.append(canvas)

    with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8, macro_block_size=16) as writer:
        for image in normalized:
            writer.append_data(np.array(image))


def add_frame_copy(frame_paths: list[Path], image: Image.Image, frame_idx: int) -> int:
    frame_path = FRAMES_DIR / f"{frame_idx:04d}.png"
    image.save(frame_path)
    frame_paths.append(frame_path)
    return frame_idx + 1


def build_walkthrough() -> tuple[list[Path], Path]:
    pythoncom.CoInitialize()
    ensure_dirs()
    clear_frames()
    copy_workbook()

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = True
    excel.DisplayAlerts = False
    excel.ScreenUpdating = True
    excel.WindowState = -4137  # Maximized

    frame_paths: list[Path] = []
    try:
        workbook = com_retry(lambda: excel.Workbooks.Open(str(WORKBOOK_COPY.resolve())))
        time.sleep(2.0)
        com_retry(lambda: workbook.Windows(1)).Zoom = 90
        sheet_names = [workbook.Worksheets(i).Name for i in range(1, workbook.Worksheets.Count + 1)]

        frame_idx = 1
        for idx, step in enumerate(STEPS, start=1):
            sheet = com_retry(lambda: workbook.Worksheets(step.sheet))
            com_retry(lambda: workbook.Save())
            capture = capture_range(sheet, step.range_addr)
            step_highlight = range_rect(sheet, capture, step.highlight_range) if step.highlight_range else None
            framed = compose_frame(
                capture,
                f"Plantilla UNFC · {step.sheet}",
                step.caption,
                active_sheet=step.sheet,
                sheet_names=sheet_names,
                highlight_box=step_highlight,
            )

            repeats = max(1, round(step.duration_s * FPS))
            for _ in range(repeats):
                frame_idx = add_frame_copy(frame_paths, framed, frame_idx)

            for edit in step.edits:
                prepare_cell(sheet, edit.cell, as_text=edit.as_text)
                com_retry(lambda s=sheet, c=edit.cell: setattr(s.Range(c), "Value", ""))
                text = edit.value
                typing_frames = max(1, round(TYPING_DURATION_S * FPS))
                total_chars = max(1, len(text))
                for frame_number in range(1, typing_frames + 1):
                    chars_to_show = max(1, round(frame_number * total_chars / typing_frames))
                    typed = text[:chars_to_show]
                    com_retry(lambda s=sheet, c=edit.cell, v=typed: setattr(s.Range(c), "Value", v))
                    com_retry(lambda: workbook.Save())
                    capture = capture_range(sheet, step.range_addr)
                    highlight_box = range_rect(sheet, capture, edit.highlight_range) if edit.highlight_range else None
                    framed = compose_frame(
                        capture,
                        f"Plantilla UNFC · {step.sheet}",
                        step.caption,
                        active_sheet=step.sheet,
                        sheet_names=sheet_names,
                        highlight_text=edit.overlay,
                        highlight_box=highlight_box,
                    )
                    frame_idx = add_frame_copy(frame_paths, framed, frame_idx)

                capture = capture_range(sheet, step.range_addr)
                highlight_box = range_rect(sheet, capture, edit.highlight_range) if edit.highlight_range else None
                framed = compose_frame(
                    capture,
                    f"Plantilla UNFC · {step.sheet}",
                    step.caption,
                    active_sheet=step.sheet,
                    sheet_names=sheet_names,
                    highlight_text=edit.overlay,
                    highlight_box=highlight_box,
                )
                edit_repeats = max(2, round(edit.duration_s * FPS))
                for _ in range(edit_repeats):
                    frame_idx = add_frame_copy(frame_paths, framed, frame_idx)

        com_retry(lambda: workbook.Close(SaveChanges=True))
    finally:
        try:
            com_retry(lambda: excel.Quit(), retries=10, delay=0.5)
        finally:
            pythoncom.CoUninitialize()

    render_video(frame_paths, VIDEO_PATH, fps=FPS)
    return frame_paths, VIDEO_PATH


def main() -> None:
    frames, video = build_walkthrough()
    print(f"Frames generated: {len(frames)}")
    print(f"Video: {video}")


if __name__ == "__main__":
    main()
