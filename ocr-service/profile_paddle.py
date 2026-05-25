import time
import fitz
import os
from tempfile import TemporaryDirectory
from app.services.paddle_service import extract_lines

file_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Truist Bank.pdf"

print("Extracting first page image...")
doc = fitz.open(file_path)
page = doc.load_page(0)

for zoom in [4.16, 2.77, 2.08, 1.38]:
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    with TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, f"test_{zoom}.png")
        pixmap.save(image_path)
        print(f"\nZoom {zoom} (approx {int(zoom * 72)} DPI):")
        start = time.time()
        lines = extract_lines(image_path, 1)
        end = time.time()
        print(f"Time: {end - start:.2f}s | Lines found: {len(lines)}")
