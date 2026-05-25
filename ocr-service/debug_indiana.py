import logging
import time
from app.services.pdf_service import extract_lines_from_digital_pdf
from app.services.parser_service import parse_bank_statement

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Indiana Bank.pdf"

start = time.time()
lines = extract_lines_from_digital_pdf(file_path)
t1 = time.time()
print(f"pdf extraction took {t1 - start:.2f} seconds")

parsed = parse_bank_statement(lines)
t2 = time.time()
print(f"parse_bank_statement took {t2 - t1:.2f} seconds")

print(f"Total time: {t2 - start:.2f} seconds")
