import pymupdf

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
    ImagePosition,
)

from src.main.services.extractors.base import DocumentExtractor
from src.main.services.extractors.image_content_classifier import (
    ImageContentClassifier,
)
from src.main.services.extractors.image_text_analyzer import (
    ImageTextAnalyzer,
)
from src.main.services.extractors.ocr_detector import (
    OcrDetector,
)
from src.main.services.extractors.ocr_extractor import (
    OcrExtractor,
)
from src.main.services.extractors.page_content_detector import (
    PageContentDetector,
)
from src.main.services.storage.image_storage import (
    ImageStorageService,
)


class PdfExtractor(DocumentExtractor):

    IMAGE_URL_PREFIX = "/images"

    def __init__(
        self,
        page_content_detector: PageContentDetector,
        image_text_analyzer: ImageTextAnalyzer | None = None,
        image_content_classifier: ImageContentClassifier | None = None,
        ocr_detector: OcrDetector | None = None,
        ocr_extractor: OcrExtractor | None = None,
        image_storage_service: ImageStorageService | None = None,
    ):
        self._page_content_detector = page_content_detector

        self._image_text_analyzer = (
            image_text_analyzer or ImageTextAnalyzer()
        )

        self._image_content_classifier = (
            image_content_classifier or ImageContentClassifier()
        )

        self._ocr_detector = (
            ocr_detector or OcrDetector()
        )

        self._ocr_extractor = (
            ocr_extractor or OcrExtractor()
        )

        self._image_storage_service = (
            image_storage_service
        )

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

        try:

            units: list[DocumentUnit] = []

            has_native_text = False
            has_ocr_text = False

            for index, page in enumerate(document):

                unit = self._extract_page(
                    page=page,
                    index=index
                )

                units.append(unit)

                if unit.extraction_method in (
                    ExtractionMethod.NATIVE,
                    ExtractionMethod.HYBRID,
                ):

                    has_native_text = True

                if unit.ocr_used:

                    has_ocr_text = True

            extraction_method = (
                self._resolve_extraction_method(
                    has_native_text=has_native_text,
                    has_ocr_text=has_ocr_text
                )
            )

            return ExtractionResult(
                units=units,
                extraction_method=extraction_method,
                ocr_used=has_ocr_text
            )

        finally:

            document.close()

    def _extract_page(
        self,
        page: pymupdf.Page,
        index: int
    ) -> DocumentUnit:

        analysis = (
            self._page_content_detector.analyze(
                page
            )
        )

        native_text = (
            page.get_text("text").strip()
        )

        blocks: list[DocumentBlock] = []

        if native_text:

            blocks.append(
                DocumentBlock(
                    type=DocumentBlockType.TEXT,
                    text=native_text
                )
            )

        ocr_texts: list[str] = []

        ocr_used = False

        page_blocks = (
            page.get_text("dict")
            .get("blocks", [])
        )

        for block in page_blocks:

            if block.get("type") != 1:
                continue

            image_bytes = block.get("image")
            bbox = block.get("bbox")

            if not image_bytes or not bbox:
                continue

            position = (
                self._create_image_position(
                    bbox
                )
            )

            image_analysis = (
                self._image_text_analyzer.analyze(
                    image_bytes
                )
            )

            image_content_type = (
                self._image_content_classifier.classify(
                    image_analysis
                )
            )

            image_id = (
                self._store_image(
                    image_bytes=image_bytes,
                    content_type=self._resolve_image_content_type(
                        block
                    ),
                    page_number=index + 1,
                )
            )

            image_url = (
                self._create_image_url(
                    image_id
                )
            )

            blocks.append(
                DocumentBlock(
                    type=DocumentBlockType.IMAGE,
                    position=position,
                    image_content_type=image_content_type,
                    image_id=image_id,
                    image_url=image_url,
                )
            )

            if not self._ocr_detector.needs_image_ocr(
                image_content_type
            ):
                continue

            ocr_text = (
                self._ocr_extractor.extract(
                    image_bytes
                )
            )

            if not ocr_text:
                continue

            ocr_texts.append(
                ocr_text
            )

            blocks.append(
                DocumentBlock(
                    type=DocumentBlockType.TEXT,
                    text=ocr_text
                )
            )

            ocr_used = True

        combined_text = (
            self._combine_text(
                native_text=native_text,
                ocr_texts=ocr_texts
            )
        )

        extraction_method = (
            self._resolve_page_extraction_method(
                has_native_text=bool(native_text),
                has_ocr_text=bool(ocr_texts)
            )
        )

        return DocumentUnit(
            index=index,
            type=DocumentUnitType.PAGE,
            location=DocumentLocation(
                page_number=index + 1
            ),
            text=combined_text,
            search_text=combined_text,
            extraction_method=extraction_method,
            ocr_used=ocr_used,
            blocks=blocks,
        )

    def _store_image(
        self,
        image_bytes: bytes,
        content_type: str,
        page_number: int,
    ) -> str | None:

        if self._image_storage_service is None:
            return None

        return self._image_storage_service.save(
            image_bytes=image_bytes,
            content_type=content_type,
            file_name=f"page-{page_number}.png",
            metadata={
                "page_number": page_number,
            },
        )

    @staticmethod
    def _resolve_image_content_type(
        block: dict
    ) -> str:

        content_type = block.get(
            "ext"
        )

        if content_type:

            return (
                f"image/{content_type.lower()}"
            )

        return "application/octet-stream"

    @classmethod
    def _create_image_url(
        cls,
        image_id: str | None
    ) -> str | None:

        if image_id is None:
            return None

        return (
            f"{cls.IMAGE_URL_PREFIX}/{image_id}"
        )

    @staticmethod
    def _create_image_position(
        bbox: tuple
    ) -> ImagePosition:

        x0, y0, x1, y1 = bbox

        return ImagePosition(
            x=float(x0),
            y=float(y0),
            width=float(x1 - x0),
            height=float(y1 - y0),
        )

    @staticmethod
    def _combine_text(
        native_text: str,
        ocr_texts: list[str]
    ) -> str:

        parts: list[str] = []

        if native_text:
            parts.append(
                native_text
            )

        parts.extend(
            text
            for text in ocr_texts
            if text
        )

        return "\n\n".join(parts)

    @staticmethod
    def _resolve_page_extraction_method(
        has_native_text: bool,
        has_ocr_text: bool
    ) -> ExtractionMethod:

        if has_native_text and has_ocr_text:
            return ExtractionMethod.HYBRID

        if has_ocr_text:
            return ExtractionMethod.OCR

        return ExtractionMethod.NATIVE

    @staticmethod
    def _resolve_extraction_method(
        has_native_text: bool,
        has_ocr_text: bool
    ) -> ExtractionMethod:

        if has_native_text and has_ocr_text:
            return ExtractionMethod.HYBRID

        if has_ocr_text:
            return ExtractionMethod.OCR

        return ExtractionMethod.NATIVE