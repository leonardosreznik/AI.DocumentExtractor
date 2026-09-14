from fastapi import APIRouter

from src.main.models.request import DocumentExtractionRequest
from src.main.models.response import DocumentExtractionResponse
from src.main.services.document_service import DocumentService
from src.main.services.extractors.resolver import ExtractorResolver
from src.main.services.extractors.txt import TxtExtractor
from src.main.services.extractors.pdf import PdfExtractor


documents_routes = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


resolver = ExtractorResolver([
    TxtExtractor(),
    PdfExtractor()
])

document_service = DocumentService(resolver)


@documents_routes.post(
    "/extract",
    response_model=DocumentExtractionResponse
)
def extract_document(
    request: DocumentExtractionRequest
):
    return document_service.extract(request)