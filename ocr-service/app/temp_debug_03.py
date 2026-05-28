import os
import fitz
import sys

from app.services.metadata_service import MetadataExtractor

extractor = MetadataExtractor()

pdf_path = r"c:\Users\amank\Downloads\Office\DIFM-Extractor\Statements\03-2026 SNEADS TIRE AND OIL LLC (1).pdf"
doc = fitz.open(pdf_path)
text = doc[0].get_text("text")

print("RAW:", text[:200])

for pat in extractor.patterns["account_holder"]:
    import re
    m = re.search(pat, text[:2000], re.MULTILINE)
    if m:
        print("MATCHED PATTERN:", pat)
        print("MATCHED TEXT:", m.group(1))
    else:
        print("NO MATCH:", pat)
