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

# Known US bank names for header scanning
_KNOWN_BANKS = [
    "BancFirst", "BancorpSouth", "PEOPLESSOUTH BANK", "PeopleSouth",
    "Chase", "JPMorgan", "Wells Fargo", "Bank of America", "PNC", "TD Bank",
    "BMO", "Truist", "Santander", "Navy Federal", "Fifth Third", "US Bank",
    "M&T Bank", "Fulton Bank", "Tab Bank", "First Enterprise",
    "First Kansas", "First Service", "Five Star", "Forbright",
    "Indiana Members", "LMCU", "Mercury", "Stellar", "Exchange Bank",
    "Wayne Bank", "Timberlake", "Regions", "SunTrust", "KeyBank", "Citibank",
    "Capital One", "Ally Bank", "Discover Bank", "BBVA", "Huntington",
    "Regions Bank", "First National", "Citizens Bank",
]
_KNOWN_BANK_RE = re.compile(
    r"\b(" + "|".join(re.escape(b) for b in _KNOWN_BANKS) + r")\b",
    re.IGNORECASE,
)


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
                r"^\s*([A-Z][A-Z0-9 '&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.?))\s+Customer\s+Number",
                # BancFirst: two name lines before "DBA ..."
                r"^\s*([A-Z][A-Z\s]{4,50})\n(?:[A-Z][A-Z\s]{3,40}\n)?DBA\s",
                # BancorpSouth: "SNEADS TIRE AND OIL LLC Date 3/31/26"
                r"^\s*([A-Z][A-Z0-9\s'&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.?))\s+Date\s+\d",
                # Greeting
                r"(?:Dear|Attn\.?)\s+([A-Z][a-zA-Z\s,\.]+)",
                # All-caps LLC/INC name on its own line
                r"^\s*([A-Z][A-Z\s'&]{5,50}(?:LLC|INC|CORP|CO\.?|LTD\.?))(?:\s*$|\s+Page\s+\d)",
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
            # BANK NAME
            # ----------------------------------------------------------------
            "bank_name": [
                # Explicit label
                r"(?:^|\n)(?:Bank|Financial\s+Institution)\s*:?\s*([^\n]{3,50})",
                # Known bank name anywhere in header
                r"(PEOPLESSOUTH\s+BANK|PeopleSouth|BancFirst|BancorpSouth|"
                r"Chase|JPMorgan|Wells\s*Fargo|Bank\s+of\s+America|PNC|TD\s+Bank|"
                r"BMO|Truist|Santander|Navy\s+Federal|Fifth\s+Third|US\s+Bank|"
                r"M&T\s+Bank|Fulton\s+Bank|Tab\s+Bank|First\s+Enterprise|"
                r"First\s+Kansas|First\s+Service|Five\s+Star|Forbright|"
                r"Indiana\s+(?:Members)?|LMCU|Mercury|Stellar|Exchange\s+Bank|"
                r"Wayne\s+Bank|Timberlake|Regions\s+Bank?|SunTrust|KeyBank|"
                r"Citibank|Capital\s+One|Ally\s+Bank|Discover\s+Bank|BBVA|"
                r"Huntington|First\s+National|Citizens\s+Bank)",
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
                # "** Ending Balance 12/31/25 1,555.28-" → extract the date
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
                # Prefer business names with LLC/INC/etc.
                if (
                    re.match(r"^\s*[A-Z][A-Z0-9\s'&,\.]{4,60}(?:LLC|INC|CORP|CO\.?|LTD\.?)(?:\s|$)", line)
                    and not _JUNK_HOLDER_FRAGMENTS.search(line)
                ):
                    metadata["account_holder"] = line
                    recovered = True
                    break
            if not recovered:
                del metadata["account_holder"]

        # --- bank_name ---
        bank = metadata.get("bank_name", "")
        if bank:
            # Reject if it starts with digits (transaction artefact)
            if re.match(r"^\d", bank):
                del metadata["bank_name"]
                bank = ""
            elif len(bank.strip()) > 55:
                del metadata["bank_name"]
                bank = ""

        # If still missing, scan known banks in first 500 chars
        if not metadata.get("bank_name"):
            m = _KNOWN_BANK_RE.search(header_text[:500])
            if m:
                metadata["bank_name"] = m.group(1)

        # BancFirst uses "BNCF:XXXXXXX" marker — detect it
        if not metadata.get("bank_name") and "BNCF:" in header_text[:500]:
            metadata["bank_name"] = "BancFirst"

        return metadata


def extract_document_metadata(raw_text: str) -> Dict[str, Optional[str]]:
    return MetadataExtractor().extract_metadata(raw_text)