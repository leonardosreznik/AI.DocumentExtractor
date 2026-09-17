from src.main.models.enums import ImageContentType
from src.main.models.response import ImageTextAnalysis
from src.main.services.extractors.image_content_classifier import (
    ImageContentClassifier,
)


def create_analysis(
    *,
    component_count: int,
    average_component_width: float,
    average_component_height: float,
    average_component_area: float,
    small_component_ratio: float,
    component_density: float,
    vertical_group_count: int,
    horizontal_coverage: float,
    horizontal_projection_variance: float,
    vertical_spacing_mean: float,
    vertical_spacing_std: float,
    edge_density: float = 0.0,
) -> ImageTextAnalysis:

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
    )


def test_text():

    analysis = create_analysis(
        component_count=24,
        average_component_width=12.45,
        average_component_height=14.66,
        average_component_area=55.37,
        small_component_ratio=1.0,
        component_density=0.0002,
        vertical_group_count=1,
        horizontal_coverage=0.69,
        horizontal_projection_variance=0.00204,
        vertical_spacing_mean=0.0,
        vertical_spacing_std=0.0,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.TEXT


def test_multi_line_text():

    analysis = create_analysis(
        component_count=131,
        average_component_width=12.03,
        average_component_height=14.16,
        average_component_area=53.33,
        small_component_ratio=1.0,
        component_density=0.000436,
        vertical_group_count=5,
        horizontal_coverage=0.573,
        horizontal_projection_variance=0.00260,
        vertical_spacing_mean=0.160,
        vertical_spacing_std=0.00108,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.TEXT


def test_small_dense_text():

    analysis = create_analysis(
        component_count=906,
        average_component_width=9.72,
        average_component_height=6.57,
        average_component_area=30.50,
        small_component_ratio=1.0,
        component_density=0.000888,
        vertical_group_count=35,
        horizontal_coverage=0.248,
        horizontal_projection_variance=0.00180,
        vertical_spacing_mean=0.0249,
        vertical_spacing_std=0.00010,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.TEXT


def test_table():

    analysis = create_analysis(
        component_count=121,
        average_component_width=56.64,
        average_component_height=26.37,
        average_component_area=166.36,
        small_component_ratio=0.843,
        component_density=0.000151,
        vertical_group_count=7,
        horizontal_coverage=0.854,
        horizontal_projection_variance=0.01217,
        vertical_spacing_mean=0.095,
        vertical_spacing_std=0.031,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.GRAPHIC


def test_drawing():

    analysis = create_analysis(
        component_count=4,
        average_component_width=211.0,
        average_component_height=161.0,
        average_component_area=694.5,
        small_component_ratio=0.0,
        component_density=0.000033,
        vertical_group_count=1,
        horizontal_coverage=0.77,
        horizontal_projection_variance=0.00716,
        vertical_spacing_mean=0.0,
        vertical_spacing_std=0.0,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.GRAPHIC


def test_texture():

    analysis = create_analysis(
        component_count=2360,
        average_component_width=5.23,
        average_component_height=5.31,
        average_component_area=12.91,
        small_component_ratio=0.999,
        component_density=0.01966,
        vertical_group_count=31,
        horizontal_coverage=1.0,
        horizontal_projection_variance=0.000695,
        vertical_spacing_mean=0.0327,
        vertical_spacing_std=0.00192,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result != ImageContentType.TEXT

def test_text_with_signature():

    analysis = create_analysis(
        component_count=36,
        average_component_width=36.13,
        average_component_height=15.11,
        average_component_area=116.41,
        small_component_ratio=0.944,
        component_density=0.000075,
        vertical_group_count=3,
        horizontal_coverage=0.675,
        horizontal_projection_variance=0.001869,
        vertical_spacing_mean=0.2565,
        vertical_spacing_std=0.1906,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.MIXED


def test_text_with_stamp():

    analysis = create_analysis(
        component_count=45,
        average_component_width=30.91,
        average_component_height=32.57,
        average_component_area=109.04,
        small_component_ratio=0.911,
        component_density=0.000080,
        vertical_group_count=2,
        horizontal_coverage=0.588,
        horizontal_projection_variance=0.000337,
        vertical_spacing_mean=0.4423,
        vertical_spacing_std=0.0,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.MIXED


def test_text_with_drawing():

    analysis = create_analysis(
        component_count=28,
        average_component_width=37.96,
        average_component_height=27.71,
        average_component_area=127.10,
        small_component_ratio=0.857,
        component_density=0.000233,
        vertical_group_count=2,
        horizontal_coverage=0.805,
        horizontal_projection_variance=0.008878,
        vertical_spacing_mean=0.3791,
        vertical_spacing_std=0.0,
    )

    classifier = ImageContentClassifier()

    result = classifier.classify(analysis)

    assert result == ImageContentType.MIXED    