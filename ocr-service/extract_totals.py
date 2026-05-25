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
            if any(kw in line_lower for kw in ["deposit", "addition", "credit", "withdrawal", "subtraction", "debit"]):
                # Look for lines that have both a keyword and a dollar sign
                if "$" in line or (i + 1 < len(lines) and "$" in lines[i+1]):
                    print(f"  {line.strip()}")
                    if i + 1 < len(lines) and "$" in lines[i+1]:
                        print(f"    -> {lines[i+1].strip()}")
    except Exception as e:
        pass
