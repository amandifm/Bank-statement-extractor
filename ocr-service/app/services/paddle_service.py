import os
from functools import lru_cache
from typing import List

from paddleocr import PaddleOCR


@lru_cache(maxsize=1)
def get_ocr_engine():
    language = os.getenv("PADDLE_LANGUAGE", "en")
    return PaddleOCR(use_angle_cls=False, lang=language, show_log=False)


def _normalize_result(result, page_number: int) -> List[dict]:
    lines = []
    if not result:
        return lines

    page_result = result[0] if len(result) == 1 and isinstance(result[0], list) else result
    for item in page_result:
        if not item or len(item) < 2:
            continue

        box = item[0]
        text_data = item[1]
        text = text_data[0] if text_data else ""
        confidence = float(text_data[1]) if len(text_data) > 1 else 0.0
        xs = [point[0] for point in box]
        ys = [point[1] for point in box]

        lines.append(
            {
                "text": text.strip(),
                "confidence": confidence,
                "box": box,
                "x_min": min(xs),
                "x_max": max(xs),
                "y_min": min(ys),
                "y_max": max(ys),
                "page": page_number,
            }
        )

    return [line for line in lines if line["text"]]


def extract_lines(image, page_number: int) -> List[dict]:
    result = get_ocr_engine().ocr(image, cls=True)
    return _normalize_result(result, page_number)
