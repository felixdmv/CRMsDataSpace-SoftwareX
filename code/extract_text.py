#!/usr/bin/env python3
"""
extract_text.py
Extract text from PDFs under ../pdfs/ and optionally OCR pages without text.
Provides functions used by the indexing pipeline and a small CLI for testing.
"""
import os
import sys
import argparse
from typing import List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDFS_DIR = os.path.join(ROOT, "pdfs")
TEXTS_DIR = os.path.join(os.path.dirname(__file__), "texts")
os.makedirs(TEXTS_DIR, exist_ok=True)


def list_pdfs(pdf_dir: str = PDFS_DIR) -> List[str]:
    pdfs = []
    for dirpath, _, files in os.walk(pdf_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(dirpath, f))
    return sorted(pdfs)


def extract_text_from_pdf(pdf_path: str, ocr_if_needed: bool = True, ocr_languages: str = "eng") -> Tuple[List[str], bool]:
    """Extract text per page from a PDF.

    Returns (pages_text_list, ocr_used_bool).
    If a page has very little text, OCR is attempted for that page (requires pdf2image + pytesseract).
    """
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError("pypdf is required. Install with 'pip install pypdf'") from e

    pages_text: List[str] = []
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"[ERROR] cannot open {pdf_path}: {e}")
        return [], False

    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages_text.append(text)

    pages_to_ocr = [i for i, t in enumerate(pages_text) if len(t.strip()) < 50]
    ocr_used = False
    if pages_to_ocr and ocr_if_needed:
        try:
            from pdf2image import convert_from_path
            from pytesseract import image_to_string
        except Exception as e:
            print(f"[WARN] OCR libraries not available: {e}")
            return pages_text, False

        poppler_path = os.environ.get("POPPLER_PATH", None)
        try:
            images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
        except Exception as e:
            print(f"[WARN] pdf2image failed for {pdf_path}: {e}")
            return pages_text, False

        for idx in pages_to_ocr:
            try:
                img = images[idx]
            except Exception:
                continue
            try:
                ocr_text = image_to_string(img, lang=ocr_languages)
            except Exception as e:
                print(f"[WARN] pytesseract failed on page {idx}: {e}")
                ocr_text = ""
            if ocr_text:
                pages_text[idx] = (pages_text[idx] + "\n" + ocr_text).strip()
                ocr_used = True

    return pages_text, ocr_used


def save_text(pdf_path: str, pages_text: List[str]) -> str:
    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(TEXTS_DIR, basename + ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for i, t in enumerate(pages_text, start=1):
            f.write(f"--- PAGE {i} ---\n")
            f.write(t + "\n\n")
    print(f"[INFO] saved extracted text to {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfs", nargs="*", help="PDF paths to process (default: ../pdfs/*)")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR fallback for pages with little text")
    args = parser.parse_args()
    pdfs = args.pdfs if args.pdfs else list_pdfs()
    if not pdfs:
        print(f"[WARN] No PDFs found in {PDFS_DIR}")
        sys.exit(1)
    for pdf in pdfs:
        print(f"[INFO] Processing {pdf}")
        pages_text, used_ocr = extract_text_from_pdf(pdf, ocr_if_needed=args.ocr)
        print(f"[INFO] pages={len(pages_text)} ocr_used={used_ocr}")
        save_text(pdf, pages_text)
