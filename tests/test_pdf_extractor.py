from io import BytesIO

import pymupdf
from PIL import Image, ImageDraw

from src.main.models.enums import (
    DocumentBlockType,
    ExtractionMethod,
    ImageContentType,
)

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

from src.main.services.extractors.pdf import (
    PdfExtractor,
)

from src.main.services.storage.image_storage import (
    ImageStorageService,
)

from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


class FakeOcrExtractor:

    def __init__(
        self,
        text: str = "TEXTO OCR DE TESTE"
    ):
        self.text = text
        self.call_count = 0

    def extract(
        self,
        image_bytes: bytes
    ) -> str:

        self.call_count += 1

        return self.text


class FakeImageTextAnalyzer:

    def __init__(
        self,
        has_text: bool = True
    ):
        self.has_text = has_text

    def analyze(
        self,
        image_bytes: bytes
    ):
        from src.main.models.response import (
            ImageTextAnalysis,
        )

        return ImageTextAnalysis(
            has_text=self.has_text,
            confidence=1.0 if self.has_text else 0.0,
            edge_density=0.01,
            component_count=10,
            average_component_width=10.0,
            average_component_height=10.0,
            average_component_area=100.0,
            small_component_ratio=0.8,
            component_density=0.001,
            vertical_group_count=3,
            horizontal_coverage=0.8,
            horizontal_projection_variance=0.001,
            vertical_spacing_mean=0.05,
            vertical_spacing_std=0.01,
            max_component_area_ratio=1.0,
            max_component_width_ratio=1.0,
            max_component_height_ratio=1.0,
            components=[],
        )


class FakeImageContentClassifier:

    def __init__(
        self,
        content_type: ImageContentType
    ):
        self.content_type = content_type

    def classify(
        self,
        analysis
    ) -> ImageContentType:

        return self.content_type


def create_pdf(
    native_text: str | None = None,
    image_bytes: bytes | None = None
) -> bytes:

    document = pymupdf.open()

    page = document.new_page(
        width=595,
        height=842
    )

    if native_text:

        page.insert_text(
            (50, 100),
            native_text,
            fontsize=14
        )

    if image_bytes:

        page.insert_image(
            pymupdf.Rect(
                50,
                150,
                550,
                450
            ),
            stream=image_bytes
        )

    pdf_bytes = document.tobytes()

    document.close()

    return pdf_bytes


