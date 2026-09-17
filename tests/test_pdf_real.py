from pathlib import Path

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


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf-exemplo-1.pdf"
)


def create_real_pdf_extractor() -> PdfExtractor:

    return PdfExtractor(
        page_content_detector=PageContentDetector(),
        image_text_analyzer=ImageTextAnalyzer(),
        image_content_classifier=ImageContentClassifier(),
        ocr_detector=OcrDetector(),
        ocr_extractor=OcrExtractor(),
    )


def test_extract_real_pdf():

    assert FIXTURE_PATH.exists()

    pdf_bytes = FIXTURE_PATH.read_bytes()

    extractor = create_real_pdf_extractor()

    result = extractor.extract(
        pdf_bytes
    )

    assert len(result.units) == 3

    for unit in result.units:

        print()
        print(
            f"Página {unit.location.page_number}"
        )

        print(
            f"Método: {unit.extraction_method}"
        )

        print(
            f"OCR utilizado: {unit.ocr_used}"
        )

        print(
            f"Texto: {unit.text[:500]}"
        )

        for block in unit.blocks:

            print(
                f"  Bloco: {block.type}"
            )

            if block.image_content_type:

                print(
                    "    Tipo da imagem: "
                    f"{block.image_content_type}"
                )

    assert result.ocr_used is True

    assert result.extraction_method in (
        ExtractionMethod.OCR,
        ExtractionMethod.HYBRID,
    )


def test_real_pdf_contains_images():

    pdf_bytes = FIXTURE_PATH.read_bytes()

    extractor = create_real_pdf_extractor()

    result = extractor.extract(
        pdf_bytes
    )

    for unit in result.units:

        image_blocks = [
            block
            for block in unit.blocks
            if block.type == DocumentBlockType.IMAGE
        ]

        assert len(image_blocks) >= 1


def test_real_pdf_extracts_ocr_text():

    pdf_bytes = FIXTURE_PATH.read_bytes()

    extractor = create_real_pdf_extractor()

    result = extractor.extract(
        pdf_bytes
    )

    all_text = "\n".join(
        unit.text
        for unit in result.units
    ).upper()

    assert (
        "BIRTH CERTIFICATE"
        in all_text
    )