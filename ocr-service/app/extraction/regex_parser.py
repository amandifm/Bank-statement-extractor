import re
from typing import List, Optional

from app.models.transaction import Transaction

DATE_PATTERN = re.compile(
    r"(?P<date>\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b)"
)
AMOUNT_PATTERN = re.compile(r"(?<!\w)(?:[$₹€£]?\s*)?[-+]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:CR|DR))?(?!\w)", re.I)
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
}


def parse_amount(value: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.\-]", "", value)
    if not cleaned or cleaned in {"-", "."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def looks_like_header(text: str) -> bool:
    lowered = text.lower()
    return sum(1 for word in HEADER_WORDS if word in lowered) >= 2


def detect_type(text: str, amount_tokens: List[str]) -> str:
    lowered = text.lower()
    tail = " ".join(amount_tokens[-2:]).lower()
    if "cr" in tail or "credit" in lowered or "deposit" in lowered:
        return "Credit"
    if "dr" in tail or "debit" in lowered or "withdrawal" in lowered:
        return "Debit"
    return "Debit"


def parse_transaction_row(row: dict, index: int) -> Optional[Transaction]:
    text = re.sub(r"\s+", " ", row["text"]).strip()
    if not text or looks_like_header(text):
        return None

    date_match = DATE_PATTERN.search(text)
    if not date_match:
        return None

    amount_matches = list(AMOUNT_PATTERN.finditer(text))
    amount_tokens = [match.group(0).strip() for match in amount_matches]
    numeric_amounts = [parse_amount(token) for token in amount_tokens]
    numeric_amounts = [amount for amount in numeric_amounts if amount is not None]

    if not numeric_amounts:
        return None

    date = date_match.group("date")
    balance = numeric_amounts[-1] if len(numeric_amounts) >= 2 else None
    transaction_amount = numeric_amounts[-2] if len(numeric_amounts) >= 2 else numeric_amounts[0]
    transaction_type = detect_type(text, amount_tokens)

    debit = transaction_amount if transaction_type == "Debit" else None
    credit = transaction_amount if transaction_type == "Credit" else None

    description_start = date_match.end()
    description_end = amount_matches[0].start() if amount_matches else len(text)
    description = text[description_start:description_end].strip(" -|:")
    if not description:
        description = text[date_match.end():].strip()

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))
    if len(numeric_amounts) >= 2:
        confidence += 0.01

    return Transaction(
        id=f"txn-{index:04d}",
        date=date,
        description=description,
        debit=debit,
        credit=credit,
        balance=balance,
        type=transaction_type,
        confidence=min(confidence, 0.99),
        raw_text=text,
        page=row.get("page", 1),
    )


def parse_transactions(rows: List[dict]) -> List[dict]:
    transactions = []
    for row in rows:
        transaction = parse_transaction_row(row, len(transactions) + 1)
        if transaction:
            transactions.append(transaction.to_dict())
    return transactions
