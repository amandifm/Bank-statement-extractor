#!/usr/bin/env python3
"""Focused parser checks for bank-statement table layouts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.extraction.regex_parser import parse_transactions


def item(text, x1, x2):
    return {
        "text": text,
        "confidence": 0.96,
        "x_min": x1,
        "x_max": x2,
        "y_min": 0,
        "y_max": 10,
    }


def row(text, items, y=0):
    for value in items:
        value["y_min"] = y
        value["y_max"] = y + 10
    return {
        "text": text,
        "confidence": 0.94,
        "page": 1,
        "items": items,
        "x_min": min(value["x_min"] for value in items),
        "x_max": max(value["x_max"] for value in items),
        "y_min": y,
        "y_max": y + 10,
    }


def test_statement_with_without_year_dates():
    rows = [
        row(
            "Date Description Withdrawal Deposit Balance",
            [
                item("Date", 10, 50),
                item("Description", 100, 220),
                item("Withdrawal", 430, 520),
                item("Deposit", 560, 640),
                item("Balance", 700, 780),
            ],
        ),
        row(
            "02/01 PGD EasyPay Debit 203.24 22,098.23",
            [
                item("02/01", 10, 60),
                item("PGD EasyPay Debit", 100, 300),
                item("203.24", 430, 500),
                item("22,098.23", 700, 780),
            ],
            20,
        ),
        row(
            "02/04 Check No. 2345 450.00 22,477.00",
            [
                item("02/04", 10, 60),
                item("Check No. 2345", 100, 300),
                item("450.00", 560, 640),
                item("22,477.00", 700, 780),
            ],
            40,
        ),
    ]

    transactions = parse_transactions(rows)

    assert len(transactions) == 2
    assert transactions[0]["date"] == "02/01"
    assert transactions[0]["debit"] == 203.24
    assert transactions[0]["credit"] is None
    assert transactions[1]["credit"] == 450.00
    assert transactions[1]["debit"] is None


def test_statement_with_reference_column_and_negative_balance():
    rows = [
        row(
            "Date Description Ref. Withdrawals Deposits Balance",
            [
                item("Date", 10, 55),
                item("Description", 100, 220),
                item("Ref.", 360, 410),
                item("Withdrawals", 445, 540),
                item("Deposits", 575, 650),
                item("Balance", 700, 780),
            ],
        ),
        row(
            "2003-11-06 Mortgage Payment 710.49 -62.47",
            [
                item("2003-11-06", 10, 90),
                item("Mortgage Payment", 100, 260),
                item("710.49", 445, 515),
                item("-62.47", 700, 760),
            ],
            20,
        ),
    ]

    transactions = parse_transactions(rows)

    assert len(transactions) == 1
    assert transactions[0]["debit"] == 710.49
    assert transactions[0]["balance"] == -62.47


def test_multiline_particulars_are_kept_with_row():
    rows = [
        row(
            "Date Particulars Instrument No Withdrawals Deposits Balance",
            [
                item("Date", 10, 55),
                item("Particulars", 100, 220),
                item("Instrument No", 330, 430),
                item("Withdrawals", 465, 560),
                item("Deposits", 600, 680),
                item("Balance", 730, 810),
            ],
        ),
        row(
            "24-04-2023 MPAY/UPI/TRTR/022513331882/VI 500.00 38,492.24",
            [
                item("24-04-2023", 10, 90),
                item("MPAY/UPI/TRTR/022513331882/VI", 100, 310),
                item("500.00", 600, 680),
                item("38,492.24", 730, 810),
            ],
            20,
        ),
        row(
            "JB/akshu.ballaI@ok/U",
            [item("JB/akshu.ballaI@ok/U", 100, 310)],
            35,
        ),
    ]

    transactions = parse_transactions(rows)

    assert len(transactions) == 1
    assert transactions[0]["credit"] == 500.00
    assert "JB/akshu.ballaI@ok/U" in transactions[0]["description"]


def test_dated_opening_balance_row_is_not_dropped():
    rows = [
        row(
            "Date Description Withdrawals Deposits Balance",
            [
                item("Date", 10, 50),
                item("Description", 100, 220),
                item("Withdrawals", 430, 520),
                item("Deposits", 560, 640),
                item("Balance", 700, 780),
            ],
        ),
        row(
            "07/01/2023 Opening Balance - - $5,000.00",
            [
                item("07/01/2023", 10, 90),
                item("Opening Balance", 100, 260),
                item("-", 430, 450),
                item("-", 560, 580),
                item("$5,000.00", 700, 780),
            ],
            20,
        ),
    ]

    transactions = parse_transactions(rows)

    assert len(transactions) == 1
    assert transactions[0]["description"] == "Opening Balance"
    assert transactions[0]["debit"] is None
    assert transactions[0]["credit"] is None
    assert transactions[0]["balance"] == 5000.00


if __name__ == "__main__":
    test_statement_with_without_year_dates()
    test_statement_with_reference_column_and_negative_balance()
    test_multiline_particulars_are_kept_with_row()
    test_dated_opening_balance_row_is_not_dropped()
    print("Bank statement table parser tests passed")
