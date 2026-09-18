from fastapi import APIRouter

from src.main.dependencies import (
    get_image_storage_service,
)

from src.main.models.request import (
    DocumentExtractionRequest,
)

from src.main.models.response import (
    DocumentExtractionResponse,
)

from src.main.services.document_service import (
    DocumentService,
)

from src.main.services.extractors.resolver import (
    ExtractorResolver,
)

from src.main.services.extractors.txt import (
    TxtExtractor,
)

from src.main.services.extractors.pdf import (
    PdfExtractor,
)

from src.main.services.extractors.page_content_detector import (
    PageContentDetector,
)

from src.main.services.extractors.image_text_analyzer import (
    ImageTextAnalyzer,
)

from src.main.services.extractors.image_content_classifier import (
    ImageContentClassifier,
)

from src.main.services.extractors.ocr_detector import (
    OcrDetector,
)

from src.main.services.extractors.ocr_extractor import (
    OcrExtractor,
)


documents_routes = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


page_content_detector = (
    PageContentDetector()
)

image_text_analyzer = (
    ImageTextAnalyzer()
)

image_content_classifier = (
    ImageContentClassifier()
)

ocr_detector = (
    OcrDetector()
)

ocr_extractor = (
    OcrExtractor()
)

image_storage_service = (
    get_image_storage_service()
)


pdf_extractor = PdfExtractor(
    page_content_detector=page_content_detector,
    image_text_analyzer=image_text_analyzer,
    image_content_classifier=image_content_classifier,
    ocr_detector=ocr_detector,
    ocr_extractor=ocr_extractor,
    image_storage_service=image_storage_service,
)


resolver = ExtractorResolver([
    TxtExtractor(),
    pdf_extractor,
])


document_service = DocumentService(
    resolver
)


@documents_routes.post(
    "/extract",
    response_model=DocumentExtractionResponse
)
def extract_document(
    request: DocumentExtractionRequest
):

    return document_service.extract(
        request
    )