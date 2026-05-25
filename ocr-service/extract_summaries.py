import os
import glob
import fitz

pdf_dir = "C:/Users/amank/Downloads/Office/DIFM-Extractor/OCR Testing -Bank Statements"
pdfs = glob.glob(f"{pdf_dir}/*.pdf")

for pdf in pdfs:
    try:
        doc = fitz.open(pdf)
        text = doc[0].get_text()
        
        # Try to find common summary lines
        lines = text.split("\n")
        print(f"\n--- {os.path.basename(pdf)} ---")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in ["deposit", "withdrawal", "addition", "subtraction", "credit", "debit", "balance"]):
                # Print the line and the next line to capture amounts
                print(f"  {line.strip()}")
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and any(c.isdigit() for c in next_line):
                        print(f"    -> {next_line}")
    except Exception as e:
        print(f"Error on {pdf}: {e}")
