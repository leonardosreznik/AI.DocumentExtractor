import pymupdf

from src.main.services.extractors.base import DocumentExtractor
from src.main.services.extractors.page_content_detector import (
    PageContentDetector,
)

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


class PdfExtractor(DocumentExtractor):

    def __init__(
        self,
        page_content_detector: PageContentDetector
    ):
        self._page_content_detector = page_content_detector

    def can_handle(
        self,
        content_type: str,
        file_name: str
    ) -> bool:

        return (
            content_type == "application/pdf"
            or file_name.lower().endswith(".pdf")
        )

    def extract(
        self,
        content: bytes
    ) -> ExtractionResult:

        document = pymupdf.open(
            stream=content,
            filetype="pdf"
        )
        
        units: list[DocumentUnit] = []

        for index, page in enumerate(document):

            analysis = self._page_content_detector.analyze(page)

            text = page.get_text("text")

            unit = DocumentUnit(
                index=index,
                type=DocumentUnitType.PAGE,

                location=DocumentLocation(
                    page_number=index + 1
                ),

                content_type=analysis.content_type,

                text=text,
                search_text=text,

                extraction_method=ExtractionMethod.NATIVE,
                ocr_used=False,

                images=analysis.images,

                blocks=[
                    DocumentBlock(
                        type=DocumentBlockType.TEXT,
                        text=text
                    )
                ]
            )

            units.append(unit)

        document.close()

        return ExtractionResult(
            units=units,
            extraction_method=ExtractionMethod.NATIVE,
            ocr_used=False
        )