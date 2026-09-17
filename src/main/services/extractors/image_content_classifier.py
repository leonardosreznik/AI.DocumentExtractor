from src.main.models.enums import ImageContentType
from src.main.models.response import ImageTextAnalysis


class ImageContentClassifier:

    MAX_TEXT_COMPONENT_DENSITY = 0.002

    MAX_TEXT_AVERAGE_COMPONENT_AREA = 250

    MIN_TEXT_SMALL_COMPONENT_RATIO = 0.5

    MIN_GEOMETRIC_RATIO = 10.0

    MIN_GRAPHIC_PROJECTION_VARIANCE = 0.005

    def classify(
        self,
        analysis: ImageTextAnalysis
    ) -> ImageContentType:

        if analysis.component_count == 0:
            return ImageContentType.UNKNOWN

        if self._looks_like_mixed(
            analysis
        ):
            return ImageContentType.MIXED

        if self._looks_like_graphic(
            analysis
        ):
            return ImageContentType.GRAPHIC

        if self._looks_like_text(
            analysis
        ):
            return ImageContentType.TEXT

        return ImageContentType.UNKNOWN

    @classmethod
    def _looks_like_text(
        cls,
        analysis: ImageTextAnalysis
    ) -> bool:

        return (
            analysis.component_density
            < cls.MAX_TEXT_COMPONENT_DENSITY
            and
            analysis.average_component_area
            < cls.MAX_TEXT_AVERAGE_COMPONENT_AREA
            and
            analysis.small_component_ratio
            > cls.MIN_TEXT_SMALL_COMPONENT_RATIO
        )

    @classmethod
    def _looks_like_mixed(
        cls,
        analysis: ImageTextAnalysis
    ) -> bool:

        has_text = cls._looks_like_text(
            analysis
        )

        has_geometrically_dominant_component = (
            analysis.max_component_area_ratio
            >= cls.MIN_GEOMETRIC_RATIO
            or
            analysis.max_component_width_ratio
            >= cls.MIN_GEOMETRIC_RATIO
            or
            analysis.max_component_height_ratio
            >= cls.MIN_GEOMETRIC_RATIO
        )

        return (
            has_text
            and
            has_geometrically_dominant_component
        )

    @classmethod
    def _looks_like_graphic(
        cls,
        analysis: ImageTextAnalysis
    ) -> bool:

        has_large_components = (
            analysis.average_component_area
            > cls.MAX_TEXT_AVERAGE_COMPONENT_AREA
        )

        has_structured_graphic_pattern = (
            analysis.horizontal_projection_variance
            > cls.MIN_GRAPHIC_PROJECTION_VARIANCE
        )

        has_high_component_density = (
            analysis.component_density
            >= cls.MAX_TEXT_COMPONENT_DENSITY
        )

        return (
            has_large_components
            or
            has_structured_graphic_pattern
            or
            has_high_component_density
        )