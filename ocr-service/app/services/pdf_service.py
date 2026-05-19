from pathlib import Path
from typing import List

import fitz


def pdf_to_images(pdf_path: str, output_dir: str, zoom: float = 2.0) -> List[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = str(Path(output_dir) / f"page-{page_index + 1}.png")
        pixmap.save(image_path)
        image_paths.append(image_path)

    document.close()
    return image_paths
