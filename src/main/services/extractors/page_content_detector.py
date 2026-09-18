import pymupdf

from src.main.models.enums import PageContentType
from src.main.models.response import (
    DetectedImage,
    ImagePosition,
    PageContentAnalysis,
)


class PageContentDetector:

    IMAGE_BLOCK_TYPE = 1

    def analyze(
        self,
        page: pymupdf.Page
    ) -> PageContentAnalysis:

        text = page.get_text(
            "text"
        )

        has_text = bool(
            text.strip()
        )

        images: list[DetectedImage] = []

        self._detect_block_images(
            page=page,
            images=images,
        )

        self._detect_embedded_images(
            page=page,
            images=images,
        )

        has_images = bool(
            images
        )

        if has_text and has_images:

            content_type = (
                PageContentType.TEXT_AND_IMAGE
            )

        elif has_text:

            content_type = (
                PageContentType.TEXT
            )

        elif has_images:

            content_type = (
                PageContentType.IMAGE
            )

        else:

            content_type = (
                PageContentType.EMPTY
            )

        return PageContentAnalysis(
            content_type=content_type,
            has_text=has_text,
            has_images=has_images,
            images=images,
        )

    def _detect_block_images(
        self,
        page: pymupdf.Page,
        images: list[DetectedImage],
    ) -> None:

        blocks = page.get_text(
            "dict"
        ).get(
            "blocks",
            []
        )

        for block in blocks:

            if block.get(
                "type"
            ) != self.IMAGE_BLOCK_TYPE:
                continue

            bbox = block.get(
                "bbox"
            )

            if not bbox:
                continue

            position = (
                self._create_position(
                    bbox
                )
            )

            if self._contains_position(
                images,
                position,
            ):
                continue

            images.append(
                DetectedImage(
                    index=len(images),
                    position=position,
                    xref=None,
                )
            )

    def _detect_embedded_images(
        self,
        page: pymupdf.Page,
        images: list[DetectedImage],
    ) -> None:

        embedded_images = (
            page.get_images(
                full=True
            )
        )

        for image in embedded_images:

            xref = image[0]

            rectangles = (
                page.get_image_rects(
                    xref
                )
            )

            for rectangle in rectangles:

                position = (
                    self._create_position(
                        (
                            rectangle.x0,
                            rectangle.y0,
                            rectangle.x1,
                            rectangle.y1,
                        )
                    )
                )

                if self._contains_position(
                    images,
                    position,
                ):
                    continue

                images.append(
                    DetectedImage(
                        index=len(images),
                        position=position,
                        xref=xref,
                    )
                )

    @staticmethod
    def _create_position(
        bbox: tuple
    ) -> ImagePosition:

        x0, y0, x1, y1 = bbox

        return ImagePosition(
            x=float(x0),
            y=float(y0),
            width=float(x1 - x0),
            height=float(y1 - y0),
        )

    @staticmethod
    def _contains_position(
        images: list[DetectedImage],
        position: ImagePosition,
    ) -> bool:

        tolerance = 0.01

        for image in images:

            existing = image.position

            if (
                abs(
                    existing.x - position.x
                ) <= tolerance
                and
                abs(
                    existing.y - position.y
                ) <= tolerance
                and
                abs(
                    existing.width - position.width
                ) <= tolerance
                and
                abs(
                    existing.height - position.height
                ) <= tolerance
            ):
                return True

        return False