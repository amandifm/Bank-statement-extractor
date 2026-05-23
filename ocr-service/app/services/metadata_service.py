import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract document metadata from raw OCR/PDF text for any US bank statement."""

    def __init__(self):
        self.patterns = {
            "account_holder": [
                # Explicit labels
                r"(?:Account\s+Holder|Account\s+Name|Customer\s+Name|Name\s+on\s+Account)\s*:?\s*([^\n]+)",
                # Common greeting patterns
                r"(?:Dear|Attn\.?)\s+([A-Z][a-zA-Z\s,\.]+)",
                # All-caps name block common in US bank statements (2–4 words)
                r"^([A-Z][A-Z\s'&]{5,50}(?:LLC|INC|CORP|CO\.?|LTD\.?)?)$",
            ],
            "account_number": [
                r"Account\s+(?:No|Number|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                r"Acct\.?\s*(?:No|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                # Primary Account Number (Navy Federal, BMO)
                r"Primary\s+Account\s+(?:Number|#)\.?\s*:?\s*([X\*\d\-\s]{6,25})",
                # Masked account like "XX-XXXX-6361"
                r"(?:Account|Acct)[\s#:]*([X\d\-]{8,})",
            ],
            "bank_name": [
                # Explicit label
                r"(?:Bank|Financial\s+Institution)\s*:?\s*([^\n]{3,50})",
                # Well-known names in first 500 chars
                r"(Chase|JPMorgan|Wells\s*Fargo|Bank\s+of\s+America|PNC|TD\s+Bank|"
                r"BMO|Truist|Santander|Navy\s+Federal|Fifth\s+Third|US\s+Bank|"
                r"M&T\s+Bank|Fulton\s+Bank|Tab\s+Bank|First\s+Enterprise|"
                r"First\s+Kansas|First\s+Service|Five\s+Star|Forbright|"
                r"Indiana\s+(?:Members)?|LMCU|Mercury|Stellar|Exchange\s+Bank|"
                r"Wayne\s+Bank|Timberkand|Timberlake)",
            ],
            "statement_period_start": [
                r"(?:Statement\s+Period|Period)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|-)",
                r"(?:From|Starting|Begin)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"For\s+the\s+Period\s+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                # TD Bank: "Jul 01 2025-Jul 31 2025"
                r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–]",
                # "May 31, 2025 through June 30, 2025" (Chase)
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\s+through",
            ],
            "statement_period_end": [
                r"(?:Statement\s+Period|Period)\s*:?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\s*(?:to|-)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"(?:To|Until|End|Ending|Through)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"through\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
                r"[-–]\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
            ],
            "statement_date": [
                r"(?:Statement\s+Date|As\s+of|As\s+At|Date)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                r"(?:Statement\s+Date|As\s+of)\s*:?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
            ],
            "beginning_balance": [
                r"(?:Beginning|Opening|Starting)\s+Balance\s*:?\s*\$?([\d,]+\.\d{2})",
            ],
            "ending_balance": [
                r"(?:Ending|Closing)\s+Balance\s*:?\s*\$?([\d,]+\.\d{2})",
            ],
        }

    def extract_metadata(self, raw_text: str) -> Dict[str, Optional[str]]:
        metadata: Dict[str, Optional[str]] = {}
        # Use only first 2000 chars for header fields (bank name, account, period)
        header_text = raw_text[:2000]

        for key, patterns in self.patterns.items():
            # For bank name, search header only
            search_text = header_text if key in ("bank_name", "account_holder", "account_number") else raw_text
            value = self._extract_field(search_text, patterns)
            if value:
                metadata[key] = self._clean_value(value, key)

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
            # Keep digits, dashes, and masking chars
            value = re.sub(r"[^a-zA-Z0-9\-\*X]", "", value)

        if "balance" in field_name:
            # Strip any stray currency symbols
            value = value.lstrip("$").strip()

        max_length = 100 if "holder" in field_name else 60
        if len(value) > max_length:
            value = value[:max_length] + "..."

        return value


def extract_document_metadata(raw_text: str) -> Dict[str, Optional[str]]:
    return MetadataExtractor().extract_metadata(raw_text)
