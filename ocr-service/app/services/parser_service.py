from app.extraction.regex_parser import parse_transactions
from app.extraction.row_detector import detect_rows
from app.extraction.table_detector import detect_table_region


def parse_bank_statement(ocr_lines):
    rows = detect_table_region(detect_rows(ocr_lines))
    transactions = parse_transactions(rows)
    raw_text = "\n".join(row["text"] for row in rows)

    avg_confidence = 0
    if transactions:
        avg_confidence = sum(item["confidence"] for item in transactions) / len(transactions)

    summary = {
        "transaction_count": len(transactions),
        "average_confidence": round(avg_confidence, 4),
        "pages_processed": len({line["page"] for line in ocr_lines}),
        "status": "complete" if transactions else "needs_review",
    }

    return {
        "transactions": transactions,
        "summary": summary,
        "raw_text": raw_text,
        "rows": rows,
    }
