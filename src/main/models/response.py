from pydantic import BaseModel, Field

from .enums import (
    DocumentBlockType,
    DocumentFormat,
    DocumentUnitType,
    ExtractionMethod,
    PageContentType
)


class DocumentLocation(BaseModel):
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    section: str | None = None


class DocumentBlock(BaseModel):
    type: DocumentBlockType
    text: str = ""
    confidence: float | None = None


class DocumentUnit(BaseModel):
    index: int
    type: DocumentUnitType

    location: DocumentLocation

    text: str = ""
    search_text: str = ""

    extraction_method: ExtractionMethod
    ocr_used: bool = False

    blocks: list[DocumentBlock] = Field(
        default_factory=list
    )


class ExtractionResult(BaseModel):
    units: list[DocumentUnit] = Field(
        default_factory=list
    )

    extraction_method: ExtractionMethod
    ocr_used: bool = False


class DocumentMetadata(BaseModel):
    file_name: str
    content_type: str
    format: DocumentFormat

    size_bytes: int
    sha256: str

    unit_count: int | None = None

    ocr_used: bool = False
    extraction_method: ExtractionMethod

    extractor_version: str


class DocumentExtractionResponse(BaseModel):
    document: DocumentMetadata

    units: list[DocumentUnit] = Field(
        default_factory=list
    )

class ImagePosition(BaseModel):
    x: float
    y: float
    width: float
    height: float

class DetectedImage(BaseModel):
    index: int
    position: ImagePosition

class PageContentAnalysis(BaseModel):
    content_type: PageContentType

    has_text: bool
    has_images: bool

    images: list[DetectedImage] = Field(
        default_factory=list
    )            