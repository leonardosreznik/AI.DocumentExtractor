from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    DOC = "doc"
    DOCX = "docx"
    PPT = "ppt"
    PPTX = "pptx"
    XLS = "xls"
    XLSX = "xlsx"
    CSV = "csv"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ExtractionMethod(str, Enum):
    NATIVE = "native"
    OCR = "ocr"
    HYBRID = "hybrid"


class DocumentUnitType(str, Enum):
    DOCUMENT = "document"
    PAGE = "page"
    SLIDE = "slide"
    SHEET = "sheet"
    SECTION = "section"


class DocumentBlockType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    UNKNOWN = "unknown"

class PageContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TEXT_AND_IMAGE = "text_and_image"
    EMPTY = "empty"

        