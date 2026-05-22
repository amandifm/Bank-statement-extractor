import re
from typing import Dict, List, Optional

from app.models.transaction import Transaction

DATE_PATTERNS = [
    r"(?<!\d)(?P<date>\d{4}[/-]\d{1,2}[/-]\d{1,2})(?!\d)",
    r"(?<!\d)(?P<date>\d{1,2}[./:-]\d{1,2}[./:-]\d{2,4})(?!\d)",
    r"(?<!\d)(?P<date>\d{4}[./:-]\d{2,4})(?!\d)",
    r"(?<!\d)(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})(?!\d)",
    r"(?<!\d)(?P<date>\d{1,2}[/-]\d{1,2})(?![/-]\d|\d)",
    r"(?P<date>mm/dd/yyyy)",
    r"(?<!\d)(?P<date>\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})(?!\d)",
    r"(?<!\d)(?P<date>\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4})(?!\d)",
]

DATE_PATTERN_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in DATE_PATTERNS]

# Require cents so dates/card ids such as 06 or 1111 are never parsed as money.
AMOUNT_PATTERN = re.compile(
    r"(?:^|\s)"
    r"(?P<currency>[$])?"
    r"(?P<amount>-?(?:\d{1,3}(?:,\d{3})+|\d+)[.,:]\\d{2}|-?\d{1,3}(?:,\d{3})*\.\d{2}|-?\d+\.\d{2})"
    r"(?:\s*(?:CR|DR|D|C))?"
    r"(?=\s|$)",
    re.IGNORECASE,
)

COLUMN_ALIASES = {
    "date": "date",
    "value date": "value_date",      # Yes Bank has separate Value Date column
    "post date": "date",             # Suncoast "Post Date"
    "eff date": "value_date",        # Suncoast "Eff Date"
    "description": "description",
    "particulars": "description",
    "details": "description",
    "narration": "description",
    "transaction description": "description",   # Suncoast
    "transaction details": "description",
    "ref": "reference",
    "reference": "reference",
    "instrument": "reference",
    "instrument no": "reference",
    "card": "reference",             # CreditWize card ID column
    "card id": "reference",
    "withdrawal": "debit",
    "withdrawals": "debit",
    "withdraw": "debit",
    "debit": "debit",
    "debits": "debit",
    "deposit": "credit",
    "deposits": "credit",
    "credit": "credit",
    "credits": "credit",
    # Suncoast / single-amount-column statements
    "amount": "amount",
    "new balance": "balance",
    "balance": "balance",
}

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
    "reference",
}

NON_TRANSACTION_PHRASES = {
    "account number",
    "closing balance",
    "copyright",
    "opening balance",
    "page no",
    "sampletemplates",
    "statement date",
    "statement period",
    "templatelab",
    "total deposits",
    "total withdrawals",
}


def parse_amount(value: str) -> Optional[float]:
    """Parse a money amount from OCR text."""
    if not value:
        return None

    cleaned = re.sub(r"[^\d.\-,:]", "", value).strip()
    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    try:
        is_negative = cleaned.startswith("-") or cleaned.endswith("-")
        normalized = cleaned.strip("-")
        separators = [index for index, char in enumerate(normalized) if char in ".,:"]
        if separators and len(normalized) - separators[-1] == 3:
            decimal_index = separators[-1]
            whole = re.sub(r"[^\d]", "", normalized[:decimal_index])
            cents = re.sub(r"[^\d]", "", normalized[decimal_index + 1:])
            normalized = f"{whole}.{cents}"
        else:
            normalized = normalized.replace(",", "")
        amount = float(normalized)
        return -amount if is_negative else amount
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

    if any(word in lowered for word in ["cr", "credit", "deposit", "received", "transfer in", "+"]):
        return "Credit"

    if any(word in lowered for word in ["dr", "debit", "withdrawal", "paid", "transfer out", "-"]):
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


def strip_leading_date(text: str) -> str:
    """Remove a date prefix that OCR glued into the description cell."""
    match = find_date(text)
    if match and match.start() == 0:
        return text[match.end():].strip(" -|:/")
    return text.strip(" -|:/")


