import re
from typing import Dict, List, Optional

from app.models.transaction import Transaction

# ─── Date patterns ─────────────────────────────────────────────────────────────
DATE_PATTERNS = [
    # ISO: 2025-08-01
    r"(?<!\d)(?P<date>\d{4}[/-]\d{1,2}[/-]\d{1,2})(?!\d)",
    # US with 4-year: 08/01/2025, 08-01-2025
    r"(?<!\d)(?P<date>\d{1,2}[./\-]\d{1,2}[./\-]\d{4})(?!\d)",
    # US with 2-year: 08/01/25, 08-01-25
    r"(?<!\d)(?P<date>\d{1,2}[./\-]\d{1,2}[./\-]\d{2})(?!\d)",
    # US without year, including OCR-spaced separators: 8/01, 6 / 02
    r"(?<!\d)(?P<date>\d{1,2}\s*/\s*\d{1,2})(?!\s*/\s*\d)",
    # Navy Federal / BMO style: 07-01 (month-day, no year)
    r"(?<!\d)(?P<date>\d{1,2}-\d{1,2})(?!\d)",
    # TD Bank: Jul 01 2025
    r"(?P<date>\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
    # Month DD YYYY: August 01 2025
    r"(?P<date>(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
    # US Bank: "Aug 1" or "Aug\n1" (date split across tokens)
    r"(?P<date>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?)",
]

DATE_PATTERN_COMPILED = [re.compile(p, re.IGNORECASE) for p in DATE_PATTERNS]

# Require cents (two decimal digits) to avoid card IDs / phone numbers
AMOUNT_PATTERN = re.compile(
    r"(?:^|\s)"
    r"(?P<open_paren>\()?"
    r"(?P<currency>[^\d\s(+-])?"
    r"(?P<sign>-)?"
    r"(?P<amount>(?:(?:\d{1,3}(?:,\d{3})+|\d+)?\.\d{2}))"
    r"(?P<trail_sign>-)?"
    r"(?P<close_paren>\))?"
    r"(?:\s*(?:CR|DR|D|C))?"
    r"(?=\s|$)",
    re.IGNORECASE,
)

COLUMN_ALIASES = {
    "date": "date",
    "posting date": "date",
    "postingdate": "date",
    "post date": "date",
    "posted": "date",
    "postdate": "date",
    "posting": "date",
    "value date": "date",
    "eff date": "date",
    "effective date": "date",
    "transaction date": "date",
    "transactiondate": "date",
    "description": "description",
    "transaction description": "description",
    "transaction detail": "description",
    "transaction details": "description",
    "description of transaction": "description",
    "particulars": "description",
    "details": "description",
    "narration": "description",
    "ref": "reference",
    "ref no": "reference",
    "reference": "reference",
    "reference no": "reference",
    "instrument": "reference",
    "instrument no": "reference",
    "card": "reference",
    "card id": "reference",
    "check no": "reference",
    "check number": "reference",
    "cheque no": "reference",
    "withdrawal": "debit",
    "withdrawals": "debit",
    "withdraw": "debit",
    "debit": "debit",
    "debits": "debit",
    "debit amount": "debit",
    "payment": "debit",
    "payments": "debit",
    "deposit": "credit",
    "deposits": "credit",
    "credit": "credit",
    "credits": "credit",
    "credit amount": "credit",
    "amount": "amount",
    "new balance": "balance",
    "balance": "balance",
    "running balance": "balance",
    "ending balance": "balance",
}

HEADER_WORDS = {
    "date", "description", "particulars", "withdrawal", "deposit",
    "debit", "credit", "balance", "amount", "transaction", "reference",
    "posting", "posted",
}

NON_TRANSACTION_PHRASES = {
    "account number", "closing balance", "copyright", "opening balance",
    "page no", "sampletemplates", "statement date", "statement period",
    "templatelab", "total deposits", "total withdrawals", "total debits",
    "total credits", "beginning balance", "ending balance",
    "account summary", "account activity", "subtotal",
    "daily balance summary",
    "previous balance", "previous statement balance",
    "temporary statement", "formal statement of your account",
    "regularly scheduled statement",
}

# ─── Amount parser ──────────────────────────────────────────────────────────────

