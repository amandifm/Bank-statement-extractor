import re
from typing import List

# Rows whose text matches these patterns are almost certainly boilerplate
# and should be dropped before transaction parsing.
_BOILERPLATE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^\s*page\s+\d+\s+of\s+\d+",
        r"member\s+fdic",
        r"equal\s+housing\s+lender",
        r"routing\s+(?:number|no)",
        r"toll.free",
        r"privacy\s+policy",
        r"questions\s+about\s+this\s+statement",
        r"in\s+case\s+of\s+errors",
        r"reconcil",
        r"important\s+(?:account\s+)?information",
        r"regulation\s+[a-z]",
        r"message\s+and\s+data\s+rates",
        r"^\s*(?:continued\s+on\s+next\s+page|subtotal|total)\s*$",
    ]
]


def _is_boilerplate(text: str) -> bool:
    for pat in _BOILERPLATE_PATTERNS:
        if pat.search(text):
            return True
    return False


def detect_table_region(rows: List[dict]) -> List[dict]:
    """
    Filter rows that are clearly non-transactional boilerplate.
    Keeps all rows that might contain transactions, summaries, or headers.

    Intentionally tolerant: it is better to keep a marginal row and let
    the downstream parser skip it than to drop a real transaction here.
    """
    filtered = []
    for row in rows:
        text = row.get("text", "")
        if not text.strip():
            continue
        if _is_boilerplate(text):
            continue
        filtered.append(row)
    return filtered