def money_values_from_text(text: str) -> List[float]:
    """Extract money values in row order."""
    values = []
    for match in AMOUNT_PATTERN.finditer(text):
        amount = parse_amount(match.group("amount"))
        if amount is not None:
            values.append(amount)
    return values


def _item_text(item: dict) -> str:
    return re.sub(r"\s+", " ", item.get("text", "")).strip()


def _item_center(item: dict) -> float:
    return (float(item.get("x_min", 0)) + float(item.get("x_max", 0))) / 2


def _normalize_header_label(text: str) -> Optional[str]:
    cleaned = re.sub(r"[^a-z\s]", " ", text.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned in COLUMN_ALIASES:
        return COLUMN_ALIASES[cleaned]

    for phrase, canonical in COLUMN_ALIASES.items():
        if phrase in cleaned:
            return canonical
    return None


def build_table_context(row: dict) -> Optional[dict]:
    """
    Infer table columns from a visual header row.

    Extended to support single-amount-column layouts (Suncoast: Amount +
    New Balance) in addition to the traditional debit/credit layout.
    """
    items = row.get("items") or []
    if not items:
        return None

    columns = []
    seen = set()
    for item in sorted(items, key=lambda value: value.get("x_min", 0)):
        label = _normalize_header_label(_item_text(item))
        if label and label not in seen:
            columns.append(
                {
                    "name": label,
                    "x_min": float(item.get("x_min", 0)),
                    "x_max": float(item.get("x_max", 0)),
                    "center": _item_center(item),
                }
            )
            seen.add(label)

    names = {column["name"] for column in columns}

    # Require at minimum: a date column, a balance column, and either
    # debit/credit columns OR a single "amount" column.
    has_date = "date" in names
    has_balance = "balance" in names
    has_debit_credit = bool({"debit", "credit"} & names)
    has_amount = "amount" in names

    if not has_date or not has_balance or not (has_debit_credit or has_amount):
        return None

    columns = sorted(columns, key=lambda column: column["center"])
    boundaries = []
    for index, column in enumerate(columns):
        left = -float("inf") if index == 0 else (columns[index - 1]["center"] + column["center"]) / 2
        right = float("inf") if index == len(columns) - 1 else (column["center"] + columns[index + 1]["center"]) / 2
        boundaries.append({**column, "left": left, "right": right})

    # Tag whether this is a single-amount-column layout
    layout = "amount_column" if (has_amount and not has_debit_credit) else "debit_credit"
    return {"columns": boundaries, "layout": layout}


def _bucket_items(row: dict, context: dict) -> Dict[str, List[str]]:
    buckets = {column["name"]: [] for column in context.get("columns", [])}
    for item in sorted(row.get("items") or [], key=lambda value: value.get("x_min", 0)):
        text = _item_text(item)
        if not text:
            continue
        center = _item_center(item)
        for column in context.get("columns", []):
            if column["left"] <= center < column["right"]:
                buckets.setdefault(column["name"], []).append(text)
                break
    return buckets


def _bucket_text(buckets: Dict[str, List[str]], name: str) -> str:
    return " ".join(buckets.get(name, [])).strip()


def _amount_from_bucket(buckets: Dict[str, List[str]], name: str) -> Optional[float]:
    values = money_values_from_text(_bucket_text(buckets, name))
    return values[-1] if values else None


def _append_continuation(rows: List[dict], row: dict) -> bool:
    if not rows or find_date(row.get("text", "")) or looks_like_header(row.get("text", "")):
        return False

    text = re.sub(r"\s+", " ", row.get("text", "")).strip()
    if not text:
        return True
    if any(phrase in text.lower() for phrase in NON_TRANSACTION_PHRASES):
        return False
    if len(money_values_from_text(text)) >= 2:
        return False

    previous = rows[-1]
    if not find_date(previous.get("text", "")):
        return False

    previous["text"] = f"{previous.get('text', '')} {text}".strip()
    previous.setdefault("items", []).extend(row.get("items") or [])
    previous["confidence"] = min(previous.get("confidence", 0.75), row.get("confidence", 0.75))
    previous["y_max"] = max(previous.get("y_max", row.get("y_max", 0)), row.get("y_max", 0))
    return True


def normalize_logical_rows(rows: List[dict]) -> List[dict]:
    """Attach OCR continuation lines to the transaction row above them."""
    logical_rows = []
    for row in rows:
        if _append_continuation(logical_rows, dict(row)):
            continue
        logical_rows.append(dict(row))
    return logical_rows


def _resolve_debit_credit_from_amount(
    amount: Optional[float],
    text: str,
    previous_balance: Optional[float],
    balance: Optional[float],
) -> tuple[Optional[float], Optional[float], str]:
    """
    Resolve a single-amount-column value into (debit, credit, type).

    Suncoast stores withdrawals as negative amounts in the Amount column.
    Strategy (in priority order):
      1. Negative amount → Debit
      2. Balance delta vs previous balance → determines direction
      3. Keyword in description → determines direction
      4. Default → Credit (deposits are more common as positive)
    """
    if amount is None:
        return None, None, "Debit"

    # 1. Signed amount
    if amount < 0:
        return abs(amount), None, "Debit"
    if amount > 0:
        # 2. Balance delta
        if previous_balance is not None and balance is not None:
            delta = round(balance - previous_balance, 2)
            if delta < 0:
                return abs(amount), None, "Debit"
            if delta > 0:
                return None, abs(amount), "Credit"
        # 3. Keywords
        t = detect_type(text)
        if t == "Debit":
            return abs(amount), None, "Debit"
        return None, abs(amount), "Credit"

    return None, None, "Debit"


def parse_transaction_row_by_columns(
    row: dict,
    context: dict,
    index: int,
    previous_balance: Optional[float] = None,
) -> Optional[Transaction]:
    """Parse a transaction row using table column positions."""
    text = re.sub(r"\s+", " ", row.get("text", "")).strip()
    if not text:
        return None

    buckets = _bucket_items(row, context)
    date_text = _bucket_text(buckets, "date") or text
    date_match = find_date(date_text)
    if looks_like_header(text) and "opening balance" not in text.lower():
        return None

    layout = context.get("layout", "debit_credit")
    debit: Optional[float] = None
    credit: Optional[float] = None

    if layout == "amount_column":
        # Single signed-amount column (e.g. Suncoast)
        raw_amount = _amount_from_bucket(buckets, "amount")
        balance = _amount_from_bucket(buckets, "balance")
        if balance is None:
            values = money_values_from_text(text)
            balance = values[-1] if values else None
        debit, credit, transaction_type = _resolve_debit_credit_from_amount(
            raw_amount, text, previous_balance, balance
        )
    else:
        # Traditional debit / credit columns
        debit = _amount_from_bucket(buckets, "debit")
        credit = _amount_from_bucket(buckets, "credit")
        balance = _amount_from_bucket(buckets, "balance")

        if balance is None:
            values = money_values_from_text(text)
            balance = values[-1] if values else None

        if debit is None and credit is None:
            if previous_balance is not None and balance is not None:
                delta = round(balance - previous_balance, 2)
                if delta > 0:
                    credit = abs(delta)
                elif delta < 0:
                    debit = abs(delta)
            else:
                values = money_values_from_text(text)
                if len(values) >= 2:
                    debit = abs(values[-2])

        transaction_type = "Credit" if credit is not None and debit is None else "Debit"

    # Fix: debit/credit must always be stored as positive values
    if debit is not None:
        debit = abs(debit)
    if credit is not None:
        credit = abs(credit)

    description_parts = buckets.get("description", []) + buckets.get("reference", [])
    description = strip_leading_date(" ".join(part for part in description_parts if part))
    if not description:
        first_amount = next(AMOUNT_PATTERN.finditer(text), None)
        if date_match:
            description = clean_description(
                text, date_match, first_amount.start() if first_amount else len(text)
            )

    if not description or "end of transactions" in description.lower():
        return None
    if not date_match and balance is None:
        return None

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))

    return Transaction(
        id=f"txn-{index:04d}",
        date=date_match.group("date") if date_match else "",
        description=description[:100],
        debit=debit,
        credit=credit,
        balance=balance,
        type=transaction_type,
        confidence=round(confidence, 3),
        raw_text=text[:200],
        page=row.get("page", 1),
    )


