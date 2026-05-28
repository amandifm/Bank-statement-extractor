import os
import fitz
import sys

from app.services.metadata_service import extract_document_metadata

pdf_dir = r"c:\Users\amank\Downloads\Office\DIFM-Extractor\Statements"
pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

for pdf in pdfs:
    pdf_path = os.path.join(pdf_dir, pdf)
    doc = fitz.open(pdf_path)
    text = ""
    # Just read the first page for metadata
    if len(doc) > 0:
        text = doc[0].get_text("text")
    print("========================================")
    print(f"File: {pdf}")
    print("----------------------------------------")
    print("EXTRACTED METADATA:")
    print(extract_document_metadata(text))
    print("----------------------------------------")
    print("RAW TEXT:")
    print(text[:1500])
    print("========================================")
