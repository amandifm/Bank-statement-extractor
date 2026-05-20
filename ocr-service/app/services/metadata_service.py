import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract document metadata (account name, bank, statement dates, etc.) from OCR text."""

    def __init__(self):
        # Patterns to extract common bank statement metadata
        self.patterns = {
            'account_holder': [
                r'(?:Account Holder|Account Name|Name|Customer Name)\s*:?\s*([^\n]+)',
                r'(?:Dear|Attn)\s+([A-Z][a-zA-Z\s]+)',
            ],
            'account_number': [
                r'(?:Account|Acct|A/C)?\s*(?:Number|No|#)\s*:?\s*([A-Z0-9\-\s]{8,20})',
                r'Account\s+(?:No|Number)\.?\s*:?\s*([0-9\-*]{8,})',
            ],
            'bank_name': [
                r'(?:Bank|Financial Institution|Branch)\s*:?\s*([^\n]+)',
            ],
            'statement_period_start': [
                r'(?:Statement|Period|From)\s+(?:Date|Period)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'statement_period_end': [
                r'(?:To|Until|End)\s+(?:Date)?:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:Statement|Period)\s+(?:Date|Period)?\s*(?:to|-)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'statement_date': [
                r'(?:Date|Statement Date|As of|As At)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
        }

    def extract_metadata(self, raw_text: str) -> Dict[str, Optional[str]]:
        """Extract all available metadata from raw OCR text."""
        metadata = {}

        for key, patterns in self.patterns.items():
            value = self._extract_field(raw_text, patterns)
            if value:
                metadata[key] = self._clean_value(value, key)

        logger.info(f"Extracted metadata: {metadata}")
        return metadata

    def _extract_field(self, text: str, patterns: list) -> Optional[str]:
        """Try each pattern and return the first match."""
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    return match.group(1).strip()
            except Exception as e:
                logger.warning(f"Pattern matching error: {e}")
        return None

    def _clean_value(self, value: str, field_name: str) -> str:
        """Clean and normalize extracted values."""
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value).strip()

        # For account numbers, remove common noise
        if 'account' in field_name:
            value = re.sub(r'[^a-zA-Z0-9\-\*]', '', value)

        # Limit length for display
        max_length = 100 if 'holder' in field_name else 50
        if len(value) > max_length:
            value = value[:max_length] + '...'

        return value


def extract_document_metadata(raw_text: str) -> Dict[str, Optional[str]]:
    """Convenience function to extract metadata from raw OCR text."""
    extractor = MetadataExtractor()
    return extractor.extract_metadata(raw_text)
