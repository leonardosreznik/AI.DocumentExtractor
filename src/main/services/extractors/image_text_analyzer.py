import cv2
import numpy as np

from src.main.models.response import (
    ImageComponent,
    ImageTextAnalysis,
)


class ImageTextAnalyzer:

    def analyze(
        self,
        image_bytes: bytes
    ) -> ImageTextAnalysis:

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            return ImageTextAnalysis(
                has_text=False,
                confidence=0.0,
                edge_density=0.0,
                component_count=0,
                average_component_width=0.0,
                average_component_height=0.0,
                average_component_area=0.0,
                small_component_ratio=0.0,
                component_density=0.0,
                vertical_group_count=0,
                horizontal_coverage=0.0,
                horizontal_projection_variance=0.0,
                vertical_spacing_mean=0.0,
                vertical_spacing_std=0.0,
                max_component_area_ratio=0.0,
                max_component_width_ratio=0.0,
                max_component_height_ratio=0.0,
                components=[]
            )

        height, width = image.shape

        edges = cv2.Canny(
            image,
            100,
            200
        )

        edge_pixels = np.count_nonzero(edges)
        total_pixels = height * width

        edge_density = edge_pixels / total_pixels

        component_count, _, stats, _ = (
            cv2.connectedComponentsWithStats(
                edges,
                connectivity=8
            )
        )

        component_count -= 1

        component_density = component_count / total_pixels

        components: list[ImageComponent] = []

        if component_count > 0:

            component_stats = stats[1:]

            tops = component_stats[:, cv2.CC_STAT_TOP]
            lefts = component_stats[:, cv2.CC_STAT_LEFT]
            component_widths = component_stats[:, cv2.CC_STAT_WIDTH]
            component_heights = component_stats[:, cv2.CC_STAT_HEIGHT]
            component_areas = component_stats[:, cv2.CC_STAT_AREA]

            median_component_area = float(
                np.median(component_areas)
            )

            median_component_width = float(
                np.median(component_widths)
            )

            median_component_height = float(
                np.median(component_heights)
            )

            max_component_area_ratio = (
                float(np.max(component_areas))
                / median_component_area
                if median_component_area > 0
                else 0.0
            )

            max_component_width_ratio = (
                float(np.max(component_widths))
                / median_component_width
                if median_component_width > 0
                else 0.0
            )

            max_component_height_ratio = (
                float(np.max(component_heights))
                / median_component_height
                if median_component_height > 0
                else 0.0
            )

            # Componentes espaciais individuais
            for index in range(component_count):

                x = float(lefts[index])
                y = float(tops[index])

                component_width = float(
                    component_widths[index]
                )

                component_height = float(
                    component_heights[index]
                )

                area = float(
                    component_areas[index]
                )

                components.append(
                    ImageComponent(
                        index=index,
                        x=x,
                        y=y,
                        width=component_width,
                        height=component_height,
                        area=area,
                        center_x=x + component_width / 2,
                        center_y=y + component_height / 2,
                    )
                )

            average_component_width = float(
                np.mean(component_widths)
            )

            average_component_height = float(
                np.mean(component_heights)
            )

            average_component_area = float(
                np.mean(component_areas)
            )

            small_components = component_areas < 200

            small_component_ratio = float(
                np.mean(small_components)
            )

            centers_y = tops + component_heights / 2

            line_tolerance = max(
                5.0,
                average_component_height * 0.75
            )

            sorted_centers = np.sort(centers_y)

            vertical_groups = []

            current_group = [
                sorted_centers[0]
            ]

            for center in sorted_centers[1:]:

                if (
                    center - np.mean(current_group)
                    <= line_tolerance
                ):
                    current_group.append(center)

                else:
                    vertical_groups.append(
                        current_group
                    )

                    current_group = [
                        center
                    ]

            vertical_groups.append(
                current_group
            )

            group_centers = np.array([
                np.mean(group)
                for group in vertical_groups
            ])

            vertical_group_count = len(
                group_centers
            )

            if len(group_centers) > 1:

                vertical_spacings = np.diff(
                    group_centers
                )

                normalized_spacings = (
                    vertical_spacings / height
                )

                vertical_spacing_mean = float(
                    np.mean(normalized_spacings)
                )

                vertical_spacing_std = float(
                    np.std(normalized_spacings)
                )

            else:

                vertical_spacing_mean = 0.0
                vertical_spacing_std = 0.0

            horizontal_start = np.min(
                lefts
            )

            horizontal_end = np.max(
                lefts + component_widths
            )

            horizontal_coverage = (
                horizontal_end - horizontal_start
            ) / width

            horizontal_projection = np.sum(
                edges > 0,
                axis=1
            )

            horizontal_projection = (
                horizontal_projection / width
            )

            horizontal_projection_variance = float(
                np.var(horizontal_projection)
            )

        else:

            average_component_width = 0.0
            average_component_height = 0.0
            average_component_area = 0.0
            small_component_ratio = 0.0
            vertical_group_count = 0
            horizontal_coverage = 0.0
            horizontal_projection_variance = 0.0
            vertical_spacing_mean = 0.0
            vertical_spacing_std = 0.0

            max_component_area_ratio = 0.0
            max_component_width_ratio = 0.0
            max_component_height_ratio = 0.0

        return ImageTextAnalysis(
            has_text=False,
            confidence=0.0,
            edge_density=edge_density,
            component_count=component_count,
            average_component_width=average_component_width,
            average_component_height=average_component_height,
            average_component_area=average_component_area,
            small_component_ratio=small_component_ratio,
            component_density=component_density,
            vertical_group_count=vertical_group_count,
            horizontal_coverage=horizontal_coverage,
            horizontal_projection_variance=horizontal_projection_variance,
            vertical_spacing_mean=vertical_spacing_mean,
            vertical_spacing_std=vertical_spacing_std,
            max_component_area_ratio=max_component_area_ratio,
            max_component_width_ratio=max_component_width_ratio,
            max_component_height_ratio=max_component_height_ratio,
            components=components
        )