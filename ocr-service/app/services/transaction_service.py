import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2

from app.services.paddle_service import extract_lines
from app.services.parser_service import parse_bank_statement
from app.services.pdf_service import pdf_to_images
from app.services.preprocess_service import preprocess_image

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def extract_transactions_from_file(file_path: str) -> dict:
    """Extract transactions from a bank statement file."""
    source = Path(file_path)
    suffix = source.suffix.lower()
    
    logger.info(f"Starting extraction for file: {source.name} (type: {suffix})")

    with TemporaryDirectory() as temp_dir:
        # Step 1: Convert to images
        try:
            if suffix == ".pdf":
                logger.info("Converting PDF to images...")
                image_paths = pdf_to_images(str(source), temp_dir)
                logger.info(f"PDF converted to {len(image_paths)} images")
            elif suffix in IMAGE_EXTENSIONS:
                logger.info(f"Processing {suffix} image directly")
                image_paths = [str(source)]
            else:
                raise ValueError("Unsupported file type. Upload a PDF or image bank statement.")
        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            raise
        
        # Step 2: Extract text from each page
        all_lines = []
        pages = []
        
        for page_number, image_path in enumerate(image_paths, start=1):
            try:
                logger.info(f"Processing page {page_number}/{len(image_paths)}")
                
                # Preprocess image
                image = preprocess_image(image_path)
                processed_path = str(Path(temp_dir) / f"processed-{page_number}.png")
                cv2.imwrite(processed_path, image)
                
                # Extract text lines using OCR
                lines = extract_lines(processed_path, page_number)
                logger.info(f"Page {page_number}: Extracted {len(lines)} text lines")
                
                all_lines.extend(lines)
                pages.append({
                    "page": page_number,
                    "line_count": len(lines),
                    "status": "processed"
                })
            except Exception as e:
                logger.error(f"Error processing page {page_number}: {e}")
                pages.append({
                    "page": page_number,
                    "line_count": 0,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Step 3: Parse transactions
        logger.info(f"Parsing {len(all_lines)} total lines into transactions...")
        try:
            parsed = parse_bank_statement(all_lines)
            parsed["pages"] = pages
            
            logger.info(f"Extraction complete: {len(parsed['transactions'])} transactions found")
            logger.debug(f"Summary: {parsed['summary']}")
            
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse transactions: {e}")
            raise
