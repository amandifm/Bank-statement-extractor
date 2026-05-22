import cv2
import numpy as np
from PIL import Image

from app.preprocess.denoise import denoise
from app.preprocess.deskew import deskew
from app.preprocess.sharpen import sharpen
from app.preprocess.threshold import adaptive_threshold


def preprocess_image(image_path: str):
    """
    Load and preprocess a scanned bank-statement image for PaddleOCR.

    Pipeline (revised):
      1. deskew       – correct page tilt
      2. denoise      – remove scanner noise (light touch for clean renders)
      3. threshold    – convert to binary grayscale (BGR output)
      4. sharpen      – enhance edges on the already-binarised image

    The previous order ran sharpen before threshold, which amplified noise
    before binarisation and produced halos around digits.

    WebP support: cv2.imread cannot read WebP on all builds.  We fall back to
    PIL for those formats so Bank_statement__6_.webp (Bank of Baroda) is handled
    correctly.
    """
    image = _safe_imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    image = deskew(image)
    image = denoise(image)       # ← denoise first while still colour
    image = adaptive_threshold(image)   # ← binarise to grayscale-in-BGR
    image = sharpen(image)       # ← sharpen the clean binary result
    return image


def _safe_imread(image_path: str):
    """Read an image via cv2; fall back to PIL for WebP and other exotic formats."""
    img = cv2.imread(image_path)
    if img is not None:
        return img

    try:
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img
    except Exception:
        return None
