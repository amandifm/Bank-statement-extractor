import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Lines that look like names but are NOT account holders
_JUNK_HOLDER_FRAGMENTS = re.compile(
    r"checking|savings|account|business|number|enclosures|balance|credit|debit|"
    r"service|charge|interest|period|average|ledger|fdic|statement|page|date|"
    r"activity|deposits|withdrawals|essentials|primary|member|notice|reverse|"
    r"important|information|continued|reverse|dir\s+\d|bncf:|temp",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# BANK-SPECIFIC FINGERPRINTS
# Each entry: (canonical_name, list_of_regex_patterns)
# Patterns are tried in order; first match wins.
# All patterns are searched against the first 800 chars of the document.
# ---------------------------------------------------------------------------
_BANK_FINGERPRINTS = [
    # ── Chase / JPMorgan ───────────────────────────────────────────────────
    # Header line 2 is always "JPMorgan Chase Bank, N.A."
    (
        "JPMorgan Chase Bank, N.A.",
        [r"JPMorgan\s+Chase\s+Bank", r"\bChase\.com\b", r"Chase\.com\b"],
    ),
    # ── BMO ────────────────────────────────────────────────────────────────
    # First line is always "bmo.com/contact"
    (
        "BMO Bank",
        [r"\bbmo\.com\b", r"(?:^|\n)bmo\b"],
    ),
    # ── Navy Federal Credit Union ──────────────────────────────────────────
    # No explicit name in header; toll-free number 1-888-842-NFCU is unique
    (
        "Navy Federal Credit Union",
        [r"navy\s*federal", r"888-842-6328", r"navyfederal\.org"],
    ),
    # ── Forbright Bank ────────────────────────────────────────────────────
    # "Forbright Bank" appears as a standalone address line
    (
        "Forbright Bank",
        [r"\bForbright\s+Bank\b", r"\bForbright\b"],
    ),
    # ── LMCU (Lake Michigan Credit Union) ─────────────────────────────────
    # Address block contains "LAKE MICHIGAN CREDIT UNION"
    (
        "Lake Michigan Credit Union",
        [r"LAKE\s+MICHIGAN\s+CREDIT\s+UNION", r"\bLMCU\b"],
    ),
    # ── Santander Bank ────────────────────────────────────────────────────
    # No standalone name line; domain "santanderbank.com" is the only signal
    (
        "Santander Bank",
        [r"santanderbank\.com", r"\bSantander\s+Bank\b", r"\bSantander\b"],
    ),
    # ── Wells Fargo ───────────────────────────────────────────────────────
    # Type 2 (digital): line 1 is "Wells Fargo Business Essentials Ckg"
    # Type 1 (scanned): no text layer — handled separately by fallback
    (
        "Wells Fargo Bank, N.A.",
        [r"Wells\s*Fargo\s+(?:Business|Bank)", r"wellsfargo\.com", r"\bWells\s+Fargo\b"],
    ),
    # ── PNC Bank ──────────────────────────────────────────────────────────
    # "PNC Bank" is a clean standalone line 2.
    # OLD pattern caught "Banking by visiting PNC.com/Enroll" — fixed with
    # a negative-lookahead that rejects "Banking" continuations.
    (
        "PNC Bank",
        [
            r"(?m)^PNC\s+Bank\s*$",                    # exact standalone line
            r"\bPNC\s+Bank\b(?!\s*(?:ing|\.com))",     # word boundary, not "Banking"
        ],
    ),
    # ── U.S. Bank ─────────────────────────────────────────────────────────
    # "U.S. Bank National Association" or "To Contact U.S. Bank" in header
    (
        "U.S. Bank",
        [r"U\.S\.\s+Bank\s+National", r"To\s+Contact\s+U\.S\.\s+Bank", r"\bU\.S\.\s*Bank\b", r"\busbank\.com\b"],
    ),
    # ── Tab Bank ──────────────────────────────────────────────────────────
    # No standalone name line; only signal is "www.TABbank.com"
    (
        "Tab Bank",
        [r"TABbank\.com", r"\bTab\s+Bank\b", r"tabbank\.com"],
    ),
    # ── TD Bank ───────────────────────────────────────────────────────────
    # "TD Business Convenience Plus" is the clearest line
    (
        "TD Bank",
        [r"TD\s+Business\s+Convenience", r"\bTD\s+Bank\b", r"tdbank\.com"],
    ),
    # ── Truist ────────────────────────────────────────────────────────────
    (
        "Truist Bank",
        [r"\bTruist\s+Bank\b", r"\bTruist\b", r"truist\.com"],
    ),
    # ── M&T Bank ──────────────────────────────────────────────────────────
    (
        "M&T Bank",
        [r"\bM\s*&\s*T\s+Bank\b", r"mtb\.com"],
    ),
    # ── Fifth Third Bank ──────────────────────────────────────────────────
    # PDF code "FTCSTMT034" is a unique marker
    (
        "Fifth Third Bank",
        [r"FTCSTMT\d+", r"Fifth\s+Third\s+Bank", r"53\.com"],
    ),
    # ── Fulton Bank ───────────────────────────────────────────────────────
    (
        "Fulton Bank",
        [r"\bFulton\s+Bank\b", r"fultonbank\.com"],
    ),
    # ── Mercury Bank ──────────────────────────────────────────────────────
    # No standalone name; routing number 091311229 belongs to Mercury/Choice Financial
    (
        "Mercury Bank",
        [r"091311229", r"\bMercury\b(?!\s+[A-Z]{2}\b)", r"mercury\.com"],
    ),
    # ── Stellar Bank ──────────────────────────────────────────────────────
    (
        "Stellar Bank",
        [r"\bStellar\s+Bank\b", r"stellarbank\.com"],
    ),
    # ── Exchange Bank ─────────────────────────────────────────────────────
    (
        "Exchange Bank",
        [r"\bExchange\s+Bank\b", r"exchangebank\.com"],
    ),
    # ── Wayne Bank ────────────────────────────────────────────────────────
    (
        "Wayne Bank",
        [r"\bWayne\s+Bank\b", r"waynebank\.com"],
    ),
    # ── Indiana Members Credit Union ──────────────────────────────────────
    (
        "Indiana Members Credit Union",
        [r"Indiana\s+Members\s+Credit\s+Union", r"\bIMCU\b"],
    ),
    # ── First Enterprise Bank ─────────────────────────────────────────────
    (
        "First Enterprise Bank",
        [r"First\s+Enterprise\s+Bank", r"firstenterprisebank\.com"],
    ),
    # ── First Kansas Bank ─────────────────────────────────────────────────
    (
        "First Kansas Bank",
        [r"First\s+Kansas\s+Bank", r"firstkansasbank\.com"],
    ),
    # ── First Service Bank ────────────────────────────────────────────────
    (
        "First Service Bank",
        [r"First\s+Service\s+Bank", r"firstservicebank\.com"],
    ),
    # ── Five Star Bank ────────────────────────────────────────────────────
    (
        "Five Star Bank",
        [r"Five\s+Star\s+Bank", r"fivestarbank\.com"],
    ),
    # ── Forbright Bank (already above) ──────────────────────────────────
    # ── BancFirst ────────────────────────────────────────────────────────
    (
        "BancFirst",
        [r"\bBancFirst\b", r"BNCF:"],
    ),
    # ── BancorpSouth ─────────────────────────────────────────────────────
    (
        "BancorpSouth",
        [r"\bBancorpSouth\b"],
    ),
    # ── Other common banks ───────────────────────────────────────────────
    ("Bank of America",  [r"Bank\s+of\s+America", r"bankofamerica\.com"]),
    ("Citibank",         [r"\bCitibank\b", r"citi\.com"]),
    ("Capital One",      [r"Capital\s+One", r"capitalone\.com"]),
    ("Ally Bank",        [r"\bAlly\s+Bank\b", r"ally\.com"]),
    ("Discover Bank",    [r"\bDiscover\s+Bank\b", r"discover\.com"]),
    ("Huntington Bank",  [r"\bHuntington\b(?!\s+(?:Ave|Dr|Rd|St|Blvd|Lane))", r"huntington\.com"]),
    ("KeyBank",          [r"\bKeyBank\b", r"key\.com"]),
    ("Regions Bank",     [r"\bRegions\s+Bank\b", r"regions\.com"]),
    ("SunTrust Bank",    [r"\bSunTrust\b", r"suntrust\.com"]),
    ("Citizens Bank",    [r"\bCitizens\s+Bank\b", r"citizensbank\.com"]),
    ("First National Bank", [r"First\s+National\s+Bank"]),
]

# Pre-compile all fingerprint patterns
_COMPILED_FINGERPRINTS = [
    (name, [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns])
    for name, patterns in _BANK_FINGERPRINTS
]


def _detect_bank_name(header_text: str) -> Optional[str]:
    """
    Walk every bank's fingerprints in priority order.
    Returns the canonical bank name on first match, or None.
    Searches the first 800 characters (wide enough to catch footer URLs
    but short enough to avoid false matches in transaction bodies).
    """
    search_zone = header_text[:800]
    for canonical_name, compiled_patterns in _COMPILED_FINGERPRINTS:
        for pattern in compiled_patterns:
            if pattern.search(search_zone):
                return canonical_name
    return None


class MetadataExtractor:
    """Extract document metadata from raw OCR/PDF text for any US bank statement."""

    def __init__(self):
        self.patterns = {
            # ----------------------------------------------------------------
            # ACCOUNT HOLDER
            # ----------------------------------------------------------------
            "account_holder": [
                # Explicit label on same line
                r"(?:Account\s+Holder|Account\s+Name|Customer\s+Name|Name\s+on\s+Account)\s*:?\s*([^\n]+)",
                # PeopleSouth: "SNEADS TIRE AND OIL LLC  Customer Number: SAA8460"
                r"^\s*([A-Z][A-Z0-9 '&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.))\s+Customer\s+Number",
                # BancFirst: two name lines before "DBA ..."
                r"^\s*([A-Z][A-Z\s]{4,50})\n(?:[A-Z][A-Z\s]{3,40}\n)?DBA\s",
                # BancorpSouth: "SNEADS TIRE AND OIL LLC Date 3/31/26"
                r"^\s*([A-Z][A-Z0-9\s'&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.))\s+Date\s+\d",
                # Greeting
                r"(?:Dear|Attn\.?)\s+([A-Z][a-zA-Z\s,\.]+)",
                # All-caps LLC/INC name on its own line
                r"^\s*([A-Z][A-Z\s'&]{5,50}(?:LLC|INC|CORP|CO\.?|LTD\.))(?:\s*$|\s+Page\s+\d)",
            ],
            # ----------------------------------------------------------------
            # ACCOUNT NUMBER
            # ----------------------------------------------------------------
            "account_number": [
                r"Account\s+(?:No|Number|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                r"Acct\.?\s*(?:No|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                r"Primary\s+Account\s+(?:Number|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                r"(?:Account|Acct)[\s#:]*([X\d\-]{8,})",
                # Standalone 8-15 digit number on its own line (BancFirst footer area)
                r"^(\d{8,15})$",
            ],
            # ----------------------------------------------------------------
            # BANK NAME  (legacy patterns kept as secondary fallback only)
            # Primary detection is now done by _detect_bank_name() in _validate()
            # ----------------------------------------------------------------
            "bank_name": [
                # Explicit "Bank: XYZ" label — rare but unambiguous
                r"(?:^|\n)Bank\s*:\s*([^\n]{3,50})",
                # "Financial Institution: XYZ" label
                r"Financial\s+Institution\s*:\s*([^\n]{3,50})",
            ],
            # ----------------------------------------------------------------
            # STATEMENT PERIOD START
            # ----------------------------------------------------------------
            "statement_period_start": [
                # "Statement Dates 3/02/26 thru 3/31/26"
                r"Statement\s+Dates?\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(?:thru|to|-)",
                # "Statement Period: 01/01/26 to 01/31/26"
                r"Statement\s+Period\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|-|thru)",
                # "Date Range: 4/1/2026-4/16/2026"
                r"Date\s+Range\s*:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*[-–]",
                # "Beginning Balance 12/01/25"
                r"Beginning\s+Balance\s+(\d{1,2}/\d{1,2}/\d{2,4})",
                r"(?:From|Starting|Begin)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"For\s+the\s+Period\s+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–]",
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\s+through",
            ],
            # ----------------------------------------------------------------
            # STATEMENT PERIOD END
            # ----------------------------------------------------------------
            "statement_period_end": [
                r"Statement\s+Dates?\s+\d{1,2}/\d{1,2}/\d{2,4}\s+(?:thru|to|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})",
                r"Statement\s+Period\s*:?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\s*(?:to|-|thru)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"Date\s+Range\s*:?\s*\d{1,2}/\d{1,2}/\d{2,4}\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{2,4})",
                # "** Ending Balance 12/31/25 1,555.28-"
                r"\*\*\s*Ending\s+Balance\s+(\d{1,2}/\d{1,2}/\d{2,4})",
                r"(?:To|Until|End|Ending|Through)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"through\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
                r"[-–]\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
            ],
            # ----------------------------------------------------------------
            # STATEMENT DATE
            # ----------------------------------------------------------------
            "statement_date": [
                r"(?:Statement\s+Date|As\s+of|As\s+At)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"(?:Statement\s+Date|As\s+of)\s*:?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
                # "STATEMENT DATE 12/31/25" (BancFirst page 2 header)
                r"STATEMENT\s+DATE\s+(\d{1,2}/\d{1,2}/\d{2,4})",
                # Lone date line in the header area (BancFirst: "12/31/25" alone)
                r"^(\d{1,2}/\d{1,2}/\d{2,4})\s*$",
            ],
            # ----------------------------------------------------------------
            # BALANCES
            # ----------------------------------------------------------------
            "beginning_balance": [
                r"(?:Beginning|Opening|Starting)\s+Balance(?:\s+\d{1,2}/\d{1,2}/\d{2,4})?\s*:?\s*\$?([\d,]+\.\d{2})",
            ],
            "ending_balance": [
                r"(?:Ending|Closing)\s+Balance\s*:?\s*\$?([\d,]+\.\d{2})",
                r"\*\*\s*Ending\s+Balance\s+\d{1,2}/\d{2}/\d{2}\s+([\d,]+(?:\.\d{2})?)",
            ],
        }

    def extract_metadata(self, raw_text: str) -> Dict[str, Optional[str]]:
        metadata: Dict[str, Optional[str]] = {}
        header_text = raw_text[:2000]

        for key, patterns in self.patterns.items():
            search_text = (
                header_text
                if key in ("bank_name", "account_holder", "account_number", "statement_date")
                else raw_text
            )
            value = self._extract_field(search_text, patterns)
            if value:
                metadata[key] = self._clean_value(value, key)

        metadata = self._validate(metadata, header_text)
        logger.debug("Extracted metadata: %s", metadata)
        return metadata

    def _extract_field(self, text: str, patterns: list) -> Optional[str]:
        for pattern in patterns:
            try:
                m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    return m.group(1).strip()
            except Exception as e:
                logger.warning("Pattern matching error: %s", e)
        return None

    def _clean_value(self, value: str, field_name: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()

        if "account_number" in field_name:
            value = re.sub(r"[^a-zA-Z0-9\-\*X]", "", value)

        if "balance" in field_name:
            value = value.lstrip("$").strip()

        max_length = 100 if "holder" in field_name else 60
        if len(value) > max_length:
            value = value[:max_length] + "..."

        return value

    def _validate(self, metadata: Dict, header_text: str) -> Dict:
        """Reject values that are clearly wrong and attempt recovery."""

        # --- account_holder ---
        holder = metadata.get("account_holder", "")
        if holder and _JUNK_HOLDER_FRAGMENTS.search(holder):
            recovered = False
            for line in header_text.splitlines():
                line = line.strip()
                if (
                    re.match(r"^\s*[A-Z][A-Z0-9\s'&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.)(?:\s|$)", line)
                    and not _JUNK_HOLDER_FRAGMENTS.search(line)
                ):
                    metadata["account_holder"] = line
                    recovered = True
                    break
            if not recovered:
                del metadata["account_holder"]

        # --- bank_name ---
        # Step 1: validate any legacy-pattern match
        bank = metadata.get("bank_name", "")
        if bank:
            if re.match(r"^\d", bank) or len(bank.strip()) > 55:
                del metadata["bank_name"]
                bank = ""

        # Step 2: always try fingerprint detection (higher accuracy than legacy patterns)
        fingerprint_result = _detect_bank_name(header_text)
        if fingerprint_result:
            # Fingerprint always wins over legacy pattern match
            metadata["bank_name"] = fingerprint_result
        elif not metadata.get("bank_name"):
            # Step 3: BancFirst BNCF marker (legacy fallback)
            if "BNCF:" in header_text[:500]:
                metadata["bank_name"] = "BancFirst"

        return metadata


def extract_document_metadata(raw_text: str) -> Dict[str, Optional[str]]:
    return MetadataExtractor().extract_metadata(raw_text)