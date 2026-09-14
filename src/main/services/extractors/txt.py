from src.main.services.extractors.base import DocumentExtractor

from src.main.models.enums import (
    DocumentBlockType,
    DocumentUnitType,
    ExtractionMethod,
)

from src.main.models.response import (
    DocumentBlock,
    DocumentLocation,
    DocumentUnit,
    ExtractionResult,
)


class TxtExtractor(DocumentExtractor):

    def can_handle(
        self,
        content_type: str,
        file_name: str
    ) -> bool:

        return (
            content_type == "text/plain"
            or file_name.lower().endswith(".txt")
        )

    def extract(
        self,
        content: bytes
    ) -> ExtractionResult:

        text = content.decode("utf-8")

        unit = DocumentUnit(
            index=0,
            type=DocumentUnitType.DOCUMENT,
            location=DocumentLocation(),

            text=text,
            search_text=text,

            extraction_method=ExtractionMethod.NATIVE,
            ocr_used=False,

            blocks=[
                DocumentBlock(
                    type=DocumentBlockType.TEXT,
                    text=text
                )
            ]
        )

        return ExtractionResult(
            units=[unit],
            extraction_method=ExtractionMethod.NATIVE,
            ocr_used=False
        )