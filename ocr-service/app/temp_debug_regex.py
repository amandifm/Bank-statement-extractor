import re
text = """           SNEADS TIRE AND OIL LLC                  Date  3/31/26          Page     1
           7975 HIGHWAY 90                          Primary Account        3620005268
"""
m = re.search(r"^\s*([A-Z][A-Z\s'&]{5,50}(?:LLC|INC|CORP|CO\.?|LTD\.?))\b", text, re.MULTILINE)
print("Match:", m.groups() if m else "No match")
