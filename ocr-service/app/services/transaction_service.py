import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2

from app.services.paddle_service import extract_lines
from app.services.parser_service import parse_bank_statement
from app.services.pdf_service import (
    extract_lines_from_digital_pdf,
    is_digital_pdf,
    pdf_to_images,
)
from app.services.preprocess_service import preprocess_image

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def extract_transactions_from_file(file_path: str) -> dict:
    """Extract transactions from a bank statement file.

    Digital PDFs bypass the render→OCR pipeline entirely: text is extracted
    directly via pdfplumber at 100 % accuracy.  Scanned PDFs and image files
    continue to use the preprocess → PaddleOCR path.
    """
    source = Path(file_path)
    suffix = source.suffix.lower()

    logger.info("Starting extraction for file: %s (type: %s)", source.name, suffix)

    # ── Digital PDF fast path ──────────────────────────────────────────────
    if suffix == ".pdf" and is_digital_pdf(file_path):
        logger.info("Digital PDF detected — using direct text extraction (no OCR)")
        try:
            all_lines = extract_lines_from_digital_pdf(file_path)
            pages = [{"page": 1, "line_count": len(all_lines), "status": "processed"}]
            parsed = parse_bank_statement(all_lines)
            parsed["pages"] = pages
            logger.info(
                "Digital extraction complete: %d transactions", len(parsed["transactions"])
            )
            return parsed
        except Exception as e:
            logger.error("Digital extraction failed, falling back to OCR: %s", e)
            # Fall through to OCR path

    # ── OCR path (scanned PDF or image) ──────────────────────────────────
    with TemporaryDirectory() as temp_dir:
        try:
            if suffix == ".pdf":
                logger.info("Scanned PDF — converting to images at 300 DPI...")
                image_paths = pdf_to_images(str(source), temp_dir)
                logger.info("PDF converted to %d images", len(image_paths))
            elif suffix in IMAGE_EXTENSIONS:
                logger.info("Processing %s image directly", suffix)
                image_paths = [str(source)]
            else:
                raise ValueError(
                    "Unsupported file type. Upload a PDF or image bank statement."
                )
        except Exception as e:
            logger.error("Failed to prepare images: %s", e)
            raise

        all_lines: list = []
        pages: list = []

        for page_number, image_path in enumerate(image_paths, start=1):
            try:
                logger.info(
                    "Processing page %d/%d: %s", page_number, len(image_paths), image_path
                )
                image = preprocess_image(image_path)
                processed_path = str(Path(temp_dir) / f"processed-{page_number}.png")
                cv2.imwrite(processed_path, image)

                lines = extract_lines(processed_path, page_number)
                logger.info("Page %d: extracted %d text lines", page_number, len(lines))

                all_lines.extend(lines)
                pages.append(
                    {"page": page_number, "line_count": len(lines), "status": "processed"}
                )
            except Exception as e:
                logger.error("Error processing page %d: %s", page_number, e)
                pages.append(
                    {
                        "page": page_number,
                        "line_count": 0,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        logger.info("Parsing %d total lines into transactions...", len(all_lines))
        try:
            parsed = parse_bank_statement(all_lines)
            parsed["pages"] = pages
            logger.info(
                "Extraction complete: %d transactions found", len(parsed["transactions"])
            )
            return parsed
        except Exception as e:
            logger.error("Failed to parse transactions: %s", e)
            raise
