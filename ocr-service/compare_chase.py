import fitz

pdf_path = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements/Chase Bank.pdf"
doc = fitz.open(pdf_path)
text = doc[0].get_text()

for line in text.split("\n"):
    if "$" in line:
        print(line.strip())
