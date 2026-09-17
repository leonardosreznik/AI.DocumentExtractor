from io import BytesIO
from pathlib import Path

import pytesseract
from PIL import Image


class OcrExtractor:

    TESSERACT_PATH = (
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
    )

    LANGUAGE = "por"

    def __init__(self):

        if not self.TESSERACT_PATH.exists():
            raise FileNotFoundError(
                "Tesseract OCR não encontrado em: "
                f"{self.TESSERACT_PATH}"
            )

        pytesseract.pytesseract.tesseract_cmd = str(
            self.TESSERACT_PATH
        )

    def extract(
        self,
        image_bytes: bytes
    ) -> str:

        if not image_bytes:
            return ""

        image = Image.open(
            BytesIO(image_bytes)
        )

        try:

            text = pytesseract.image_to_string(
                image,
                lang=self.LANGUAGE
            )

            return text.strip()

        finally:

            image.close()