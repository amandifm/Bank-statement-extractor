import re
from typing import List, Optional

from app.models.transaction import Transaction

DATE_PATTERNS = [
    r"(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(?P<date>\d{4}[/-]\d{1,2}[/-]\d{1,2})",
    r"(?P<date>\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
    r"(?P<date>\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})",
]

DATE_PATTERN_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in DATE_PATTERNS]

# Require cents so dates/card ids such as 06 or 1111 are never parsed as money.
AMOUNT_PATTERN = re.compile(
    r"(?:^|\s|-)"
    r"(?P<currency>[$])?"
    r"(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})"
    r"(?:\s*(?:CR|DR|D|C))?"
    r"(?=\s|$|-)",
    re.IGNORECASE,
)

HEADER_WORDS = {
    "date",
    "description",
    "particulars",
    "withdrawal",
    "deposit",
    "debit",
    "credit",
    "balance",
    "amount",
    "transaction",
    "cheque",
    "reference",
}

NON_TRANSACTION_PHRASES = {
    "account number",
    "closing balance",
    "opening balance",
    "page no",
    "statement date",
    "statement period",
    "total deposits",
    "total withdrawals",
}


def parse_amount(value: str) -> Optional[float]:
    """Parse a money amount from OCR text."""
    if not value:
        return None

    cleaned = re.sub(r"[^\d.\-,]", "", value).strip()
    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    try:
        return float(cleaned.replace(",", ""))
    except ValueError:
        return None


def looks_like_header(text: str) -> bool:
    """Check if text looks like a header or statement summary row."""
    lowered = text.lower()
    if any(phrase in lowered for phrase in NON_TRANSACTION_PHRASES):
        return True

    header_count = sum(1 for word in HEADER_WORDS if word in lowered)
    return header_count >= 2


def find_date(text: str) -> Optional[re.Match]:
    """Find the first date in a row."""
    for pattern in DATE_PATTERN_COMPILED:
        match = pattern.search(text)
        if match:
            return match
    return None


def detect_type(text: str) -> str:
    """Detect transaction type from text when balance movement is unavailable."""
    lowered = text.lower()

    if any(word in lowered for word in ["cr", "credit", "deposit", "received", "+"]):
        return "Credit"

    if any(word in lowered for word in ["dr", "debit", "withdrawal", "paid", "-"]):
        return "Debit"

    return "Debit"


def clean_description(text: str, date_match: re.Match, first_amount_position: int) -> str:
    """Remove table columns before the transaction details."""
    description = text[date_match.end():first_amount_position].strip(" -|:/")

    # Typical card statement row:
    # processed date, transaction date, card id, transaction details, amount, balance.
    description = re.sub(r"^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+", "", description)
    description = re.sub(r"^\s*\d{3,6}\s+", "", description)
    description = description.strip(" -|:/")

    return description if len(description) >= 2 else "Transaction"


def money_values_from_text(text: str) -> List[float]:
    """Extract positive money values in row order."""
    values = []
    for match in AMOUNT_PATTERN.finditer(text):
        amount = parse_amount(match.group("amount"))
        if amount is not None and amount > 0:
            values.append(amount)
    return values


def parse_transaction_row(
    row: dict,
    index: int,
    previous_balance: Optional[float] = None,
) -> Optional[Transaction]:
    """Parse a single transaction row from OCR output."""
    text = re.sub(r"\s+", " ", row["text"]).strip()

    if not text or looks_like_header(text):
        return None

    date_match = find_date(text)
    if not date_match:
        return None

    amount_matches = list(AMOUNT_PATTERN.finditer(text))
    numeric_amounts = money_values_from_text(text)
    if not numeric_amounts:
        return None

    balance = numeric_amounts[-1]
    transaction_amount = numeric_amounts[-2] if len(numeric_amounts) >= 2 else numeric_amounts[0]
    transaction_type = detect_type(text)

    if previous_balance is not None:
        delta = round(balance - previous_balance, 2)
        if delta > 0:
            transaction_type = "Credit"
            transaction_amount = abs(delta)
        elif delta < 0:
            transaction_type = "Debit"
            transaction_amount = abs(delta)

    description = clean_description(text, date_match, amount_matches[0].start())

    debit = transaction_amount if transaction_type == "Debit" else None
    credit = transaction_amount if transaction_type == "Credit" else None

    confidence = row.get("confidence", 0.75)
    confidence = min(0.99, max(0.5, confidence))

    return Transaction(
        id=f"txn-{index:04d}",
        date=date_match.group("date"),
        description=description[:100],
        debit=debit,
        credit=credit,
        balance=balance,
        type=transaction_type,
        confidence=round(confidence, 3),
        raw_text=text[:200],
        page=row.get("page", 1),
    )


def parse_transactions(rows: List[dict]) -> List[dict]:
    """Parse multiple transaction rows."""
    transactions = []
    previous_balance = None

    for row in rows:
        try:
            text = re.sub(r"\s+", " ", row.get("text", "")).strip()
            lowered = text.lower()
            money_values = money_values_from_text(text)

            if "opening balance" in lowered and money_values:
                previous_balance = money_values[-1]
                continue

            transaction = parse_transaction_row(row, len(transactions) + 1, previous_balance)
            if transaction:
                item = transaction.to_dict()
                transactions.append(item)
                if item.get("balance") is not None:
                    previous_balance = item["balance"]
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return transactions
