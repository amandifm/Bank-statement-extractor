import time
print("Starting imports...")
t0 = time.time()
import fitz
t1 = time.time()
print(f"Import fitz took: {t1 - t0:.2f}s")
from app.services.pdf_service import is_digital_pdf
t2 = time.time()
print(f"Import pdf_service took: {t2 - t1:.2f}s")

file_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Indiana Bank.pdf"

print("Calling fitz.open...")
t3 = time.time()
doc = fitz.open(file_path)
t4 = time.time()
print(f"fitz.open took: {t4 - t3:.2f}s")

print("Calling get_text...")
t5 = time.time()
text = doc[0].get_text().strip()
t6 = time.time()
print(f"get_text took: {t6 - t5:.2f}s")

print("Is digital PDF?", len(text) > 100)
