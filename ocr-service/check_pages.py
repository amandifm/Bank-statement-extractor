import fitz
for fname in ["Truist Bank.pdf", "Wayne Bank.pdf"]:
    path = f"C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/{fname}"
    doc = fitz.open(path)
    print(f"{fname}: {doc.page_count} pages")
    doc.close()
