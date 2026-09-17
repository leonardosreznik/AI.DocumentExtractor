import cv2
import numpy as np

from src.main.models.response import ImageTextAnalysis


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
                vertical_spacing_std=0.0
            )

        height, width = image.shape

        # ---------------------------------------------------------
        # 1. Detecção de bordas
        # ---------------------------------------------------------

        edges = cv2.Canny(
            image,
            100,
            200
        )

        edge_pixels = np.count_nonzero(
            edges
        )

        total_pixels = height * width

        edge_density = (
            edge_pixels / total_pixels
        )

        # ---------------------------------------------------------
        # 2. Componentes conectados
        # ---------------------------------------------------------

        component_count, _, stats, _ = (
            cv2.connectedComponentsWithStats(
                edges,
                connectivity=8
            )
        )

        # O componente 0 representa o fundo.
        component_count -= 1

        component_density = (
            component_count / total_pixels
        )

        # ---------------------------------------------------------
        # 3. Estatísticas dos componentes
        # ---------------------------------------------------------

        if component_count > 0:

            component_stats = stats[1:]

            tops = component_stats[
                :,
                cv2.CC_STAT_TOP
            ]

            lefts = component_stats[
                :,
                cv2.CC_STAT_LEFT
            ]

            component_widths = component_stats[
                :,
                cv2.CC_STAT_WIDTH
            ]

            component_heights = component_stats[
                :,
                cv2.CC_STAT_HEIGHT
            ]

            component_areas = component_stats[
                :,
                cv2.CC_STAT_AREA
            ]

            average_component_width = float(
                np.mean(
                    component_widths
                )
            )

            average_component_height = float(
                np.mean(
                    component_heights
                )
            )

            average_component_area = float(
                np.mean(
                    component_areas
                )
            )

            small_components = (
                component_areas < 200
            )

            small_component_ratio = float(
                np.mean(
                    small_components
                )
            )

            # -----------------------------------------------------
            # 4. Agrupamentos verticais
            # -----------------------------------------------------

            # Centro vertical de cada componente.
            centers_y = (
                tops +
                component_heights / 2
            )

            line_tolerance = max(
                5.0,
                average_component_height * 0.75
            )

            sorted_centers = np.sort(
                centers_y
            )

            vertical_groups = []

            current_group = [
                sorted_centers[0]
            ]

            for center in sorted_centers[1:]:

                if (
                    center -
                    np.mean(current_group)
                    <= line_tolerance
                ):

                    current_group.append(
                        center
                    )

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

            # Centro vertical de cada agrupamento.
            group_centers = np.array(
                [
                    np.mean(group)
                    for group in vertical_groups
                ]
            )

            vertical_group_count = len(
                group_centers
            )

            # -----------------------------------------------------
            # 5. Espaçamento vertical
            # -----------------------------------------------------

            if len(group_centers) > 1:

                vertical_spacings = np.diff(
                    group_centers
                )

                # Normalização pela altura da imagem.
                normalized_spacings = (
                    vertical_spacings / height
                )

                vertical_spacing_mean = float(
                    np.mean(
                        normalized_spacings
                    )
                )

                vertical_spacing_std = float(
                    np.std(
                        normalized_spacings
                    )
                )

            else:

                vertical_spacing_mean = 0.0
                vertical_spacing_std = 0.0

            # -----------------------------------------------------
            # 6. Cobertura horizontal
            # -----------------------------------------------------

            horizontal_start = np.min(
                lefts
            )

            horizontal_end = np.max(
                lefts + component_widths
            )

            horizontal_coverage = (
                horizontal_end -
                horizontal_start
            ) / width

            # -----------------------------------------------------
            # 7. Projeção horizontal
            # -----------------------------------------------------

            horizontal_projection = np.sum(
                edges > 0,
                axis=1
            )

            # Normalização pela largura.
            horizontal_projection = (
                horizontal_projection / width
            )

            horizontal_projection_variance = float(
                np.var(
                    horizontal_projection
                )
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

        # ---------------------------------------------------------
        # 8. Resultado
        # ---------------------------------------------------------

        return ImageTextAnalysis(
            has_text=False,
            confidence=0.0,

            edge_density=edge_density,

            component_count=component_count,

            average_component_width=(
                average_component_width
            ),

            average_component_height=(
                average_component_height
            ),

            average_component_area=(
                average_component_area
            ),

            small_component_ratio=(
                small_component_ratio
            ),

            component_density=(
                component_density
            ),

            vertical_group_count=(
                vertical_group_count
            ),

            horizontal_coverage=(
                horizontal_coverage
            ),

            horizontal_projection_variance=(
                horizontal_projection_variance
            ),

            vertical_spacing_mean=(
                vertical_spacing_mean
            ),

            vertical_spacing_std=(
                vertical_spacing_std
            )
        )