from app.extraction.line_merger import merge_lines


def detect_rows(ocr_lines):
    return merge_lines(ocr_lines)
