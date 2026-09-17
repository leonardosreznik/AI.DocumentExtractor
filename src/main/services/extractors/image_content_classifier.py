from src.main.models.enums import ImageContentType
from src.main.models.response import ImageTextAnalysis


class ImageContentClassifier:

    def classify(
        self,
        analysis: ImageTextAnalysis
    ) -> ImageContentType:

        if analysis.component_count == 0:
            return ImageContentType.UNKNOWN

        if self._looks_like_graphic(analysis):
            return ImageContentType.GRAPHIC

        if self._looks_like_text(analysis):
            return ImageContentType.TEXT

        return ImageContentType.UNKNOWN

    @staticmethod
    def _looks_like_text(
        analysis: ImageTextAnalysis
    ) -> bool:

        return (
            analysis.component_density < 0.002
            and
            analysis.average_component_area < 250
            and
            analysis.small_component_ratio > 0.5
        )

    @staticmethod
    def _looks_like_graphic(
        analysis: ImageTextAnalysis
    ) -> bool:

        return (
            analysis.average_component_area > 250
            or
            analysis.horizontal_projection_variance > 0.005
        )