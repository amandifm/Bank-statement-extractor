def detect_table_region(rows):
    # Keep all rows for now. Most bank statements have table headers that vary
    # by bank, so downstream parsing is intentionally tolerant.
    return rows
