from src.main.services.extractors.pdf import PdfExtractor

from src.main.services.extractors.page_content_detector import (
    PageContentDetector,
)

from src.main.models.enums import (
    DocumentUnitType,
    ExtractionMethod,
)


def test_extract_pdf():
    extractor = PdfExtractor(
        PageContentDetector()
    )

    assert extractor.can_handle(
        "application/pdf",
        "teste.pdf"
    )

    # PDF mínimo de teste
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 300 300] "
        b"/Contents 4 0 R >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length 44 >>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"50 250 Td\n"
        b"(Documento de teste) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"trailer\n"
        b"<< /Root 1 0 R >>\n"
        b"%%EOF"
    )

    result = extractor.extract(content)

    assert len(result.units) == 1

    unit = result.units[0]

    assert unit.index == 0
    assert unit.type == DocumentUnitType.PAGE
    assert unit.location.page_number == 1

    assert unit.extraction_method == ExtractionMethod.NATIVE
    assert unit.ocr_used is False

    assert "Documento de teste" in unit.text
    assert unit.search_text == unit.text