def create_test_image() -> bytes:

    image = Image.new(
        "RGB",
        (600, 300),
        "white"
    )

    draw = ImageDraw.Draw(
        image
    )

    draw.text(
        (50, 100),
        "TEXTO DA IMAGEM",
        fill="black"
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


def create_extractor(
    image_content_type: ImageContentType,
    ocr_extractor: FakeOcrExtractor,
    image_storage_service: ImageStorageService | None = None,
) -> PdfExtractor:

    return PdfExtractor(
        page_content_detector=PageContentDetector(),
        image_text_analyzer=FakeImageTextAnalyzer(),
        image_content_classifier=FakeImageContentClassifier(
            image_content_type
        ),
        ocr_detector=OcrDetector(),
        ocr_extractor=ocr_extractor,
        image_storage_service=image_storage_service,
    )


def test_extract_native_pdf():

    pdf = create_pdf(
        native_text="Este é um documento digital com texto nativo."
    )

    ocr = FakeOcrExtractor()

    extractor = create_extractor(
        image_content_type=ImageContentType.TEXT,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    assert len(result.units) == 1

    unit = result.units[0]

    assert unit.extraction_method == (
        ExtractionMethod.NATIVE
    )

    assert unit.ocr_used is False

    assert (
        "documento digital"
        in unit.text
    )

    assert ocr.call_count == 0


def test_extract_scanned_pdf():

    image = create_test_image()

    pdf = create_pdf(
        image_bytes=image
    )

    ocr = FakeOcrExtractor(
        text="CERTIDAO EXTRAIDA POR OCR"
    )

    extractor = create_extractor(
        image_content_type=ImageContentType.TEXT,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    assert len(result.units) == 1

    unit = result.units[0]

    assert unit.extraction_method == (
        ExtractionMethod.OCR
    )

    assert unit.ocr_used is True

    assert (
        "CERTIDAO EXTRAIDA POR OCR"
        in unit.text
    )

    assert ocr.call_count == 1


def test_extract_hybrid_pdf():

    image = create_test_image()

    pdf = create_pdf(
        native_text="Processo número 123456 possui certidão.",
        image_bytes=image
    )

    ocr = FakeOcrExtractor(
        text="CERTIDAO DIGITALIZADA"
    )

    extractor = create_extractor(
        image_content_type=ImageContentType.TEXT,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    assert len(result.units) == 1

    unit = result.units[0]

    assert unit.extraction_method == (
        ExtractionMethod.HYBRID
    )

    assert unit.ocr_used is True

    assert (
        "Processo número 123456"
        in unit.text
    )

    assert (
        "CERTIDAO DIGITALIZADA"
        in unit.text
    )

    assert ocr.call_count == 1


def test_photo_does_not_trigger_ocr():

    image = create_test_image()

    pdf = create_pdf(
        image_bytes=image
    )

    ocr = FakeOcrExtractor()

    extractor = create_extractor(
        image_content_type=ImageContentType.PHOTO,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    unit = result.units[0]

    assert unit.ocr_used is False

    assert unit.extraction_method == (
        ExtractionMethod.NATIVE
    )

    assert ocr.call_count == 0

    image_blocks = [
        block
        for block in unit.blocks
        if block.type == DocumentBlockType.IMAGE
    ]

    assert len(image_blocks) == 1

    assert image_blocks[0].image_content_type == (
        ImageContentType.PHOTO
    )


def test_graphic_does_not_trigger_ocr():

    image = create_test_image()

    pdf = create_pdf(
        image_bytes=image
    )

    ocr = FakeOcrExtractor()

    extractor = create_extractor(
        image_content_type=ImageContentType.GRAPHIC,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    unit = result.units[0]

    assert unit.ocr_used is False

    assert ocr.call_count == 0

    image_blocks = [
        block
        for block in unit.blocks
        if block.type == DocumentBlockType.IMAGE
    ]

    assert len(image_blocks) == 1

    assert image_blocks[0].image_content_type == (
        ImageContentType.GRAPHIC
    )


def test_mixed_image_triggers_ocr():

    image = create_test_image()

    pdf = create_pdf(
        image_bytes=image
    )

    ocr = FakeOcrExtractor(
        text="TEXTO DENTRO DE IMAGEM MISTA"
    )

    extractor = create_extractor(
        image_content_type=ImageContentType.MIXED,
        ocr_extractor=ocr
    )

    result = extractor.extract(
        pdf
    )

    unit = result.units[0]

    assert unit.ocr_used is True

    assert unit.extraction_method == (
        ExtractionMethod.OCR
    )

    assert (
        "TEXTO DENTRO DE IMAGEM MISTA"
        in unit.text
    )

    assert ocr.call_count == 1


def test_extract_image_stores_image():

    storage = MongoStorage(
        database_name="ai_document_extractor_test"
    )

    image_storage_service = ImageStorageService(
        storage
    )

    image = create_test_image()

    pdf = create_pdf(
        image_bytes=image
    )

    pdf_document = pymupdf.open(
        stream=pdf,
        filetype="pdf"
    )

    try:

        expected_image = (
            pdf_document[0]
            .get_text("dict")["blocks"][0]["image"]
        )

        ocr = FakeOcrExtractor()

        extractor = create_extractor(
            image_content_type=ImageContentType.PHOTO,
            ocr_extractor=ocr,
            image_storage_service=image_storage_service,
        )

        result = extractor.extract(
            pdf
        )

        unit = result.units[0]

        image_blocks = [
            block
            for block in unit.blocks
            if block.type == DocumentBlockType.IMAGE
        ]

        assert len(image_blocks) == 1

        image_block = image_blocks[0]

        assert image_block.image_id is not None

        assert image_block.image_url is not None

        assert (
            image_block.image_url
            == f"/images/{image_block.image_id}"
        )

        stored_image = (
            image_storage_service.get(
                image_block.image_id
            )
        )

        assert stored_image.read() == expected_image

        assert (
            stored_image.content_type
            == "image/png"
        )

    finally:

        if image_blocks:
            for block in image_blocks:
                if block.image_id:
                    image_storage_service.delete(
                        block.image_id
                    )

        pdf_document.close()

        storage.close()