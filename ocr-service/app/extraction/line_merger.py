from statistics import median
from typing import List


def merge_lines(ocr_lines: List[dict]) -> List[dict]:
    """
    Merge individual OCR word/text boxes into logical rows.

    Key improvements vs. the original:
    - Per-page adaptive Y-threshold based on median character height.
    - Slightly tighter default (0.55 × median height) to avoid merging
      two-column rows (e.g. Navy Federal left/right columns).
    - Preserves per-item bounding boxes so downstream column-bucketing works.
    """
    if not ocr_lines:
        return []

    sorted_lines = sorted(
        ocr_lines, key=lambda line: (line["page"], line["y_min"], line["x_min"])
    )

    # Compute per-page median height for an adaptive threshold
    from collections import defaultdict
    page_heights: dict = defaultdict(list)
    for line in sorted_lines:
        h = line["y_max"] - line["y_min"]
        if h > 0:
            page_heights[line["page"]].append(h)

    def _y_threshold(page: int) -> float:
        heights = page_heights.get(page, [])
        if not heights:
            return 12.0
        return max(6, median(heights) * 0.55)

    rows = []
    for line in sorted_lines:
        current = rows[-1] if rows else None
        line_mid = (line["y_min"] + line["y_max"]) / 2
        threshold = _y_threshold(line["page"])
        line_items = line.get("items") or [line]

        if (
            current
            and current["page"] == line["page"]
            and abs(current["y_mid"] - line_mid) <= threshold
        ):
            current["items"].extend(line_items)
            # Rolling average of y_mid for stability
            current["y_mid"] = (current["y_mid"] + line_mid) / 2
        else:
            rows.append({"page": line["page"], "y_mid": line_mid, "items": list(line_items)})

    merged = []
    for row in rows:
        items = sorted(row["items"], key=lambda item: item["x_min"])
        text = " ".join(item["text"] for item in items)
        if not text.strip():
            continue
        confidence = sum(item["confidence"] for item in items) / len(items)
        merged.append(
            {
                "text": text,
                "confidence": confidence,
                "page": row["page"],
                "items": items,
                "x_min": min(item["x_min"] for item in items),
                "y_min": min(item["y_min"] for item in items),
                "x_max": max(item["x_max"] for item in items),
                "y_max": max(item["y_max"] for item in items),
            }
        )

    return merged