def parse_amount(value: str) -> Optional[float]:
    """Parse a money string into a float. Returns None if not parseable."""
    if not value:
        return None
    cleaned = re.sub(r"[^\d.\-,]", "", value).strip()
    if not cleaned or cleaned in {"-", ".", ","}:
        return None
    try:
        is_negative = cleaned.startswith("-") or cleaned.endswith("-")
        normalized = cleaned.strip("-")
        # Find last separator — if 2 digits follow it, treat it as decimal
        separators = [i for i, c in enumerate(normalized) if c in ".,"]
        if separators and len(normalized) - separators[-1] == 3:
            dec = separators[-1]
            whole = re.sub(r"[^\d]", "", normalized[:dec])
            cents = re.sub(r"[^\d]", "", normalized[dec + 1:])
            normalized = f"{whole}.{cents}"
        else:
            normalized = normalized.replace(",", "")
        amount = float(normalized)
        return -amount if is_negative else amount
    except ValueError:
        return None


def looks_like_header(text: str) -> bool:
    lowered = text.lower()
    if any(p in lowered for p in NON_TRANSACTION_PHRASES):
        # Allow "opening balance" rows that carry an amount (they set prev_balance)
        if "opening balance" in lowered or "beginning balance" in lowered:
            return False
        return True
    count = sum(1 for w in HEADER_WORDS if w in lowered)
    return count >= 2


def find_date(text: str) -> Optional[re.Match]:
    for pattern in DATE_PATTERN_COMPILED:
        m = pattern.search(text)
        if m:
            return m
    return None


def clean_date(value: str) -> str:
    return re.sub(r"\s*([/.-])\s*", r"\1", value.strip())


def detect_type(text: str) -> Optional[str]:
    lowered = text.lower()
    
    def has_keyword(words):
        for w in words:
            if re.search(r'\b' + re.escape(w) + r'\b', lowered):
                return True
        return False
        
    if has_keyword(["debit", "withdrawal", "paid", "payment", "transfer out", "transfer to", "pos debit", "atm withdrawal", "check", "fee", "purchase", "charge"]):
        return "Debit"
    if has_keyword(["credit", "deposit", "received", "transfer in", "transfer from", "refund", "return"]):
        return "Credit"
        
    # Match "CR" or "DR" only if they appear as isolated tokens
    if re.search(r'\bcr\b', lowered):
        return "Credit"
    if re.search(r'\bdr\b', lowered):
        return "Debit"
        
    return None


def clean_description(text: str, date_match: re.Match, first_amount_pos: int) -> str:
    preamble = text[:date_match.start()].strip()
    post_date = text[date_match.end():first_amount_pos].strip(" -|:/")
    desc = f"{preamble} {post_date}".strip()
    # Strip a second date (e.g. card statement with two dates)
    desc = re.sub(r"^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+", "", desc)
    # Strip short reference codes (3-6 digits)
    desc = re.sub(r"^\s*\d{3,6}\s+", "", desc)
    if len(desc) < 2:
        amount_matches = list(AMOUNT_PATTERN.finditer(text))
        if amount_matches:
            desc = text[amount_matches[-1].end():].strip(" -|:/")
    desc = desc.strip(" -|:/")
    return desc if len(desc) >= 2 else "Transaction"


def strip_leading_date(text: str) -> str:
    m = find_date(text)
    if m and m.start() == 0:
        return text[m.end():].strip(" -|:/")
    return text.strip(" -|:/")


def money_values_from_text(text: str) -> List[float]:
    values = []
    for m in AMOUNT_PATTERN.finditer(text):
        raw = m.group("amount")
        sign = m.group("sign") or m.group("trail_sign") or ""
        if m.group("open_paren") and m.group("close_paren"):
            sign = "-"
        amount = parse_amount(sign + raw)
        if amount is not None:
            values.append(amount)
    return values


