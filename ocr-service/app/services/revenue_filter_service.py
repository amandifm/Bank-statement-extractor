"""
revenue_filter_service.py
=========================
Classifies every transaction credit as **Revenue** or **Deduction** following
the Master Keyword rules from the underwriting guidelines.

Architecture
------------
DEDUCTION_RULES        – three broad category buckets:
                           1. Financing & Loans
                           2. Internal Transfers & Linked Accounts
                           3. Banking Corrections, Reversals & Perks

WIRE_DEDUCTION_PATTERNS – applied ONLY when description contains "wire".
                          Standard business wires are KEPT as revenue.
                          Wires whose sender matches a merchant name,
                          merchant surname, lender, or LOC keyword are DEDUCTED.

classify_transactions() – public entry-point; accepts the flat transaction
                          list from the parser PLUS optional document metadata
                          (account_holder / business_name) to catch owner-name
                          and business-name self-transfers.

False-positive guards
---------------------
Two patterns require extra context to avoid misfiring:

  "interest"  – \binterest\b fires on company names like
                "FIRST INTEREST FINANCIAL GROUP". Guard: only deduct when
                the line also contains a banking-context word (earned, paid,
                accrued, dividend, rate, APY, APR, credited, posted, income).

  "rewards"   – \brewards?\b fires on merchant loyalty descriptions like
                "STAPLES REWARDS DEPOSIT". Guard: only deduct when the line
                ALSO contains a bank-perk indicator (cashback, rebate, RBT,
                point, bonus, bank, credit union) OR the rewards word is
                NOT followed by a merchant-like context.

Owner/Business-Name Matching Rules
-----------------------------------
- Wire deposits: sender matches account holder/business → deduction.
- Non-wire deposits: only flag when BOTH (a) owner/business name present
  AND (b) a transfer-indicator keyword is also present.
  Prevents false positives on merchant card settlement lines.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Rule = Dict[str, Any]


# ---------------------------------------------------------------------------
# TRANSFER INDICATOR PATTERNS
# Co-presence guard for owner/business-name checks on non-wire credits.
# ---------------------------------------------------------------------------
_TRANSFER_INDICATOR = re.compile(
    r"\b(?:transfer|xfer|xfr|authorized\s+from|from\s+acct|from\s+account|"
    r"mobile\s+transfer|online\s+transfer|internet\s+transfer|"
    r"a2a|account[-\s]*to[-\s]*account|col\s+xfer|"
    r"payroll\s+(?:transfer|deposit)|pc\s+transfer|tele(?:phone)?\s+transfer)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# FALSE-POSITIVE GUARD: "interest"
# Only deduce when the line carries a banking-context word alongside it.
# Company names like "FIRST INTEREST FINANCIAL GROUP" will NOT match.
# ---------------------------------------------------------------------------
_INTEREST_BANKING_CONTEXT = re.compile(
    r"\b(?:earned|paid|accrued|dividend|rate|apy|apr|credited|posted|"
    r"income|bearing|bearing|savings|checking|deposit|compounded|yield)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# FALSE-POSITIVE GUARD: "rewards" / "rebate"
# Merchant loyalty programs (STAPLES REWARDS DEPOSIT) should NOT be deducted.
# Only deduct when a bank-perk indicator is also present.
# ---------------------------------------------------------------------------
_REWARDS_BANK_CONTEXT = re.compile(
    r"\b(?:cashback|cash\s*back|rebate|rbt|point|bonus|bank|credit\s+union|"
    r"debit\s+card|visa|mastercard|amex|perk|statement\s+credit)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# DEDUCTION RULES
# ---------------------------------------------------------------------------
DEDUCTION_RULES: List[Rule] = [
    # -----------------------------------------------------------------------
    # 1. FINANCING & LOANS
    # -----------------------------------------------------------------------
    {
        "category": "Financing & Loans",
        "reason": (
            "Loan, advance, lender, financing, lease, overdraft, or "
            "provisional/temporary credit deposit"
        ),
        "patterns": [
            # Advances — Retro Advance, MCA Advance, Cash Advance, merchant advance, etc.
            r"\badvance(?:s|d)?\b",
            # LOC / OLB / OCC loan codes (standalone tokens only)
            r"\bloc\b",
            r"\bolb\b",
            r"\bocc\b",
            # Explicit line-of-credit phrase
            r"\bline\s+of\s+credit\b",
            # Overdraft / OD deposits
            r"\boverdraft\b",
            r"\bod\s+(?:credit|deposit|funding)\b",
            # Provisional / temporary credits
            r"\bprovisional\s+credit\b",
            r"\btemporary\s+credit\b",
            # Generic loan / lending / lender / funding / finance / capital /
            # lease / leasing / personal loan
            r"\b(?:loan|lending|lender)\b",
            r"\b(?:funding|finance|financing)\b",
            r"\b(?:capital)\b",
            r"\b(?:lease|leasing)\b",
            r"\bpersonal\s+loan\b",
            # Named equipment-finance and MCA lenders
            r"\bnextgear\b",
            r"\bcashflow\s+funding\b",
            r"\basset\s+lease\b",
            r"\bequipment\s+finance\b",
        ],
    },
    # -----------------------------------------------------------------------
    # 2. INTERNAL TRANSFERS & LINKED ACCOUNTS
    # -----------------------------------------------------------------------
    {
        "category": "Internal Transfers & Linked Accounts",
        "reason": (
            "Internal, account-to-account, online, mobile, payroll, or "
            "owner/business transfer"
        ),
        "patterns": [
            # Account-to-account
            r"\ba2a\b",
            r"\baccount[-\s]*to[-\s]*account\b",
            # Cash management
            r"\bcash\s+mgm?(?:nt|t)\b",
            r"\bcash\s+management\b",
            # COL XFER from business
            r"\bcol\s+xfer\b",
            # Deposit transfer referencing masked account numbers (xxxx1234 / ****1234)
            r"\bdeposit\s+transfer\b.*\b(?:x{2,}|\*{2,})\d{2,}\b",
            # Payroll account transfers (NOT payroll income)
            r"\bpayroll\s+(?:account|transfer|xfer)\b",
            # Fund / transfer / XFR / XFER (generic)
            r"\bfunds?\s+transfer(?:s)?\b",
            r"\btransfer(?:s)?\b",
            r"\bxfr\b",
            r"\bxfer\b",
            # Mobile banking transfers
            r"\bmobile\s+banking\s+transfer\b",
            r"\bmobile\s+(?:banking\s+)?xfer\b",
            # Online / internet banking transfers
            # (covers "INTERNET TRANSFER FROM: xxxxxx4927")
            r"\bonline\s+(?:banking\s+)?(?:transfer|xfer)\b",
            r"\binternet\s+transfer\b",
            # Online transfers FROM specific account types
            r"\bonline\s+transfers?\s+from\s+(?:checking|chk|savings?|mma|payroll)\b",
            # PC transfers
            r"\bpc\s+transfers?\b",
            # Telephone / tele transfers
            r"\btele(?:phone)?\s+transfers?\b",
            # Acorns micro-investment app deposits
            r"\bacorns\b",
            # "authorized from" (owner-name money transfers)
            r"\bauthorized\s+from\b",
        ],
    },
    # -----------------------------------------------------------------------
    # 3. BANKING CORRECTIONS, REVERSALS & PERKS
    # -----------------------------------------------------------------------
    {
        "category": "Banking Corrections, Reversals & Perks",
        "reason": (
            "Correction, reversal, return, refund, reward, interest, "
            "fee reversal, or verification deposit"
        ),
        "patterns": [
            # Credit adjustments / withdrawal-adjustment credit vouchers
            r"\bcredit\s+adjust(?:ment)?\b",
            r"\badjustment\b.*\bcredit\b",
            r"\bwithdrawal\s+adjustment\b",
            r"\bdebit\s+card\s+credit\s+voucher\b",
            # Deposit corrections / share-draft corrections
            r"\bdeposit\s+correction\b",
            r"\bshare\s+draft\s+correction\b",
            # Error deposits / misposted payments
            r"\berror\s+deposit\b",
            r"\bmisposted\b",
            # NSF (Non-Sufficient Funds) deposits
            r"\bnsf\b",
            r"\bnon[-\s]*sufficient\s+funds\b",
            # Returns / RTN / RET (word-boundary anchored to avoid false hits
            # on words like RETIREMENT, PATRON, RETURN-TO-SENDER descriptions
            # that don't represent banking returns)
            r"\breturn(?:ed|s)?\b",
            r"\brtn\b",
            r"\bret\b",
            # Cashback (always a bank perk — deduct)
            r"\bcash\s*back\b",
            # Rebates / RBT
            r"\brebates?\b",
            r"\brbt\b",
            # Dividends
            r"\bdividends?\b",
            # Refunds
            r"\brefunds?\b",
            # Treasury payments (TREAS / TREAS 310, etc.)
            r"\btreas(?:ury)?\b",
            # Vouchers / fee reversals / fee credits
            r"\bvouchers?\b",
            r"\bfees?\b.*\b(?:reversal|credit|refund)\b",
            # Trial / verify / verification deposits
            r"\btrial\s+deposits?\b",
            r"\bverify\s+deposits?\b",
            r"\bverification\s+deposits?\b",
        ],
        # ── Patterns that need extra context (false-positive guards) ──────
        # These are handled SEPARATELY in _match_rule() below, NOT in the
        # standard pattern loop.  They are listed here for documentation only.
        # "interest" → only deduct when banking context word is present
        # "rewards"  → only deduct when bank-perk context word is present
    },
]


# ---------------------------------------------------------------------------
# WIRE DEDUCTION PATTERNS
# Applied only when the description already contains the word "wire".
# Standard business wires (no matching keyword) are KEPT as revenue.
# ---------------------------------------------------------------------------
WIRE_DEDUCTION_PATTERNS: List[str] = [
    r"\bmerchant\b",
    r"\b(?:loc|line\s+of\s+credit)\b",
    r"\b(?:loan|lending|lender|funding|finance|financing|capital|lease|leasing)\b",
    r"\bnextgear\b",
    r"\bcashflow\s+funding\b",
    r"\basset\s+lease\b",
    r"\bequipment\s+finance\b",
    r"\badvance(?:s|d)?\b",
    r"\bolb\b",
    r"\bocc\b",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> float:
    """Safely coerce a value to float; returns 0.0 on failure."""
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _name_to_patterns(name: str) -> List[str]:
    """
    Turn an account-holder / business name string into regex patterns.

    Emits:
    - The full sanitised name (escaped).
    - Each 'significant' word (len >= 4, not a stop word).
    """
    if not name or len(name.strip()) < 3:
        return []

    stop_words = {
        "and", "the", "of", "or", "at", "in", "on", "for", "to", "from",
        "llc", "inc", "corp", "ltd", "co", "dba", "aka",
    }
    patterns: List[str] = []

    escaped_full = re.escape(name.strip())
    patterns.append(r"\b" + escaped_full + r"\b")

    words = re.split(r"[\s,\.&']+", name.strip())
    significant = [w for w in words if len(w) >= 4 and w.lower() not in stop_words]
    for word in significant:
        patterns.append(r"\b" + re.escape(word) + r"\b")

    return patterns


def _build_owner_patterns(metadata: Optional[Dict[str, Any]]) -> List[str]:
    """
    Build runtime regex patterns from document metadata.
    Keys checked: account_holder, business_name, owner_name.
    """
    if not metadata:
        return []
    patterns: List[str] = []
    for key in ("account_holder", "business_name", "owner_name"):
        value = metadata.get(key, "")
        if value:
            patterns.extend(_name_to_patterns(str(value)))
    return patterns


# ---------------------------------------------------------------------------
# Core matching logic
# ---------------------------------------------------------------------------

def _match_rule(
    description: str,
    wire_extra_patterns: Optional[List[str]] = None,
) -> Optional[Dict[str, str]]:
    """
    Return a dict describing why a credit should be deducted, or None if it
    should be kept as revenue.

    Wire rule (special conditional)
    --------------------------------
    If "wire" appears in the description:
      - Check WIRE_DEDUCTION_PATTERNS + injected owner/business patterns.
      - Any match → Deduction.
      - No match  → Revenue (standard business wire).

    Standard three-bucket rules
    ----------------------------
    Applied to all non-wire credits.

    Special guards (applied AFTER pattern loop):
      "interest" → deduct only when a banking-context word is also present.
      "rewards"  → deduct only when a bank-perk context word is also present.

    Owner/business name guard (non-wire only)
    -----------------------------------------
    Owner/business patterns are only flagged as deductions on non-wire credits
    when a transfer-indicator keyword is ALSO present.
    This prevents merchant card settlement lines from being misclassified.
    """
    text = description.lower()

    # ── Special conditional rule: Wire Deposits ──────────────────────────
    if re.search(r"\bwire\b", text):
        combined_wire_patterns = list(WIRE_DEDUCTION_PATTERNS)
        if wire_extra_patterns:
            combined_wire_patterns.extend(wire_extra_patterns)

        for pattern in combined_wire_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "category": "Special Conditional Rule: Wire Deposits",
                    "reason": (
                        "Wire deposit matched merchant, lender, financing, "
                        "LOC, or owner/business-name language"
                    ),
                    "matched_pattern": pattern,
                }
        return None  # Standard business wire → Revenue

    # ── Standard three-bucket rules ──────────────────────────────────────
    for rule in DEDUCTION_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "category": rule["category"],
                    "reason": rule["reason"],
                    "matched_pattern": pattern,
                }

    # ── Context-guarded: "interest" ──────────────────────────────────────
    # Bare \binterest\b fires on company names like "FIRST INTEREST FINANCIAL".
    # Only deduct when a banking-context word confirms it's actually interest income.
    if re.search(r"\binterest\b", text, re.IGNORECASE):
        if _INTEREST_BANKING_CONTEXT.search(text):
            return {
                "category": "Banking Corrections, Reversals & Perks",
                "reason": "Interest income/perk (not counted as operating revenue)",
                "matched_pattern": r"\binterest\b (with banking context)",
            }

    # ── Context-guarded: "rewards" ───────────────────────────────────────
    # Merchant loyalty program lines (STAPLES REWARDS DEPOSIT) should be KEPT.
    # Only deduct when a bank-perk indicator confirms it's from the bank itself.
    if re.search(r"\brewards?\b", text, re.IGNORECASE):
        if _REWARDS_BANK_CONTEXT.search(text):
            return {
                "category": "Banking Corrections, Reversals & Perks",
                "reason": "Bank reward/cashback perk (not counted as operating revenue)",
                "matched_pattern": r"\brewards?\b (with bank-perk context)",
            }

    # ── Owner/business name check (non-wire, with transfer-indicator guard) ─
    # Only flag when the description ALSO contains an explicit transfer keyword.
    if wire_extra_patterns and _TRANSFER_INDICATOR.search(text):
        for pattern in wire_extra_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "category": "Internal Transfers & Linked Accounts",
                    "reason": (
                        "Transfer description matches owner or business name "
                        "(internal sweep or self-transfer)"
                    ),
                    "matched_pattern": pattern,
                }

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_transactions(
    transactions: List[dict],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify every transaction credit as Revenue or Deduction and build a
    full audit-ready breakdown.

    Parameters
    ----------
    transactions : list of dicts
        Flat transaction list from the parser. Each dict must contain at
        minimum: description (or raw_text), credit, debit.
    metadata : dict, optional
        Document-level metadata from metadata_service.
        Expected keys: account_holder, business_name, owner_name.
        Used to detect owner-name / business-name wire and transfer matches.

    Returns
    -------
    dict with three keys:
        snapshot           – high-level totals: raw vs adjusted, variance
        credits_breakdown  – every credit itemised with status + reason
        debits_breakdown   – every debit with full description and amount
    """
    owner_patterns = _build_owner_patterns(metadata)

    raw_credit_total: float = 0.0
    adjusted_revenue_total: float = 0.0
    revenue_deduction_total: float = 0.0
    debit_total: float = 0.0

    credits_breakdown: List[dict] = []
    debits_breakdown: List[dict] = []

    for item in transactions:
        description = str(
            item.get("description") or item.get("raw_text") or ""
        ).strip()
        credit = _to_float(item.get("credit"))
        debit = _to_float(item.get("debit"))

        # ── Credits (incoming funds) ──────────────────────────────────────
        if credit > 0:
            raw_credit_total = round(raw_credit_total + credit, 2)

            match = _match_rule(description, wire_extra_patterns=owner_patterns)

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
                    "matched_pattern": item.get("revenue_matched_pattern"),
                }
            )

        # ── Debits (outgoing funds) ───────────────────────────────────────
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

    accepted_count = sum(1 for c in credits_breakdown if c["status"] == "Revenue")
    deduction_count = sum(1 for c in credits_breakdown if c["status"] == "Deduction")

    snapshot = {
        "raw_credit_total": raw_credit_total,
        "adjusted_revenue_total": adjusted_revenue_total,
        "revenue_deduction_total": revenue_deduction_total,
        "variance": round(raw_credit_total - adjusted_revenue_total, 2),
        "debit_total": debit_total,
        "credit_count": len(credits_breakdown),
        "accepted_revenue_count": accepted_count,
        "deduction_count": deduction_count,
        "debit_count": len(debits_breakdown),
    }

    return {
        "snapshot": snapshot,
        "credits_breakdown": credits_breakdown,
        "debits_breakdown": debits_breakdown,
    }