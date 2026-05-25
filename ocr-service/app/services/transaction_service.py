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


def _extract_with_ocr(source: Path, suffix: str) -> dict:
    with TemporaryDirectory() as temp_dir:
        try:
            if suffix == ".pdf":
                logger.info("Rendering PDF pages at 300 DPI for OCR...")
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
                    "Processing page %d/%d: %s",
                    page_number,
                    len(image_paths),
                    image_path,
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

        logger.info("Parsing %d total OCR lines into transactions...", len(all_lines))
        parsed = parse_bank_statement(all_lines)
        parsed["pages"] = pages
        logger.info(
            "OCR extraction complete: %d transactions found", len(parsed["transactions"])
        )
        return parsed


def extract_transactions_from_file(file_path: str) -> dict:
    """Extract transactions from a bank statement file.

    Digital PDFs use embedded text first. If that text produces no transactions,
    the service renders the PDF and retries through PaddleOCR.
    """
    source = Path(file_path)
    suffix = source.suffix.lower()

    logger.info("Starting extraction for file: %s (type: %s)", source.name, suffix)

    if suffix == ".pdf" and is_digital_pdf(file_path):
        logger.info("Digital PDF detected; using direct text extraction first")
        try:
            all_lines = extract_lines_from_digital_pdf(file_path)
            pages = [{"page": 1, "line_count": len(all_lines), "status": "processed"}]
            parsed = parse_bank_statement(all_lines)
            parsed["pages"] = pages
            if parsed.get("transactions"):
                logger.info(
                    "Digital extraction complete: %d transactions",
                    len(parsed["transactions"]),
                )
                return parsed
            logger.info("Digital extraction found no transactions; retrying with OCR")
        except Exception as e:
            logger.error("Digital extraction failed, falling back to OCR: %s", e)

    return _extract_with_ocr(source, suffix)
