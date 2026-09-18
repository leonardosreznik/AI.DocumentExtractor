from pathlib import Path
import sys

import pymupdf
import pytesseract
from PIL import Image
from io import BytesIO


TESSERACT_PATH = Path(
    "C:/Program Files/Tesseract-OCR/tesseract.exe"
)

LANGUAGE = "por"

PSM_VALUES = (
    3,
    6,
    11,
    12,
)


def configure_tesseract() -> None:

    if not TESSERACT_PATH.exists():

        raise FileNotFoundError(
            "Tesseract OCR não encontrado em: "
            f"{TESSERACT_PATH}"
        )

    pytesseract.pytesseract.tesseract_cmd = (
        str(TESSERACT_PATH)
    )


def extract_first_image(
    pdf_path: Path,
) -> tuple[bytes, str]:

    document = pymupdf.open(
        pdf_path
    )

    try:

        for page in document:

            images = page.get_images(
                full=True
            )

            for image in images:

                xref = image[0]

                extracted = (
                    document.extract_image(
                        xref
                    )
                )

                image_bytes = extracted.get(
                    "image"
                )

                extension = extracted.get(
                    "ext",
                    "bin"
                )

                if image_bytes:

                    return (
                        image_bytes,
                        extension,
                    )

    finally:

        document.close()

    raise RuntimeError(
        "Nenhuma imagem incorporada "
        "foi encontrada no PDF."
    )


def extract_ocr_data(
    image: Image.Image,
    psm: int,
) -> list[dict]:

    data = pytesseract.image_to_data(
        image,
        lang=LANGUAGE,
        config=f"--psm {psm}",
        output_type=pytesseract.Output.DICT,
    )

    results = []

    count = len(
        data.get(
            "text",
            []
        )
    )

    for index in range(count):

        text = (
            data["text"][index]
            or ""
        ).strip()

        if not text:
            continue

        try:

            confidence = float(
                data["conf"][index]
            )

        except (
            ValueError,
            TypeError,
        ):

            confidence = 0.0

        results.append({
            "text": text,
            "confidence": confidence,
            "left": data["left"][index],
            "top": data["top"][index],
            "width": data["width"][index],
            "height": data["height"][index],
            "block": data["block_num"][index],
            "paragraph": data["par_num"][index],
            "line": data["line_num"][index],
        })

    return results


def print_results(
    psm: int,
    results: list[dict],
) -> None:

    print()
    print("=" * 90)
    print(
        f"PSM {psm}"
    )
    print("=" * 90)

    if not results:

        print(
            "Nenhum texto encontrado."
        )

        return

    for item in results:

        print(
            f"{item['text']:<35} "
            f"conf={item['confidence']:>6.2f} "
            f"x={item['left']:>4} "
            f"y={item['top']:>4} "
            f"w={item['width']:>4} "
            f"h={item['height']:>4} "
            f"block={item['block']} "
            f"par={item['paragraph']} "
            f"line={item['line']}"
        )


def print_lines(
    psm: int,
    results: list[dict],
) -> None:

    lines = {}

    for item in results:

        key = (
            item["block"],
            item["paragraph"],
            item["line"],
        )

        if key not in lines:

            lines[key] = {
                "text": item["text"],
                "top": item["top"],
                "confidence": item["confidence"],
            }

        else:

            lines[key]["text"] += (
                f" {item['text']}"
            )

            lines[key]["confidence"] = (
                (
                    lines[key]["confidence"]
                    + item["confidence"]
                )
                / 2
            )

    print()
    print(
        f"Linhas PSM {psm}:"
    )

    for line in sorted(
        lines.values(),
        key=lambda item: item["top"],
    ):

        print(
            f"y={line['top']:>4} "
            f"conf={line['confidence']:>6.2f} "
            f"| {line['text']}"
        )


def main() -> None:

    configure_tesseract()

    if len(sys.argv) < 2:

        print(
            "Uso:"
        )

        print(
            "python tests/ocr_diagnostic.py "
            "\"D:\\caminho\\arquivo.pdf\""
        )

        return

    pdf_path = Path(
        sys.argv[1]
    )

    if not pdf_path.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n"
            f"{pdf_path}"
        )

    print(
        "=" * 90
    )

    print(
        "DIAGNÓSTICO OCR"
    )

    print(
        "=" * 90
    )

    print(
        f"\nPDF:\n{pdf_path}"
    )

    image_bytes, extension = (
        extract_first_image(
            pdf_path
        )
    )

    print(
        f"\nImagem encontrada:"
    )

    print(
        f"  extensão: {extension}"
    )

    print(
        f"  bytes:    {len(image_bytes):,}"
    )

    image = Image.open(
        BytesIO(image_bytes)
    )

    print(
        f"  tamanho:  "
        f"{image.width} x {image.height}"
    )

    print(
        f"  modo:     {image.mode}"
    )

    try:

        for psm in PSM_VALUES:

            results = extract_ocr_data(
                image=image,
                psm=psm,
            )

            print_results(
                psm=psm,
                results=results,
            )

            print_lines(
                psm=psm,
                results=results,
            )

    finally:

        image.close()


if __name__ == "__main__":
    main()