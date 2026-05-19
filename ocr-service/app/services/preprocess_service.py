import cv2

from app.preprocess.denoise import denoise
from app.preprocess.deskew import deskew
from app.preprocess.sharpen import sharpen
from app.preprocess.threshold import adaptive_threshold


def preprocess_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    image = deskew(image)
    image = denoise(image)
    image = sharpen(image)
    image = adaptive_threshold(image)
    return image
