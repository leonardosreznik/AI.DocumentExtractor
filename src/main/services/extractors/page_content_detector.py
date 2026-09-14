import pymupdf

from src.main.models.enums import PageContentType
from src.main.models.response import (
    DetectedImage,
    ImagePosition,
    PageContentAnalysis,
)


class PageContentDetector:

    def analyze(
        self,
        page: pymupdf.Page
    ) -> PageContentAnalysis:

        text = page.get_text("text")

        has_text = bool(text.strip())

        blocks = page.get_text("dict")["blocks"]

        images: list[DetectedImage] = []

        for index, block in enumerate(blocks):

            if block.get("type") != 1:
                continue

            bbox = block.get("bbox")

            if not bbox:
                continue

            x0, y0, x1, y1 = bbox

            images.append(
                DetectedImage(
                    index=index,
                    position=ImagePosition(
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                        height=y1 - y0
                    )
                )
            )

        has_images = len(images) > 0

        if has_text and has_images:
            content_type = PageContentType.TEXT_AND_IMAGE

        elif has_text:
            content_type = PageContentType.TEXT

        elif has_images:
            content_type = PageContentType.IMAGE

        else:
            content_type = PageContentType.EMPTY

        return PageContentAnalysis(
            content_type=content_type,
            has_text=has_text,
            has_images=has_images,
            images=images
        )