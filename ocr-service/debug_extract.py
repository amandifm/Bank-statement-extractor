import sys
import time
import logging
from app.services.transaction_service import extract_transactions_from_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_name = sys.argv[1]
file_path = f"C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/{file_name}"

print(f"Starting extraction for {file_name}...")
start = time.time()
try:
    result = extract_transactions_from_file(file_path)
    print(f"Extraction successful! Found {len(result.get('transactions', []))} transactions.")
except Exception as e:
    print(f"Extraction failed: {e}")
print(f"Total time: {time.time() - start:.2f} seconds")
