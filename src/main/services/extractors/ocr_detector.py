class OcrDetector:

    MIN_TEXT_LENGTH = 20

    @classmethod
    def needs_ocr(cls, text: str) -> bool:

        if not text:
            return True

        normalized_text = text.strip()

        return len(normalized_text) < cls.MIN_TEXT_LENGTH