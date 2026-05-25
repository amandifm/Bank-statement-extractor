from app.services.transaction_service import extract_transactions_from_file
import json

file_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Fifth Third Bank.pdf"
result = extract_transactions_from_file(file_path)

for t in result.get("transactions", [])[:5]:
    print(t)
