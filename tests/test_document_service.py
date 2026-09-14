import base64

from src.main.models.request import DocumentExtractionRequest
from src.main.services.document_service import DocumentService
from src.main.services.extractors.resolver import ExtractorResolver
from src.main.services.extractors.txt import TxtExtractor


def test_extract_txt():

    text = "Olá, este é um documento de teste."

    content_base64 = base64.b64encode(
        text.encode("utf-8")
    ).decode("utf-8")

    request = DocumentExtractionRequest(
        file_name="teste.txt",
        content_type="text/plain",
        content_base64=content_base64
    )

    resolver = ExtractorResolver([
        TxtExtractor()
    ])

    service = DocumentService(resolver)

    response = service.extract(request)

    assert response.document.file_name == "teste.txt"
    assert response.document.format == "txt"
    assert response.document.size_bytes == len(text.encode("utf-8"))

    assert len(response.units) == 1
    assert response.units[0].text == text
    assert response.units[0].search_text == text
    assert response.units[0].ocr_used is False