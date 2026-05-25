import logging
from pathlib import Path
from typing import List

import fitz
import pdfplumber

logger = logging.getLogger(__name__)

# zoom=2.77 ≈ 200 DPI (72 DPI × 2.77)
_OCR_ZOOM = 2.77


def is_digital_pdf(pdf_path: str) -> bool:
    """Return True when the PDF has extractable text (not a scanned image)."""
    try:
        doc = fitz.open(pdf_path)
        for page_index in range(min(2, doc.page_count)):
            if len(doc[page_index].get_text().strip()) > 100:
                return True
        return False
    except Exception:
        return False


def extract_lines_from_digital_pdf(pdf_path: str) -> List[dict]:
    """
    Extract structured lines directly from a digital PDF using pdfplumber word
    positions.  This avoids the render→OCR round-trip and gives perfect
    character accuracy for all digital bank statements.

    Special handling included for:
    - Navy Federal: two-column layout where date+desc is on the left and
      amount+balance is on the right of the same horizontal band.
    - US Bank: month token on one line, day+description on the next.
    - BMO / Santander / Tab Bank / TD Bank: standard wide single-column tables.
    """
    all_lines: List[dict] = []

    def line_from_words(words: List[dict], page_number: int, page_width: float) -> dict:
        words.sort(key=lambda w: w["x0"])
        text = " ".join(w["text"] for w in words)
        x0_vals = [w["x0"] for w in words]
        x1_vals = [w["x1"] for w in words]
        y0_vals = [w["top"] for w in words]
        y1_vals = [w["bottom"] for w in words]
        return {
            "text": text,
            "confidence": 1.0,
            "page": page_number,
            "items": [
                {
                    "text": w["text"],
                    "confidence": 1.0,
                    "x_min": float(w["x0"]),
                    "x_max": float(w["x1"]),
                    "y_min": float(w["top"]),
                    "y_max": float(w["bottom"]),
                    "page": page_number,
                }
                for w in words
            ],
            "x_min": float(min(x0_vals)),
            "x_max": float(max(x1_vals)),
            "y_min": float(min(y0_vals)),
            "y_max": float(max(y1_vals)),
            "page_width": page_width,
        }

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(
                x_tolerance=4,
                y_tolerance=4,
                keep_blank_chars=False,
                use_text_flow=False,
            )
            if not words:
                continue

            # Adaptive Y-gap: use median word height × 0.55
            # Tighter than before (was 6 pt) to avoid merging two-column rows
            # that happen to share the same Y band (Navy Federal).
            heights = [w["bottom"] - w["top"] for w in words]
            median_h = sorted(heights)[len(heights) // 2] if heights else 12
            Y_GAP = max(4, median_h * 0.55)

            # Group words into horizontal lines
            lines: List[List[dict]] = []
            for word in words:
                merged = False
                for line in reversed(lines):
                    ref_y = (line[0]["top"] + line[0]["bottom"]) / 2
                    word_y = (word["top"] + word["bottom"]) / 2
                    if abs(ref_y - word_y) <= Y_GAP:
                        line.append(word)
                        merged = True
                        break
                if not merged:
                    lines.append([word])

            page_width = float(page.width) if page.width else 612.0

            for line_words in lines:
                if not any(w["text"].strip() for w in line_words):
                    continue
                all_lines.append(line_from_words(line_words, page_number, page_width))

    if not all_lines:
        logger.info("pdfplumber produced no words; falling back to PyMuPDF words")
        document = fitz.open(pdf_path)
        try:
            for page_index, page in enumerate(document, start=1):
                fitz_words = page.get_text("words")
                if not fitz_words:
                    continue
                page_width = float(page.rect.width)
                converted = [
                    {
                        "text": str(w[4]),
                        "x0": float(w[0]),
                        "top": float(w[1]),
                        "x1": float(w[2]),
                        "bottom": float(w[3]),
                    }
                    for w in fitz_words
                    if str(w[4]).strip()
                ]
                heights = [w["bottom"] - w["top"] for w in converted]
                median_h = sorted(heights)[len(heights) // 2] if heights else 12
                y_gap = max(4, median_h * 0.55)
                lines: List[List[dict]] = []
                for word in sorted(converted, key=lambda w: (w["top"], w["x0"])):
                    word_y = (word["top"] + word["bottom"]) / 2
                    for line in reversed(lines):
                        ref_y = (line[0]["top"] + line[0]["bottom"]) / 2
                        if abs(ref_y - word_y) <= y_gap:
                            line.append(word)
                            break
                    else:
                        lines.append([word])
                for line_words in lines:
                    all_lines.append(line_from_words(line_words, page_index, page_width))
        finally:
            document.close()

    logger.info(
        "Digital-PDF extraction produced %d lines from %s", len(all_lines), pdf_path
    )
    return all_lines


def pdf_to_images(pdf_path: str, output_dir: str, zoom: float = _OCR_ZOOM) -> List[str]:
    """Render each PDF page to a PNG at ~300 DPI for OCR."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    image_paths: List[str] = []

    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = str(Path(output_dir) / f"page-{page_index + 1}.png")
        pixmap.save(image_path)
        image_paths.append(image_path)

    document.close()
    return image_paths
