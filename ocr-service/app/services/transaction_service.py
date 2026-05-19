from pathlib import Path
from tempfile import TemporaryDirectory

import cv2

from app.services.paddle_service import extract_lines
from app.services.parser_service import parse_bank_statement
from app.services.pdf_service import pdf_to_images
from app.services.preprocess_service import preprocess_image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def extract_transactions_from_file(file_path: str) -> dict:
    source = Path(file_path)
    suffix = source.suffix.lower()

    with TemporaryDirectory() as temp_dir:
        if suffix == ".pdf":
            image_paths = pdf_to_images(str(source), temp_dir)
        elif suffix in IMAGE_EXTENSIONS:
            image_paths = [str(source)]
        else:
            raise ValueError("Unsupported file type. Upload a PDF or image bank statement.")

        all_lines = []
        pages = []
        for page_number, image_path in enumerate(image_paths, start=1):
            image = preprocess_image(image_path)
            processed_path = str(Path(temp_dir) / f"processed-{page_number}.png")
            cv2.imwrite(processed_path, image)
            lines = extract_lines(processed_path, page_number)
            all_lines.extend(lines)
            pages.append({"page": page_number, "line_count": len(lines)})

        parsed = parse_bank_statement(all_lines)
        parsed["pages"] = pages
        return parsed
