from pydantic import BaseModel, Field

from .enums import (
    DocumentBlockType,
    DocumentFormat,
    DocumentUnitType,
    ExtractionMethod,
    ImageContentType,
    PageContentType,
)


class DocumentLocation(BaseModel):

    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    section: str | None = None


class ImagePosition(BaseModel):

    x: float
    y: float
    width: float
    height: float


class DocumentBlock(BaseModel):

    type: DocumentBlockType

    text: str = ""

    confidence: float | None = None

    image_id: str | None = None

    image_url: str | None = None

    position: ImagePosition | None = None

    image_content_type: ImageContentType | None = None


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


class DetectedImage(BaseModel):

    index: int

    position: ImagePosition

    xref: int | None = None


class PageContentAnalysis(BaseModel):

    content_type: PageContentType

    has_text: bool

    has_images: bool

    images: list[DetectedImage] = Field(
        default_factory=list
    )


class ImageComponent(BaseModel):

    index: int

    x: float

    y: float

    width: float

    height: float

    area: float

    center_x: float

    center_y: float


class ImageTextAnalysis(BaseModel):

    has_text: bool

    confidence: float

    edge_density: float

    component_count: int

    average_component_width: float

    average_component_height: float

    average_component_area: float

    small_component_ratio: float

    component_density: float

    vertical_group_count: int

    horizontal_coverage: float

    horizontal_projection_variance: float

    vertical_spacing_mean: float

    vertical_spacing_std: float

    max_component_area_ratio: float

    max_component_width_ratio: float

    max_component_height_ratio: float

    components: list[ImageComponent] = Field(
        default_factory=list
    )