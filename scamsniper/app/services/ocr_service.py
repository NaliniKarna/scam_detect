import logging
import io
from PIL import Image

try:
    import easyocr
    import numpy as np
    EASYOCR_AVAILABLE = True
except Exception as e:
    EASYOCR_AVAILABLE = False
    easyocr = None
    np = None
    logging.warning("EasyOCR not available: %s", e)

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self.reader = None
        self.available = False

    def load(self):
        """Attempt to load the OCR reader. Failures are caught and logged."""
        if not EASYOCR_AVAILABLE:
            logger.warning("EasyOCR not installed; OCR unavailable")
            return False
        try:
            self.reader = easyocr.Reader(["en", "hi"])
            self.available = True
            logger.info("Loaded EasyOCR")
            return True
        except Exception as e:
            logger.warning("Failed to load EasyOCR: %s", e)
            self.reader = None
            self.available = False
            return False

    def extract_text(self, image_bytes: bytes):
        """Extract text from image bytes. Returns placeholder if OCR unavailable."""
        if not self.available or self.reader is None:
            return {"text": ""}

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(img)
            results = self.reader.readtext(img_np, detail=0)
            extracted = " ".join(results)
            return {"text": extracted.strip()}
        except Exception as e:
            logger.warning("OCR extraction failed: %s", e)
            return {"text": ""}


ocr_engine = OCRService()
