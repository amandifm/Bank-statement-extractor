import re
from typing import Any, Dict, List, Optional


Rule = Dict[str, Any]


DEDUCTION_RULES: List[Rule] = [
    {
        "category": "Financing & Loans",
        "reason": "Loan, advance, lender, financing, lease, or overdraft deposit",
        "patterns": [
            r"\badvance(?:s)?\b",
            r"\b(?:loc|olb|occ)\b",
            r"\bline\s+of\s+credit\b",
            r"\boverdraft\b|\bod\b",
            r"\bprovisional\s+credit\b|\btemporary\s+credit\b",
            r"\b(?:loan|lending|lender|funding|finance|financing|capital|lease|leasing)\b",
            r"\bnextgear\b|\bcashflow\b|\basset\s+lease\b|\bequipment\s+finance\b",
        ],
    },
    {
        "category": "Internal Transfers & Linked Accounts",
        "reason": "Internal, account-to-account, online, mobile, payroll, or owner/business transfer",
        "patterns": [
            r"\ba2a\b|\baccount[-\s]*to[-\s]*account\b",
            r"\bcash\s+mgm?nt\b|\bcash\s+management\b",
            r"\bcol\s+xfer\b",
            r"\bdeposit\s+transfer\b.*\b(?:x{2,}|\*{2,})\d{2,4}\b",
            r"\bpayroll\s+(?:account|transfer|xfer)\b",
            r"\bfunds?\s+transfers?\b|\btransfers?\b|\bxfr\b|\bxfer\b",
            r"\bmobile\s+banking\s+transfer\b|\bonline\s+(?:banking\s+)?(?:transfer|xfer)\b",
            r"\bonline\s+transfers?\s+from\s+(?:checking|chk|savings?|mma|payroll)\b",
            r"\bpc\s+transfers?\b",
            r"\btele(?:phone)?\s+transfers?\b",
            r"\bacorns\b",
            r"\bauthorized\s+from\b",
        ],
    },
    {
        "category": "Banking Corrections, Reversals & Perks",
        "reason": "Correction, reversal, return, refund, reward, interest, fee reversal, or verification deposit",
        "patterns": [
            r"\bcredit\s+adjust(?:ment)?\b|\badjustment\b.*\bcredit\b",
            r"\bwithdrawal\s+adjustment\b|\bdebit\s+card\s+credit\s+voucher\b",
            r"\bdeposit\s+correction\b|\bshare\s+draft\s+correction\b",
            r"\berror\s+deposit\b|\bmisposted\b",
            r"\bnsf\b|\bnon[-\s]*sufficient\s+funds\b",
            r"\breturns?\b|\brtn\b|\bret\b",
            r"\bcash\s*back\b|\brewards?\b|\brebates?\b|\brbt\b",
            r"\bdividends?\b|\binterest\b",
            r"\brefunds?\b",
            r"\btreas(?:ury)?\b",
            r"\bvouchers?\b|\bfees?\b.*\b(?:reversal|credit|refund)\b",
            r"\btrial\s+deposits?\b|\bverify\s+deposits?\b|\bverification\s+deposits?\b",
        ],
    },
]

WIRE_DEDUCTION_PATTERNS = [
    r"\bmerchant\b",
    r"\b(?:loc|line\s+of\s+credit)\b",
    r"\b(?:loan|lending|lender|funding|finance|financing|capital|lease|leasing)\b",
    r"\bnextgear\b|\bcashflow\b|\basset\s+lease\b|\bequipment\s+finance\b",
]


def _amount(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _match_rule(description: str) -> Optional[Dict[str, str]]:
    text = description.lower()

    if re.search(r"\bwire\b", text):
        for pattern in WIRE_DEDUCTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "category": "Special Conditional Rule: Wire Deposits",
                    "reason": "Wire deposit matched merchant, lender, financing, or LOC language",
                    "matched_pattern": pattern,
                }
        return None

    for rule in DEDUCTION_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "category": rule["category"],
                    "reason": rule["reason"],
                    "matched_pattern": pattern,
                }

    return None


def classify_transactions(transactions: List[dict]) -> Dict[str, Any]:
    """Tag credits as Revenue or Deduction and build an audit-ready breakdown."""
    raw_credit_total = 0.0
    adjusted_revenue_total = 0.0
    revenue_deduction_total = 0.0
    debit_total = 0.0
    credits_breakdown = []
    debits_breakdown = []

    for item in transactions:
        description = str(item.get("description") or item.get("raw_text") or "").strip()
        credit = _amount(item.get("credit"))
        debit = _amount(item.get("debit"))

        if credit > 0:
            raw_credit_total = round(raw_credit_total + credit, 2)
            match = _match_rule(description)
            if match:
                status = "Deduction"
                revenue_deduction_total = round(revenue_deduction_total + credit, 2)
                item["is_revenue"] = False
                item["revenue_status"] = status
                item["revenue_exclusion_category"] = match["category"]
                item["revenue_exclusion_reason"] = match["reason"]
                item["revenue_matched_pattern"] = match["matched_pattern"]
            else:
                status = "Revenue"
                adjusted_revenue_total = round(adjusted_revenue_total + credit, 2)
                item["is_revenue"] = True
                item["revenue_status"] = status
                item["revenue_exclusion_category"] = None
                item["revenue_exclusion_reason"] = None
                item["revenue_matched_pattern"] = None

            credits_breakdown.append(
                {
                    "id": item.get("id"),
                    "date": item.get("date"),
                    "description": description,
                    "amount": credit,
                    "status": status,
                    "category": item.get("revenue_exclusion_category"),
                    "reason": item.get("revenue_exclusion_reason"),
                }
            )

        if debit > 0:
            debit_total = round(debit_total + debit, 2)
            item["is_revenue"] = False
            item["revenue_status"] = None
            debits_breakdown.append(
                {
                    "id": item.get("id"),
                    "date": item.get("date"),
                    "description": description,
                    "amount": debit,
                }
            )

    return {
        "snapshot": {
            "raw_credit_total": raw_credit_total,
            "adjusted_revenue_total": adjusted_revenue_total,
            "revenue_deduction_total": revenue_deduction_total,
            "variance": round(raw_credit_total - adjusted_revenue_total, 2),
            "debit_total": debit_total,
            "credit_count": len(credits_breakdown),
            "accepted_revenue_count": sum(1 for item in credits_breakdown if item["status"] == "Revenue"),
            "deduction_count": sum(1 for item in credits_breakdown if item["status"] == "Deduction"),
            "debit_count": len(debits_breakdown),
        },
        "credits_breakdown": credits_breakdown,
        "debits_breakdown": debits_breakdown,
    }
