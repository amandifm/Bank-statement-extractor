import logging

from app.extraction.regex_parser import parse_transactions
from app.extraction.row_detector import detect_rows
from app.extraction.table_detector import detect_table_region
from app.services.metadata_service import extract_document_metadata

logger = logging.getLogger(__name__)

SKIP_SECTIONS = [

    "DAILY BALANCE",
    "CHECKS IN NUMBER ORDER",
    "CHECKS",
    "Date Check No Amount",
    "PAGE",
    "Page:",
    "MEMBER FDIC",
    "ACCOUNT NUMBER",
    "STATEMENT DATE",
    "Beginning Balance",
    "Ending Balance",
    "Activity in Date Order",
    "Date Description Amount",
    "BUSINESS CHECKING",
    "Primary Account",
    "Account:",
]


def parse_bank_statement(ocr_lines):
    """Parse OCR lines into structured transaction data."""

    if not ocr_lines:
        logger.warning("No OCR lines provided for parsing")

        return {
            "transactions": [],
            "summary": {
                "transaction_count": 0,
                "average_confidence": 0,
                "pages_processed": 0,
                "status": "empty",
            },
            "raw_text": "",
            "rows": [],
        }

    logger.info(
        f"Starting parsing of {len(ocr_lines)} OCR lines"
    )

    # Step 1
    try:

        rows = detect_rows(ocr_lines)

        logger.info(
            f"Detected {len(rows)} rows after merging"
        )

    except Exception as e:

        logger.error(
            f"Row detection failed: {e}"
        )

        rows = ocr_lines

    # Step 2
    try:

        rows = detect_table_region(rows)

        logger.info(
            f"Filtered to {len(rows)} table rows"
        )

    except Exception as e:

        logger.error(
            f"Table detection failed: {e}"
        )

    # NEW STEP 3
    filtered_rows=[]

    for row in rows:

        text = row.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        if any(
            section.lower() in text.lower()
            for section in SKIP_SECTIONS
        ):

            logger.debug(
                f"Skipping row: {text}"
            )

            continue

        filtered_rows.append(row)

    rows = filtered_rows

    logger.info(
        f"Rows after filtering: {len(rows)}"
    )

    # Step 4
    try:

        transactions = parse_transactions(rows)

        logger.info(
            f"Parsed {len(transactions)} transactions"
        )

    except Exception as e:

        logger.error(
            f"Transaction parsing failed: {e}"
        )

        transactions=[]

    # Generate raw text
    raw_text="\n".join(
        row.get("text","")
        for row in rows
        if row.get("text")
    )

    avg_confidence = 0

    if transactions:

        avg_confidence = (
            sum(
                item.get(
                    "confidence",
                    0.5
                )
                for item in transactions
            ) / len(transactions)
        )

    pages_processed = len(
        set(
            line["page"]
            for line in ocr_lines
        )
    )

    summary = {

        "transaction_count":
            len(transactions),

        "average_confidence":
            round(
                avg_confidence,
                4
            ),

        "pages_processed":
            pages_processed,

        "status":
            "complete"
            if transactions
            else "needs_review"
    }

    metadata = extract_document_metadata(
        raw_text
    )

    logger.info(
        f"Parsing complete: {summary}"
    )

    return {

        "transactions":
            transactions,

        "summary":
            summary,

        "raw_text":
            raw_text,

        "rows":
            rows,

        "metadata":
            metadata,
    }