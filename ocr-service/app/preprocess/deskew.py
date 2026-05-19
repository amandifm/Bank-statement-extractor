def deskew(image):
    # PaddleOCR handles small rotations well. Keep this hook lightweight so the
    # pipeline can be extended later without changing service contracts.
    return image