def _compact_spaced_text(text: str) -> str:
    """
    Some PDFs expose text as one character per word: "6 / 0 2 D E P O S I T".
    Collapse that shape enough for date, amount, and section parsing.
    """
    if len(re.findall(r"\b\w\b", text)) < 6:
        return text
    compact = re.sub(r"(?<=\b[A-Za-z])\s+(?=[A-Za-z]\b)", "", text)
    compact = re.sub(r"(?<=\b\d)\s+(?=\d\b)", "", compact)
    compact = re.sub(r"\s*/\s*", "/", compact)
    compact = re.sub(r"\s*,\s*", ",", compact)
    compact = re.sub(r"\s*\.\s*", ".", compact)
    return re.sub(r"\s+", " ", compact).strip()


def _section_info(text: str) -> Optional[dict]:
    lowered = re.sub(r"\s+", " ", _compact_spaced_text(text).lower())
    if re.match(r"^\d+\s+(?:credits?|debits?)\b", lowered):
        return None
    if "balance" in lowered and any(w in lowered for w in ["debit", "withdrawal"]) and any(
        w in lowered for w in ["credit", "deposit"]
    ):
        return None
    if any(p in lowered for p in [
        "deposits and credits",
        "deposits and additions",
        "deposit credits",
        "electronic deposits",
        "deposits",
        "other credits",
        "credits",
    ]):
        return {"name": "Credits / Deposits", "type": "Credit"}
    if any(p in lowered for p in [
        "withdrawals / debits",
        "withdrawals and debits",
        "checks / debits",
        "checks paid",
        "debits",
        "electronic payments",
        "electronic withdrawals",
        "other withdrawals",
        "withdrawals",
        "atm & debit card withdrawals",
        "atm debit withdrawals",
        "fees",
    ]):
        return {"name": "Debits / Withdrawals", "type": "Debit"}
    return None


def _section_type(text: str) -> Optional[str]:
    info = _section_info(text)
    return info["type"] if info else None


