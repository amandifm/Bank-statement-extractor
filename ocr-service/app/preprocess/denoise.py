import cv2


def denoise(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 7, 7, 7, 21)
