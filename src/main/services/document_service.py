import base64
import hashlib
from typing import Final

from src.main.models.enums import DocumentFormat
from src.main.models.request import DocumentExtractionRequest
from src.main.models.response import DocumentExtractionResponse, DocumentMetadata
from src.main.services.extractors.resolver import ExtractorResolver


EXTRACTOR_VERSION: Final[str] = "1.0.0"


class DocumentService:

    def __init__(self, resolver: ExtractorResolver):
        self._resolver = resolver

    def extract(
        self,
        request: DocumentExtractionRequest
    ) -> DocumentExtractionResponse:

        content = self._decode_base64(request.content_base64)

        document_format = self._get_document_format(
            request.content_type,
            request.file_name
        )

        sha256 = hashlib.sha256(content).hexdigest()

        extractor = self._resolver.resolve(
            request.content_type,
            request.file_name
        )

        extraction_result = extractor.extract(content)

        metadata = DocumentMetadata(
            file_name=request.file_name,
            content_type=request.content_type,
            format=document_format,
            size_bytes=len(content),
            sha256=sha256,
            unit_count=len(extraction_result.units),
            ocr_used=extraction_result.ocr_used,
            extraction_method=extraction_result.extraction_method,
            extractor_version=EXTRACTOR_VERSION,
        )

        return DocumentExtractionResponse(
            document=metadata,
            units=extraction_result.units,
        )

    @staticmethod
    def _decode_base64(value: str) -> bytes:

        try:
            return base64.b64decode(
                value,
                validate=True
            )
        except Exception as exc:
            raise ValueError(
                "Invalid Base64 content."
            ) from exc

    @staticmethod
    def _get_document_format(
        content_type: str,
        file_name: str
    ) -> DocumentFormat:

        content_type = content_type.lower()
        file_name = file_name.lower()

        if content_type == "text/plain" or file_name.endswith(".txt"):
            return DocumentFormat.TXT

        if content_type == "application/pdf" or file_name.endswith(".pdf"):
            return DocumentFormat.PDF

        if content_type.startswith("image/"):
            return DocumentFormat.IMAGE

        return DocumentFormat.UNKNOWN