from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from src.main.services.extractors.ocr_extractor import (
    OcrExtractor,
)


def create_test_image() -> bytes:

    image = Image.new(
        "RGB",
        (1000, 300),
        "white"
    )

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(
        "C:/Windows/Fonts/arial.ttf",
        48
    )

    draw.text(
        (50, 100),
        "CERTIDAO DE TESTE",
        fill="black",
        font=font
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


def test_extract_text_from_image():

    image_bytes = create_test_image()

    extractor = OcrExtractor()

    text = extractor.extract(
        image_bytes
    )

    normalized_text = " ".join(
        text.upper().split()
    )

    assert "CERTIDAO" in normalized_text
    assert "DE" in normalized_text
    assert "TESTE" in normalized_text