import logging
from pathlib import Path
from typing import List, Tuple

import fitz
import pdfplumber

logger = logging.getLogger(__name__)

# zoom=4.16 ≈ 300 DPI (72 DPI × 4.16). Previous value was 2.0 (144 DPI) which
# was below the 200 DPI minimum recommended for reliable OCR on small bank fonts.
_OCR_ZOOM = 4.16


def is_digital_pdf(pdf_path: str) -> bool:
    """Return True when the PDF has extractable text (not a scanned image)."""
    try:
        doc = fitz.open(pdf_path)
        # Sample the first two pages to decide
        for page_index in range(min(2, doc.page_count)):
            if len(doc[page_index].get_text().strip()) > 100:
                return True
        return False
    except Exception:
        return False


def extract_lines_from_digital_pdf(pdf_path: str) -> List[dict]:
    """
    Extract structured OCR-like lines directly from a digital PDF using
    pdfplumber word positions.  This avoids the render → OCR round-trip and
    gives perfect character accuracy for all digital bank statements
    (Suncoast, bank-statement-transactions, US_Bank_Statement, etc.).
    """
    all_lines: List[dict] = []

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

            # Group words into lines by y0 proximity (≤6 pt gap = same line)
            Y_GAP = 6
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

            for line_words in lines:
                line_words.sort(key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in line_words)
                if not text.strip():
                    continue
                x0_vals = [w["x0"] for w in line_words]
                x1_vals = [w["x1"] for w in line_words]
                y0_vals = [w["top"] for w in line_words]
                y1_vals = [w["bottom"] for w in line_words]

                # Emit one dict per word so the downstream line_merger / column
                # bucket logic gets the same per-item bounding boxes it expects.
                items = [
                    {
                        "text": w["text"],
                        "confidence": 1.0,
                        "x_min": float(w["x0"]),
                        "x_max": float(w["x1"]),
                        "y_min": float(w["top"]),
                        "y_max": float(w["bottom"]),
                        "page": page_number,
                    }
                    for w in line_words
                ]

                all_lines.append(
                    {
                        "text": text,
                        "confidence": 1.0,
                        "page": page_number,
                        "items": items,
                        "x_min": float(min(x0_vals)),
                        "x_max": float(max(x1_vals)),
                        "y_min": float(min(y0_vals)),
                        "y_max": float(max(y1_vals)),
                    }
                )

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
