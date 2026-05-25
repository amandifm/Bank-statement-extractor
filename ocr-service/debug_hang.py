import sys
import fitz
import pdfplumber

file_name = sys.argv[1]
file_path = f"C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/{file_name}"

print(f"Investigating {file_name}...")

doc = fitz.open(file_path)
print(f"Total pages: {doc.page_count}")
for i in range(min(2, doc.page_count)):
    text = doc[i].get_text().strip()
    print(f"Page {i} get_text() length: {len(text)}")
    words = doc[i].get_text("words")
    print(f"Page {i} get_text('words') count: {len(words)}")

print("pdfplumber words:")
with pdfplumber.open(file_path) as pdf:
    for i in range(min(2, len(pdf.pages))):
        page = pdf.pages[i]
        words = page.extract_words()
        print(f"Page {i} extract_words count: {len(words)}")
