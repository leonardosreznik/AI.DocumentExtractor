from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
import re
import unicodedata

import pytesseract
from PIL import Image


class OcrExtractor:

    TESSERACT_PATH = Path(
        "C:/Program Files/Tesseract-OCR/tesseract.exe"
    )

    LANGUAGE = "por"

    PRIMARY_PSM = 3

    SECONDARY_PSM = 11

    MIN_SECONDARY_LINE_LENGTH = 3

    DUPLICATE_SIMILARITY_THRESHOLD = 0.85

    def __init__(self):

        if not self.TESSERACT_PATH.exists():

            raise FileNotFoundError(
                "Tesseract OCR não encontrado em: "
                f"{self.TESSERACT_PATH}"
            )

        pytesseract.pytesseract.tesseract_cmd = (
            str(
                self.TESSERACT_PATH
            )
        )

    def extract(
        self,
        image_bytes: bytes
    ) -> str:

        if not image_bytes:
            return ""

        image = Image.open(
            BytesIO(image_bytes)
        )

        try:

            primary_lines = (
                self._extract_lines(
                    image=image,
                    psm=self.PRIMARY_PSM,
                )
            )

            secondary_lines = (
                self._extract_lines(
                    image=image,
                    psm=self.SECONDARY_PSM,
                )
            )

            lines = (
                self._merge_lines(
                    primary_lines=primary_lines,
                    secondary_lines=secondary_lines,
                )
            )

            return "\n".join(
                line["text"]
                for line in lines
                if line["text"]
            ).strip()

        finally:

            image.close()

    def _extract_lines(
        self,
        image: Image.Image,
        psm: int,
    ) -> list[dict]:

        data = pytesseract.image_to_data(
            image,
            lang=self.LANGUAGE,
            config=f"--psm {psm}",
            output_type=pytesseract.Output.DICT,
        )

        lines: dict[tuple, dict] = {}

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

            if confidence < 0:
                continue

            block_number = (
                data["block_num"][index]
            )

            paragraph_number = (
                data["par_num"][index]
            )

            line_number = (
                data["line_num"][index]
            )

            key = (
                block_number,
                paragraph_number,
                line_number,
            )

            if key not in lines:

                lines[key] = {
                    "text": text,
                    "top": float(
                        data["top"][index]
                    ),
                    "confidence": confidence,
                }

            else:

                lines[key]["text"] = (
                    f'{lines[key]["text"]} '
                    f'{text}'
                )

                lines[key]["confidence"] = (
                    (
                        lines[key]["confidence"]
                        + confidence
                    )
                    / 2
                )

                lines[key]["top"] = min(
                    lines[key]["top"],
                    float(
                        data["top"][index]
                    ),
                )

        return list(
            lines.values()
        )

    def _merge_lines(
        self,
        primary_lines: list[dict],
        secondary_lines: list[dict],
    ) -> list[dict]:

        merged = [
            dict(line)
            for line in primary_lines
        ]

        for secondary_line in secondary_lines:

            text = secondary_line[
                "text"
            ].strip()

            if len(text) < (
                self.MIN_SECONDARY_LINE_LENGTH
            ):
                continue

            if self._is_duplicate(
                text,
                merged,
            ):
                continue

            merged.append(
                dict(
                    secondary_line
                )
            )

        merged.sort(
            key=lambda line: (
                line["top"],
                -line["confidence"],
            )
        )

        return merged

    def _is_duplicate(
        self,
        text: str,
        existing_lines: list[dict],
    ) -> bool:

        for existing_line in existing_lines:

            similarity = (
                self._calculate_similarity(
                    text,
                    existing_line["text"],
                )
            )

            if similarity >= (
                self.DUPLICATE_SIMILARITY_THRESHOLD
            ):
                return True

        return False

    @staticmethod
    def _calculate_similarity(
        first: str,
        second: str,
    ) -> float:

        first_normalized = (
            OcrExtractor._normalize_text(
                first
            )
        )

        second_normalized = (
            OcrExtractor._normalize_text(
                second
            )
        )

        if not first_normalized or not second_normalized:
            return 0.0

        return SequenceMatcher(
            None,
            first_normalized,
            second_normalized,
        ).ratio()

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        text = text.upper()

        text = (
            unicodedata.normalize(
                "NFD",
                text,
            )
        )

        text = "".join(
            character
            for character in text
            if unicodedata.category(
                character
            ) != "Mn"
        )

        return re.sub(
            r"[^A-Z0-9]+",
            "",
            text,
        )