import pymupdf

from src.main.models.enums import PageContentType
from src.main.services.extractors.page_content_detector import (
    PageContentDetector,
)


def create_test_pdf() -> bytes:

    document = pymupdf.open()

    # Página 1: somente texto
    page = document.new_page()

    page.insert_text(
        (50, 50),
        "Esta página possui somente texto nativo."
    )

    # Página 2: somente imagem
    page = document.new_page()

    image = pymupdf.Pixmap(
        pymupdf.csRGB,
        pymupdf.Rect(0, 0, 200, 100),
        False
    )

    image.clear_with(255)

    page.insert_image(
        pymupdf.Rect(50, 50, 250, 150),
        pixmap=image
    )

    # Página 3: texto + imagem
    page = document.new_page()

    page.insert_text(
        (50, 50),
        "Texto antes da imagem."
    )

    page.insert_image(
        pymupdf.Rect(50, 100, 250, 200),
        pixmap=image
    )

    # Página 4: imagem + texto
    page = document.new_page()

    page.insert_image(
        pymupdf.Rect(50, 50, 250, 150),
        pixmap=image
    )

    page.insert_text(
        (50, 200),
        "Texto depois da imagem."
    )

    # Página 5: vazia
    document.new_page()

    pdf_bytes = document.tobytes()

    document.close()

    return pdf_bytes


def test_page_content_detector():

    pdf_bytes = create_test_pdf()

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    detector = PageContentDetector()

    # Página 1
    result = detector.analyze(document[0])

    assert result.content_type == PageContentType.TEXT
    assert result.has_text is True
    assert result.has_images is False
    assert len(result.images) == 0

    # Página 2
    result = detector.analyze(document[1])

    assert result.content_type == PageContentType.IMAGE
    assert result.has_text is False
    assert result.has_images is True
    assert len(result.images) == 1
    
    image = result.images[0]

    assert image.position.x == 50
    assert image.position.y == 50
    assert image.position.width == 200
    assert image.position.height == 100
    # Página 3
    result = detector.analyze(document[2])

    assert result.content_type == PageContentType.TEXT_AND_IMAGE
    assert result.has_text is True
    assert result.has_images is True
    assert len(result.images) == 1

    # Página 4
    result = detector.analyze(document[3])

    assert result.content_type == PageContentType.TEXT_AND_IMAGE
    assert result.has_text is True
    assert result.has_images is True
    assert len(result.images) == 1

    # Página 5
    result = detector.analyze(document[4])

    assert result.content_type == PageContentType.EMPTY
    assert result.has_text is False
    assert result.has_images is False
    assert len(result.images) == 0

    document.close()