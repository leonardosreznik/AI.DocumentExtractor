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

            for index, page in enumerate(
                document
            ):

                unit = self._extract_page(
                    document=document,
                    page=page,
                    index=index,
                )

                units.append(
                    unit
                )

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
                    has_ocr_text=has_ocr_text,
                )
            )

            return ExtractionResult(
                units=units,
                extraction_method=extraction_method,
                ocr_used=has_ocr_text,
            )

        finally:

            document.close()

    def _extract_page(
        self,
        document: pymupdf.Document,
        page: pymupdf.Page,
        index: int,
    ) -> DocumentUnit:

        analysis = (
            self._page_content_detector.analyze(
                page
            )
        )

        native_text = (
            page.get_text(
                "text"
            ).strip()
        )

        blocks: list[DocumentBlock] = []

        if native_text:

            blocks.append(
                DocumentBlock(
                    type=DocumentBlockType.TEXT,
                    text=native_text,
                )
            )

        ocr_texts: list[str] = []

        ocr_used = False

        image_index = 0

        for detected_image in analysis.images:

            image_data = (
                self._extract_image(
                    document=document,
                    page=page,
                    detected_image=detected_image,
                )
            )

            if image_data is None:
                continue

            (
                image_bytes,
                image_extension,
            ) = image_data

            image_index += 1

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

            content_type = (
                self._resolve_content_type(
                    image_extension
                )
            )

            image_id = (
                self._store_image(
                    image_bytes=image_bytes,
                    content_type=content_type,
                    extension=image_extension,
                    page_number=index + 1,
                    image_index=image_index,
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
                    position=detected_image.position,
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
                    text=ocr_text,
                )
            )

            ocr_used = True

        combined_text = (
            self._combine_text(
                native_text=native_text,
                ocr_texts=ocr_texts,
            )
        )

        extraction_method = (
            self._resolve_page_extraction_method(
                has_native_text=bool(native_text),
                has_ocr_text=bool(ocr_texts),
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

    @staticmethod
    def _extract_image(
        document: pymupdf.Document,
        page: pymupdf.Page,
        detected_image,
    ) -> tuple[bytes, str] | None:

        if detected_image.xref is not None:

            try:

                extracted = (
                    document.extract_image(
                        detected_image.xref
                    )
                )

            except Exception:
                return None

            image_bytes = extracted.get(
                "image"
            )

            extension = extracted.get(
                "ext"
            )

            if not image_bytes or not extension:
                return None

            return (
                image_bytes,
                str(extension).lower(),
            )

        blocks = page.get_text(
            "dict"
        ).get(
            "blocks",
            []
        )

        for block in blocks:

            if block.get(
                "type"
            ) != 1:
                continue

            bbox = block.get(
                "bbox"
            )

            if not bbox:
                continue

            position = (
                PdfExtractor._create_image_position(
                    bbox
                )
            )

            if not PdfExtractor._same_position(
                position,
                detected_image.position,
            ):
                continue

            image_bytes = block.get(
                "image"
            )

            extension = block.get(
                "ext"
            )

            if not image_bytes:
                return None

            if not extension:
                extension = "bin"

            return (
                image_bytes,
                str(extension).lower(),
            )

        return None

    @staticmethod
    def _same_position(
        first: ImagePosition,
        second: ImagePosition,
    ) -> bool:

        tolerance = 0.01

        return (
            abs(first.x - second.x)
            <= tolerance
            and
            abs(first.y - second.y)
            <= tolerance
            and
            abs(first.width - second.width)
            <= tolerance
            and
            abs(first.height - second.height)
            <= tolerance
        )

    def _store_image(
        self,
        image_bytes: bytes,
        content_type: str,
        extension: str,
        page_number: int,
        image_index: int,
    ) -> str | None:

        if self._image_storage_service is None:
            return None

        file_name = (
            f"page-{page_number}-"
            f"image-{image_index}."
            f"{extension}"
        )

        return self._image_storage_service.save(
            image_bytes=image_bytes,
            content_type=content_type,
            file_name=file_name,
            metadata={
                "page_number": page_number,
                "image_index": image_index,
                "extension": extension,
            },
        )

    @staticmethod
    def _resolve_content_type(
        extension: str,
    ) -> str:

        extension = extension.lower()

        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "bmp": "image/bmp",
            "tif": "image/tiff",
            "tiff": "image/tiff",
            "jp2": "image/jp2",
            "jpx": "image/jpx",
            "webp": "image/webp",
            "svg": "image/svg+xml",
        }

        return content_types.get(
            extension,
            f"image/{extension}",
        )

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

        return "\n\n".join(
            parts
        )

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