def parse_transaction_row(
    row: dict,
    index: int,
    previous_balance: Optional[float] = None,
) -> Optional[Transaction]:
    """
    Parse a single transaction row from OCR output (fallback / no-context path).

    Handles the Yes Bank / Bank of Baroda pattern where a row contains three
    money values: Withdrawals, Deposits, Balance.  In that layout the second-
    to-last value may be 0.00 (the empty column), so we cannot blindly use
    values[-2] as the transaction amount.

    Fix: when there are exactly 3 money values (w, d, bal) and one of the first
    two is zero, pick the non-zero one as the transaction amount.
    """
    text = re.sub(r"\s+", " ", row["text"]).strip()

    if not text:
        return None

    date_match = find_date(text)
    if not date_match:
        return None
    if looks_like_header(text) and "opening balance" not in text.lower():
        return None

    amount_matches = list(AMOUNT_PATTERN.finditer(text))
    numeric_amounts = money_values_from_text(text)
    if not numeric_amounts:
        return None

    balance = numeric_amounts[-1]
    transaction_type = detect_type(text)

    # --- Resolve transaction amount ----------------------------------------
    if len(numeric_amounts) == 1:
        # Only a balance; derive amount from previous balance
        if previous_balance is not None:
            delta = round(balance - previous_balance, 2)
            transaction_amount = abs(delta)
            transaction_type = "Credit" if delta > 0 else "Debit"
        else:
            return None  # not enough information

    elif len(numeric_amounts) == 2:
        # Standard two-value row: amount + balance
        transaction_amount = abs(numeric_amounts[-2])
        if previous_balance is not None:
            delta = round(balance - previous_balance, 2)
            transaction_type = "Credit" if delta > 0 else "Debit"
            transaction_amount = abs(delta)

    elif len(numeric_amounts) == 3:
        # Three-value row: Withdrawals | Deposits | Balance  (Yes Bank, BoB)
        # One of the first two will be 0.00 — use the non-zero one.
        w, d = numeric_amounts[0], numeric_amounts[1]
        if w != 0 and d == 0:
            transaction_amount = abs(w)
            transaction_type = "Debit"
        elif d != 0 and w == 0:
            transaction_amount = abs(d)
            transaction_type = "Credit"
        else:
            # Both non-zero (rare) — fall back to balance delta
            if previous_balance is not None:
                delta = round(balance - previous_balance, 2)
                transaction_amount = abs(delta)
                transaction_type = "Credit" if delta > 0 else "Debit"
            else:
                transaction_amount = abs(numeric_amounts[-2])
    else:
        # 4+ values: single signed amount + balance is common (Suncoast fallback)
        if previous_balance is not None:
            delta = round(balance - previous_balance, 2)
            transaction_amount = abs(delta)
            transaction_type = "Credit" if delta > 0 else "Debit"
        else:
            transaction_amount = abs(numeric_amounts[-2])

    # Override type via balance delta when available (most reliable signal)
    if previous_balance is not None:
        delta = round(balance - previous_balance, 2)
        if delta > 0:
            transaction_type = "Credit"
            transaction_amount = abs(delta)
        elif delta < 0:
            transaction_type = "Debit"
            transaction_amount = abs(delta)

    description = clean_description(
        text, date_match, amount_matches[0].start() if amount_matches else len(text)
    )

    debit = transaction_amount if transaction_type == "Debit" else None
    credit = transaction_amount if transaction_type == "Credit" else None

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))

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
    table_context_by_page: Dict[int, dict] = {}

    for row in normalize_logical_rows(rows):
        try:
            text = re.sub(r"\s+", " ", row.get("text", "")).strip()
            lowered = text.lower()
            money_values = money_values_from_text(text)
            page = row.get("page", 1)

            header_context = build_table_context(row)
            if header_context:
                table_context_by_page[page] = header_context
                continue

            if "opening balance" in lowered and money_values and not find_date(text):
                previous_balance = money_values[-1]
                continue

            transaction = None
            context = table_context_by_page.get(page)
            if context:
                transaction = parse_transaction_row_by_columns(
                    row,
                    context,
                    len(transactions) + 1,
                    previous_balance,
                )

            if not transaction:
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
