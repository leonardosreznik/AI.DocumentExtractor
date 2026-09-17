from src.main.models.enums import ImageContentType


class OcrDetector:

    MIN_TEXT_LENGTH = 20

    @classmethod
    def needs_ocr(
        cls,
        text: str
    ) -> bool:

        if not text:
            return True

        normalized_text = text.strip()

        return len(
            normalized_text
        ) < cls.MIN_TEXT_LENGTH

    @staticmethod
    def needs_image_ocr(
        image_content_type: ImageContentType
    ) -> bool:

        return image_content_type in (
            ImageContentType.TEXT,
            ImageContentType.MIXED,
        )