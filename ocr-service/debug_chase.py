from app.services.transaction_service import extract_transactions_from_file

file_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Chase Bank.pdf"
result = extract_transactions_from_file(file_path)

debits = 0
credits = 0
for t in result.get("transactions", []):
    if t.get("debit"):
        debits += t["debit"]
    if t.get("credit"):
        credits += t["credit"]

print(f"Chase Bank - Extracted Debits: ${debits:.2f}, Extracted Credits: ${credits:.2f}")
