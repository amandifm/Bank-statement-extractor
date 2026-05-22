import cv2


def denoise(image):
    """
    Remove scanner noise from a bank-statement image.

    Previous values (h=7, hColor=7, templateWindowSize=7, searchWindowSize=21)
    were too aggressive: they smeared digit strokes on clean PDF renders and
    made 0/8/6 indistinguishable to PaddleOCR.

    Conservative values (h=3, hColor=3) remove genuine noise without blurring
    fine character detail.  For truly clean 300 DPI PDF renders a light
    Gaussian blur is sufficient and much faster, but we keep NlMeans so the
    same path works for noisy scans too.
    """
    return cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)
