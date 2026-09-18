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

    MIN_SECONDARY_CONFIDENCE = 30.0

    MIN_SECONDARY_LINE_LENGTH = 3

    DUPLICATE_SIMILARITY_THRESHOLD = 0.85

    LINE_VERTICAL_TOLERANCE = 10

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

            left = float(
                data["left"][index]
            )

            top = float(
                data["top"][index]
            )

            width = float(
                data["width"][index]
            )

            height = float(
                data["height"][index]
            )

            if key not in lines:

                lines[key] = {
                    "text": text,
                    "confidence": confidence,
                    "left": left,
                    "top": top,
                    "right": left + width,
                    "bottom": top + height,
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

                lines[key]["left"] = min(
                    lines[key]["left"],
                    left,
                )

                lines[key]["top"] = min(
                    lines[key]["top"],
                    top,
                )

                lines[key]["right"] = max(
                    lines[key]["right"],
                    left + width,
                )

                lines[key]["bottom"] = max(
                    lines[key]["bottom"],
                    top + height,
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

            text = (
                secondary_line["text"]
                .strip()
            )

            if len(text) < (
                self.MIN_SECONDARY_LINE_LENGTH
            ):
                continue

            if (
                secondary_line["confidence"]
                < self.MIN_SECONDARY_CONFIDENCE
            ):
                continue

            if self._overlaps_existing_line(
                secondary_line,
                merged,
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

    def _overlaps_existing_line(
        self,
        candidate: dict,
        existing_lines: list[dict],
    ) -> bool:

        for existing_line in existing_lines:

            if self._lines_overlap(
                candidate,
                existing_line,
            ):
                return True

        return False

    @classmethod
    def _lines_overlap(
        cls,
        first: dict,
        second: dict,
    ) -> bool:

        vertical_overlap = (
            cls._calculate_overlap(
                first["top"],
                first["bottom"],
                second["top"],
                second["bottom"],
            )
        )

        if vertical_overlap > 0:
            return True

        first_center = (
            first["top"]
            + first["bottom"]
        ) / 2

        second_center = (
            second["top"]
            + second["bottom"]
        ) / 2

        return (
            abs(
                first_center
                - second_center
            )
            <= cls.LINE_VERTICAL_TOLERANCE
        )

    @staticmethod
    def _calculate_overlap(
        first_start: float,
        first_end: float,
        second_start: float,
        second_end: float,
    ) -> float:

        intersection_start = max(
            first_start,
            second_start,
        )

        intersection_end = min(
            first_end,
            second_end,
        )

        if intersection_end <= intersection_start:
            return 0.0

        intersection = (
            intersection_end
            - intersection_start
        )

        first_size = (
            first_end
            - first_start
        )

        second_size = (
            second_end
            - second_start
        )

        smallest_size = min(
            first_size,
            second_size,
        )

        if smallest_size <= 0:
            return 0.0

        return (
            intersection
            / smallest_size
        )

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

        if (
            not first_normalized
            or not second_normalized
        ):
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