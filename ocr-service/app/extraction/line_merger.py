from statistics import median
from typing import List


def merge_lines(ocr_lines: List[dict]) -> List[dict]:
    if not ocr_lines:
        return []

    sorted_lines = sorted(ocr_lines, key=lambda line: (line["page"], line["y_min"], line["x_min"]))
    heights = [line["y_max"] - line["y_min"] for line in sorted_lines]
    y_threshold = max(10, median(heights) * 0.7) if heights else 12

    rows = []
    for line in sorted_lines:
        current = rows[-1] if rows else None
        line_mid = (line["y_min"] + line["y_max"]) / 2

        if (
            current
            and current["page"] == line["page"]
            and abs(current["y_mid"] - line_mid) <= y_threshold
        ):
            current["items"].append(line)
            current["y_mid"] = (current["y_mid"] + line_mid) / 2
        else:
            rows.append({"page": line["page"], "y_mid": line_mid, "items": [line]})

    merged = []
    for row in rows:
        items = sorted(row["items"], key=lambda item: item["x_min"])
        text = " ".join(item["text"] for item in items)
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