def _account_section_name(text: str) -> Optional[str]:
    compact = re.sub(r"\s+", " ", _compact_spaced_text(text)).strip()
    match = re.search(
        r"([A-Za-z][A-Za-z '\-&]+(?:Checking|Savings|Money Market)[^)]*\(\d{2,}\)(?:\s*\(Continued\))?)",
        compact,
        re.IGNORECASE,
    )
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _is_noise_text(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return True
    if re.fullmatch(r"[\W_]{5,}", compact):
        return True
    if re.fullmatch(r"([A-Za-z])\1{3,}.*", compact):
        return True
    return False


# ─── Column-layout helpers ──────────────────────────────────────────────────────

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
    Supports:
      - Traditional debit/credit columns (Chase, PNC, BMO, Santander, Tab …)
      - Single amount column (Suncoast, Wells Fargo MTD …)
      - No-balance layouts (Navy Federal, Fifth Third — amounts only)
    """
    items = row.get("items") or []
    if not items:
        return None

    columns = []
    seen: set = set()
    for item in sorted(items, key=lambda v: v.get("x_min", 0)):
        label = _normalize_header_label(_item_text(item))
        if label and label not in seen:
            columns.append({
                "name": label,
                "x_min": float(item.get("x_min", 0)),
                "x_max": float(item.get("x_max", 0)),
                "center": _item_center(item),
            })
            seen.add(label)

    names = {c["name"] for c in columns}

    has_date = "date" in names
    has_balance = "balance" in names
    has_debit_credit = bool({"debit", "credit"} & names)
    has_amount = "amount" in names

    if not has_date or not (has_debit_credit or has_amount or has_balance):
        return None

    columns = sorted(columns, key=lambda c: c["center"])
    boundaries = []
    for i, col in enumerate(columns):
        left = -float("inf") if i == 0 else (columns[i - 1]["center"] + col["center"]) / 2
        right = float("inf") if i == len(columns) - 1 else (col["center"] + columns[i + 1]["center"]) / 2
        boundaries.append({**col, "left": left, "right": right})

    if has_amount and not has_debit_credit and not has_balance:
        layout = "amount_column_no_balance"
    elif has_amount and not has_debit_credit:
        layout = "amount_column"
    elif has_debit_credit and not has_balance:
        layout = "debit_credit_no_balance"
    else:
        layout = "debit_credit"

    return {"columns": boundaries, "layout": layout}


def _bucket_items(row: dict, context: dict) -> Dict[str, List[str]]:
    buckets = {c["name"]: [] for c in context.get("columns", [])}
    for item in sorted(row.get("items") or [], key=lambda v: v.get("x_min", 0)):
        text = _item_text(item)
        if not text:
            continue
        center = _item_center(item)
        for col in context.get("columns", []):
            if col["left"] <= center < col["right"]:
                buckets.setdefault(col["name"], []).append(text)
                break
    return buckets


def _bucket_text(buckets: Dict[str, List[str]], name: str) -> str:
    return " ".join(buckets.get(name, [])).strip()


def _amount_from_bucket(buckets: Dict[str, List[str]], name: str) -> Optional[float]:
    values = money_values_from_text(_bucket_text(buckets, name))
    return values[-1] if values else None


def _append_continuation(rows: List[dict], row: dict) -> bool:
    """Attach a description-only continuation line to the previous transaction."""
    if not rows or find_date(row.get("text", "")) or looks_like_header(row.get("text", "")):
        return False
    text = re.sub(r"\s+", " ", row.get("text", "")).strip()
    if not text:
        return True
    if _is_noise_text(text):
        return False
    if any(p in text.lower() for p in NON_TRANSACTION_PHRASES):
        return False
    if len(money_values_from_text(text)) >= 2:
        return False
    previous = rows[-1]
    if looks_like_header(previous.get("text", "")):
        return False
    if not find_date(previous.get("text", "")):
        return False
    previous["text"] = f"{previous.get('text', '')} {text}".strip()
    previous.setdefault("items", []).extend(row.get("items") or [])
    previous["confidence"] = min(previous.get("confidence", 0.75), row.get("confidence", 0.75))
    previous["y_max"] = max(previous.get("y_max", 0), row.get("y_max", 0))
    return True


def normalize_logical_rows(rows: List[dict]) -> List[dict]:
    logical_rows: List[dict] = []
    for row in rows:
        current = dict(row)
        if logical_rows:
            prev = logical_rows[-1]
            if not find_date(prev.get("text", "")) and not money_values_from_text(prev.get("text", "")):
                if (
                    find_date(current.get("text", ""))
                    and not looks_like_header(prev.get("text", ""))
                    and not _is_noise_text(prev.get("text", ""))
                ):
                    current["text"] = f"{prev.get('text', '')} {current.get('text', '')}".strip()
                    current.setdefault("items", []).extend(prev.get("items") or [])
                    logical_rows.pop()
                    
        if _append_continuation(logical_rows, current):
            continue
        logical_rows.append(current)
    return logical_rows


# ─── Amount-column (single signed amount) resolution ───────────────────────────

def _resolve_debit_credit_from_amount(
    amount: Optional[float],
    text: str,
    previous_balance: Optional[float],
    balance: Optional[float],
    forced_type: Optional[str] = None,
) -> tuple:
    if amount is None:
        return None, None, forced_type or "Debit"
    if amount < 0:
        return abs(amount), None, "Debit"
    if amount > 0:
        if previous_balance is not None and balance is not None:
            delta = round(balance - previous_balance, 2)
            if delta < 0:
                return abs(amount), None, "Debit"
            if delta > 0:
                return None, abs(amount), "Credit"
        if forced_type:
            t = forced_type
        else:
            t = detect_type(text) or "Debit"
        if t == "Debit":
            return abs(amount), None, "Debit"
        return None, abs(amount), "Credit"
    return None, None, forced_type or "Debit"


def _resolve_debit_credit_from_signed_amount(
    amount: Optional[float],
    text: str,
    forced_type: Optional[str] = None,
) -> tuple:
    if amount is None:
        return None, None, forced_type or "Debit"
    if amount < 0:
        return abs(amount), None, "Debit"
    if forced_type == "Debit":
        return abs(amount), None, "Debit"
    if forced_type == "Credit":
        return None, abs(amount), "Credit"
    explicit_type = detect_type(text) or "Debit"
    if explicit_type == "Credit":
        return None, abs(amount), "Credit"
    
    return abs(amount), None, "Debit"


# ─── Navy Federal / no-balance-column layout ────────────────────────────────────

def _parse_navy_federal_row(
    row: dict,
    index: int,
    previous_balance: Optional[float],
) -> Optional[Transaction]:
    """
    Navy Federal statements print date and description on the LEFT column and
    amount + balance on the RIGHT column (sometimes on a separate line).
    The PDF extractor gives us lines like:
        "07-01 Transfer From Shares   400.00   1,499.59"
    or two separate lines:
        "07-01 Transfer From Shares"
        "400.00   1,499.59"
    This parser handles both cases.
    """
    text = re.sub(r"\s+", " ", row.get("text", "")).strip()
    if not text or looks_like_header(text):
        return None

    date_match = find_date(text)
    values = money_values_from_text(text)

    if not values:
        return None

    balance: Optional[float] = None
    amount: Optional[float] = None

    if len(values) >= 2:
        # last value = running balance, second-to-last = transaction amount
        balance = values[-1]
        amount = abs(values[-2])
    elif len(values) == 1:
        if previous_balance is not None:
            balance = values[0]
            delta = round(balance - previous_balance, 2)
            amount = abs(delta)
        else:
            return None

    if amount is None or amount == 0:
        return None

    t_type = detect_type(text) or "Debit"
    if previous_balance is not None and balance is not None:
        delta = round(balance - previous_balance, 2)
        if delta != 0:
            t_type = "Credit" if delta > 0 else "Debit"
            amount = abs(delta)

    # Description: strip date prefix and amounts
    desc = text
    if date_match:
        desc = text[date_match.end():]
    # Remove trailing amounts
    for m in list(AMOUNT_PATTERN.finditer(desc)):
        desc = desc[:m.start()]
    desc = desc.strip(" -|:/")
    if not desc:
        desc = "Transaction"

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))
    return Transaction(
        id=f"txn-{index:04d}",
        date=date_match.group("date") if date_match else "",
        description=desc.strip(),
        debit=abs(amount) if t_type == "Debit" else None,
        credit=abs(amount) if t_type == "Credit" else None,
        balance=balance,
        type=t_type,
        confidence=round(confidence, 3),
        raw_text=text,
        page=row.get("page", 1),
    )


# ─── US Bank / "Aug 1" date style ───────────────────────────────────────────────

def _merge_usbank_date_tokens(rows: List[dict]) -> List[dict]:
    """
    US Bank PDFs render dates as two separate lines:
        "Aug"
        "1  Electronic Deposit ..."
    This merges the month token into the following description line.
    """
    MONTH_RE = re.compile(
        r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$", re.IGNORECASE
    )
    merged: List[dict] = []
    for row in rows:
        text = row.get("text", "").strip()
        if merged and MONTH_RE.match(merged[-1].get("text", "").strip()):
            prev = merged[-1]
            prev["text"] = f"{prev['text'].strip()} {text}"
            prev.setdefault("items", []).extend(row.get("items") or [])
            prev["y_max"] = max(prev.get("y_max", 0), row.get("y_max", 0))
        else:
            merged.append(dict(row))
    return merged


# ─── Column-aware row parser ────────────────────────────────────────────────────

def parse_transaction_row_by_columns(
    row: dict,
    context: dict,
    index: int,
    previous_balance: Optional[float] = None,
    forced_type: Optional[str] = None,
) -> Optional[Transaction]:
    text = re.sub(r"\s+", " ", _compact_spaced_text(row.get("text", ""))).strip()
    if not text:
        return None

    buckets = _bucket_items(row, context)
    date_text = _bucket_text(buckets, "date") or text
    date_match = find_date(date_text)
    if looks_like_header(text) and not any(
        x in text.lower() for x in ("opening balance", "beginning balance")
    ):
        return None

    layout = context.get("layout", "debit_credit")
    debit: Optional[float] = None
    credit: Optional[float] = None

    if layout == "amount_column_no_balance":
        raw_amount = _amount_from_bucket(buckets, "amount")
        if raw_amount is None:
            vals = money_values_from_text(text)
            raw_amount = vals[-1] if vals else None
        balance = None
        debit, credit, t_type = _resolve_debit_credit_from_signed_amount(
            raw_amount, text, forced_type
        )
    elif layout == "amount_column":
        raw_amount = _amount_from_bucket(buckets, "amount")
        balance = _amount_from_bucket(buckets, "balance")
        if balance is None:
            vals = money_values_from_text(text)
            balance = vals[-1] if vals else None
        debit, credit, t_type = _resolve_debit_credit_from_amount(
            raw_amount, text, previous_balance, balance, forced_type
        )
    else:
        debit = _amount_from_bucket(buckets, "debit")
        credit = _amount_from_bucket(buckets, "credit")
        balance = _amount_from_bucket(buckets, "balance")
        if balance is None and debit is None and credit is None:
            vals = money_values_from_text(text)
            balance = vals[-1] if vals else None

        if debit is None and credit is None:
            vals = money_values_from_text(text)
            if previous_balance is not None and balance is not None:
                delta = round(balance - previous_balance, 2)
                amount = abs(vals[-2]) if len(vals) >= 2 else abs(delta)
                if delta > 0:
                    credit = amount
                elif delta < 0:
                    debit = amount
            else:
                if len(vals) >= 2:
                    amount = abs(vals[-2])
                    t = forced_type or detect_type(text) or "Debit"
                    if t == "Credit":
                        credit = amount
                    else:
                        debit = amount
        else:
            # We found an amount in a bucket. But OCR columns can be tricky with right-aligned numbers.
            # Use the running balance as a source of truth if available.
            if previous_balance is not None and balance is not None:
                delta = round(balance - previous_balance, 2)
                extracted_amount = debit if debit is not None else credit
                # Only override if the extracted amount matches the delta magnitude
                if abs(abs(delta) - extracted_amount) < 0.05:
                    if delta < 0:
                        debit = extracted_amount
                        credit = None
                    elif delta > 0:
                        credit = extracted_amount
                        debit = None

        if forced_type and ((forced_type == "Debit" and debit is None) or (forced_type == "Credit" and credit is None)):
            amount = abs(debit if debit is not None else credit if credit is not None else 0)
            debit = amount if forced_type == "Debit" else None
            credit = amount if forced_type == "Credit" else None
        
        t_type = "Credit" if credit is not None and debit is None else "Debit"
        
        # Override bucket if there's a strong keyword match and no running balance to contradict it
        if (debit is None or credit is None) and (balance is None or previous_balance is None):
            keyword_type = detect_type(text)
            if keyword_type is not None and keyword_type != t_type:
                amount = abs(debit if debit is not None else credit if credit is not None else 0)
                debit = amount if keyword_type == "Debit" else None
                credit = amount if keyword_type == "Credit" else None
                t_type = keyword_type

    if debit is not None:
        debit = abs(debit)
    if credit is not None:
        credit = abs(credit)

    description_parts = buckets.get("description", []) + buckets.get("reference", [])
    description = strip_leading_date(" ".join(p for p in description_parts if p))
    if not description:
        first_amount = next(AMOUNT_PATTERN.finditer(text), None)
        if date_match:
            description = clean_description(
                text, date_match,
                first_amount.start() if first_amount else len(text)
            )

    if not date_match:
        return None
    if not description or "end of transactions" in description.lower():
        return None

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))
    return Transaction(
        id=f"txn-{index:04d}",
        date=clean_date(date_match.group("date")) if date_match else "",
        description=description.strip(),
        debit=debit,
        credit=credit,
        balance=balance,
        type=t_type,
        confidence=round(confidence, 3),
        raw_text=text,
        page=row.get("page", 1),
    )


# ─── Fallback row parser ─────────────────────────────────────────────────────────

def parse_transaction_row(
    row: dict,
    index: int,
    previous_balance: Optional[float] = None,
    forced_type: Optional[str] = None,
    has_running_balance: bool = True,
) -> Optional[Transaction]:
    """Generic fallback: works for most single-/multi-amount-column statements."""
    text = re.sub(r"\s+", " ", _compact_spaced_text(row.get("text", ""))).strip()
    if not text:
        return None

    date_match = find_date(text)
    if not date_match:
        return None
    if looks_like_header(text) and not any(
        x in text.lower() for x in ("opening balance", "beginning balance")
    ):
        return None

    amount_matches = list(AMOUNT_PATTERN.finditer(text))
    numeric_amounts = money_values_from_text(text)
    if not numeric_amounts:
        return None

    t_type = forced_type or detect_type(text) or "Debit"

    if not has_running_balance:
        transaction_amount = abs(numeric_amounts[0])
        balance = None
    else:
        balance = numeric_amounts[-1]

    if not has_running_balance:
        pass
    elif len(numeric_amounts) == 1:
        if previous_balance is not None:
            delta = round(balance - previous_balance, 2)
            transaction_amount = abs(delta)
            t_type = "Credit" if delta > 0 else "Debit"
        else:
            return None

    elif len(numeric_amounts) == 2:
        val1 = abs(numeric_amounts[0])
        val2 = numeric_amounts[1]
        
        # Check if val2 is actually the running balance
        if previous_balance is not None:
            if abs(previous_balance - val1 - val2) < 0.01:
                # val1 is a Debit, val2 is the Balance
                transaction_amount = val1
                balance = val2
                t_type = "Debit"
            elif abs(previous_balance + val1 - val2) < 0.01:
                # val1 is a Credit, val2 is the Balance
                transaction_amount = val1
                balance = val2
                t_type = "Credit"
            else:
                # Fallback: Assume Left is Debit, Right is Credit (or whatever forced_type is)
                transaction_amount = val1
                delta = round(balance - previous_balance, 2)
                if delta != 0:
                    t_type = "Credit" if delta > 0 else "Debit"
        else:
            transaction_amount = val1

    elif len(numeric_amounts) == 3:
        w, d = numeric_amounts[0], numeric_amounts[1]
        if w != 0 and d == 0:
            transaction_amount = abs(w)
            t_type = "Debit"
        elif d != 0 and w == 0:
            transaction_amount = abs(d)
            t_type = "Credit"
        else:
            transaction_amount = abs(numeric_amounts[-2])
            if previous_balance is not None:
                delta = round(balance - previous_balance, 2)
                t_type = "Credit" if delta > 0 else "Debit"
            else:
                transaction_amount = abs(numeric_amounts[-2])
    else:
        transaction_amount = abs(numeric_amounts[-2])
        if previous_balance is not None:
            delta = round(balance - previous_balance, 2)
            t_type = "Credit" if delta > 0 else "Debit"

    # Balance delta is the most reliable signal when available
    if has_running_balance and previous_balance is not None:
        delta = round(balance - previous_balance, 2)
        if delta > 0:
            t_type = "Credit"
        elif delta < 0:
            t_type = "Debit"

    description = clean_description(
        text, date_match,
        amount_matches[0].start() if amount_matches else len(text)
    )

    debit = transaction_amount if t_type == "Debit" else None
    credit = transaction_amount if t_type == "Credit" else None

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))
    return Transaction(
        id=f"txn-{index:04d}",
        date=clean_date(date_match.group("date")),
        description=description.strip(),
        debit=debit,
        credit=credit,
        balance=balance,
        type=t_type,
        confidence=round(confidence, 3),
        raw_text=text,
        page=row.get("page", 1),
    )


# ─── No-balance fallback (Fifth Third, some amount-only layouts) ─────────────────

def parse_transaction_row_no_balance(
    row: dict,
    index: int,
    forced_type: Optional[str] = None,
) -> Optional[Transaction]:
    """
    For statements that list amounts without a running balance (Fifth Third Deposits
    / Withdrawals sections, Wells Fargo MTD export where balance is absent).
    """
    text = re.sub(r"\s+", " ", _compact_spaced_text(row.get("text", ""))).strip()
    if not text or looks_like_header(text):
        return None

    date_match = find_date(text)
    values = money_values_from_text(text)
    if not date_match or not values:
        return None

    amount = abs(values[0])
    t_type = forced_type or detect_type(text) or "Debit"
    first_amount = next(AMOUNT_PATTERN.finditer(text), None)
    desc = clean_description(
        text,
        date_match,
        first_amount.start() if first_amount else len(text),
    )

    confidence = min(0.99, max(0.5, row.get("confidence", 0.75)))
    return Transaction(
        id=f"txn-{index:04d}",
        date=clean_date(date_match.group("date")),
        description=desc.strip(),
        debit=amount if t_type == "Debit" else None,
        credit=amount if t_type == "Credit" else None,
        balance=None,
        type=t_type,
        confidence=round(confidence, 3),
        raw_text=text,
        page=row.get("page", 1),
    )


# ─── Top-level parse ─────────────────────────────────────────────────────────────

def parse_transactions(rows: List[dict]) -> List[dict]:
    transactions: List[dict] = []
    previous_balance: Optional[float] = None
    table_context_by_page: Dict[int, dict] = {}
    section_type_by_page: Dict[int, Optional[str]] = {}
    section_name_by_page: Dict[int, str] = {}

    # Pre-process: merge US Bank "Aug\n1" date tokens
    rows = _merge_usbank_date_tokens(rows)

    for row in normalize_logical_rows(rows):
        try:
            text = re.sub(r"\s+", " ", row.get("text", "")).strip()
            if _is_noise_text(text):
                continue
            compact_text = _compact_spaced_text(text)
            lowered = compact_text.lower()
            money_values = money_values_from_text(compact_text)
            page = row.get("page", 1)

            account_section = _account_section_name(compact_text)
            if account_section:
                section_name_by_page[page] = account_section
                if not find_date(compact_text):
                    continue

            # Build/update column context from header rows
            header_context = build_table_context(row)
            if header_context:
                table_context_by_page[page] = header_context
                if header_context.get("layout") != "amount_column_no_balance":
                    section_type_by_page[page] = None
                    section_name_by_page.setdefault(page, "Transactions")
                continue

            section_info = _section_info(compact_text)
            if section_info and not find_date(compact_text):
                section_type_by_page[page] = section_info["type"]
                section_name_by_page[page] = section_info["name"]
                continue

            # Capture opening/beginning balance
            if any(x in lowered for x in ("opening balance", "beginning balance", "previous balance", "previous statement balance")) and money_values:
                if not find_date(compact_text):
                    previous_balance = money_values[-1]
                    continue
                # If it also has a date, update balance but allow it to be processed
                previous_balance = money_values[-1]

            date_like_count = len(re.findall(r"\d{1,2}\s*[/-]\s*\d{1,2}(?:\s*[/-]\s*\d{2,4})?", compact_text))
            if date_like_count >= 2 and (
                "denotes missing check numbers" in lowered
                or re.match(r"^\d{1,2}[/-]\d{1,2}\s+\d{3,6}\*?\s+", compact_text)
            ):
                continue
            transaction_words = (
                "deposit", "credit", "debit", "withdrawal", "payment", "transfer",
                "check", "fee", "purchase", "ach", "wire", "pos", "atm",
            )
            if date_like_count >= 2 and not any(word in lowered for word in transaction_words):
                continue

            transaction = None
            context = table_context_by_page.get(page)
            forced_type = section_type_by_page.get(page)
            section_name = section_name_by_page.get(page) or (
                "Credits / Deposits" if forced_type == "Credit"
                else "Debits / Withdrawals" if forced_type == "Debit"
                else "Transactions"
            )

            if context:
                transaction = parse_transaction_row_by_columns(
                    row, context, len(transactions) + 1, previous_balance, forced_type
                )

            if forced_type and not transaction and find_date(compact_text) and money_values:
                transaction = parse_transaction_row_no_balance(
                    row, len(transactions) + 1, forced_type
                )

            if not transaction:
                transaction = parse_transaction_row(
                    row,
                    len(transactions) + 1,
                    previous_balance,
                    forced_type,
                    has_running_balance=not forced_type,
                )

            # Last resort: no-balance parse (Fifth Third debit/credit section lines)
            if not transaction and find_date(compact_text) and money_values:
                transaction_candidate = parse_transaction_row_no_balance(
                    row, len(transactions) + 1, forced_type
                )
                # Only use if the amount looks reasonable (not a page/account number)
                if transaction_candidate and (transaction_candidate.debit or transaction_candidate.credit):
                    transaction = transaction_candidate

            if transaction:
                item = transaction.to_dict()
                is_opening = any(x in str(item.get("description", "")).lower() for x in ("opening balance", "beginning balance", "previous balance"))
                if item.get("debit") is None and item.get("credit") is None and not is_opening:
                    continue
                item["section"] = section_name
                transactions.append(item)
                if item.get("balance") is not None:
                    previous_balance = item["balance"]

        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return transactions
