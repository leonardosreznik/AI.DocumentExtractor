import cv2
import numpy as np

from src.main.services.extractors.image_text_analyzer import (
    ImageTextAnalyzer,
)


def create_image_bytes(image: np.ndarray) -> bytes:

    success, encoded = cv2.imencode(
        ".png",
        image
    )

    assert success

    return encoded.tobytes()


def print_result(label, result):

    print(
        f"\n{label}:",
        "edge_density =",
        result.edge_density,
        "component_count =",
        result.component_count,
        "avg_width =",
        result.average_component_width,
        "avg_height =",
        result.average_component_height,
        "avg_area =",
        result.average_component_area,
        "small_ratio =",
        result.small_component_ratio,
        "component_density =",
        result.component_density,
        "vertical_group_count =",
        result.vertical_group_count,
        "horizontal_coverage =",
        result.horizontal_coverage,
        "horizontal_projection_variance =",
        result.horizontal_projection_variance,
        "vertical_spacing_mean =",
        result.vertical_spacing_mean,
        "vertical_spacing_std =",
        result.vertical_spacing_std
    )

def print_component_statistics(label, result):
    if not result.components:
        return

    areas = np.array(
        [component.area for component in result.components],
        dtype=float,
    )

    widths = np.array(
        [component.width for component in result.components],
        dtype=float,
    )

    heights = np.array(
        [component.height for component in result.components],
        dtype=float,
    )

    print(f"\n=== STATISTICS: {label} ===")

    print("area:")
    print(f"  median = {np.median(areas):.2f}")
    print(f"  max    = {np.max(areas):.2f}")
    print(
        f"  ratio  = "
        f"{np.max(areas) / np.median(areas):.2f}"
    )

    print("width:")
    print(f"  median = {np.median(widths):.2f}")
    print(f"  max    = {np.max(widths):.2f}")
    print(
        f"  ratio  = "
        f"{np.max(widths) / np.median(widths):.2f}"
    )

    print("height:")
    print(f"  median = {np.median(heights):.2f}")
    print(f"  max    = {np.max(heights):.2f}")
    print(
        f"  ratio  = "
        f"{np.max(heights) / np.median(heights):.2f}"
    )    

def print_components(label, result):
    print(f"\n=== COMPONENTS: {label} ===")

    for component in result.components:
        print(
            f"index={component.index} "
            f"x={component.x:.1f} "
            f"y={component.y:.1f} "
            f"width={component.width:.1f} "
            f"height={component.height:.1f} "
            f"area={component.area:.1f} "
            f"center=({component.center_x:.1f}, "
            f"{component.center_y:.1f})"
        )    


def test_empty_image_does_not_have_text():

    image = np.full(
        (300, 400),
        255,
        dtype=np.uint8
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    assert result.has_text is False
    assert result.confidence == 0.0
    assert result.edge_density == 0.0
    assert result.component_count == 0
    assert result.vertical_group_count == 0


def test_image_with_text():

    image = np.full(
        (300, 400),
        255,
        dtype=np.uint8
    )

    cv2.putText(
        image,
        "Documento de teste",
        (30, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TEXT",
        result
    )

    assert result.edge_density > 0
    assert result.component_count > 0
    assert result.vertical_group_count > 0


def test_image_with_multiple_text_lines():

    image = np.full(
        (500, 600),
        255,
        dtype=np.uint8
    )

    lines = [
        "Processo Judicial",
        "Documento de teste",
        "Informacoes do processo",
        "Data de julgamento",
        "Resultado da decisao",
    ]

    y = 80

    for line in lines:

        cv2.putText(
            image,
            line,
            (40, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            0,
            2
        )

        y += 80

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "MULTI-LINE TEXT",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1


def test_image_with_small_dense_text():

    image = np.full(
        (1200, 850),
        255,
        dtype=np.uint8
    )

    y = 60

    for index in range(35):

        cv2.putText(
            image,
            f"Processo judicial documento linha {index + 1}",
            (50, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            0,
            1
        )

        y += 30

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "SMALL DENSE TEXT",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1


def test_image_with_spaced_text():

    image = np.full(
        (600, 800),
        255,
        dtype=np.uint8
    )

    lines = [
        "Processo Judicial",
        "Documento de teste",
        "Informacoes processuais",
        "Resultado da decisao",
    ]

    y = 80

    for line in lines:

        cv2.putText(
            image,
            line,
            (60, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            0,
            2
        )

        y += 130

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "SPACED TEXT",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1


def test_image_with_two_columns():

    image = np.full(
        (700, 1000),
        255,
        dtype=np.uint8
    )

    left_lines = [
        "Processo",
        "Interessado",
        "Matricula",
        "Admissao",
        "Aposentadoria",
        "Periodo",
    ]

    right_lines = [
        "Decisao",
        "Resultado",
        "Valor",
        "Correcao",
        "Juros",
        "Pagamento",
    ]

    y = 100

    for left, right in zip(
        left_lines,
        right_lines
    ):

        cv2.putText(
            image,
            left,
            (60, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            0,
            2
        )

        cv2.putText(
            image,
            right,
            (550, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            0,
            2
        )

        y += 80

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TWO COLUMNS",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1


def test_image_with_table():

    image = np.full(
        (800, 1000),
        255,
        dtype=np.uint8
    )

    # Texto da tabela.

    headers = [
        "Rubrica",
        "Mes",
        "Valor",
    ]

    cv2.putText(
        image,
        headers[0],
        (80, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        0,
        2
    )

    cv2.putText(
        image,
        headers[1],
        (400, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        0,
        2
    )

    cv2.putText(
        image,
        headers[2],
        (700, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        0,
        2
    )

    rows = [
        ("Salario", "01", "5000"),
        ("Salario", "02", "5200"),
        ("Diferenca", "03", "350"),
        ("Diferenca", "04", "410"),
    ]

    y = 180

    for rubric, month, value in rows:

        cv2.putText(
            image,
            rubric,
            (80, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            0,
            2
        )

        cv2.putText(
            image,
            month,
            (400, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            0,
            2
        )

        cv2.putText(
            image,
            value,
            (700, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            0,
            2
        )

        y += 90

    # Estrutura da tabela.

    cv2.rectangle(
        image,
        (50, 50),
        (900, 600),
        0,
        2
    )

    for x in [330, 620]:

        cv2.line(
            image,
            (x, 50),
            (x, 600),
            0,
            2
        )

    for y in [140, 230, 320, 410, 500]:

        cv2.line(
            image,
            (50, y),
            (900, y),
            0,
            2
        )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TABLE",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1


def test_image_with_signature():

    image = np.full(
        (600, 800),
        255,
        dtype=np.uint8
    )

    cv2.putText(
        image,
        "Documento para assinatura",
        (60, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )

    cv2.line(
        image,
        (100, 400),
        (600, 400),
        0,
        2
    )

    # Simula uma assinatura manuscrita.
    points = np.array(
        [
            [120, 380],
            [150, 350],
            [180, 390],
            [210, 340],
            [240, 385],
            [270, 345],
            [300, 380],
            [340, 330],
            [380, 375],
            [420, 340],
            [460, 370],
            [500, 350],
        ],
        dtype=np.int32
    )

    cv2.polylines(
        image,
        [points],
        False,
        0,
        3
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TEXT + SIGNATURE",
        result
    )

    print_component_statistics(
        "TEXT + SIGNATURE",
        result
    )

    print_components(
        "TEXT + SIGNATURE",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 0


def test_image_with_stamp():

    image = np.full(
        (700, 800),
        255,
        dtype=np.uint8
    )

    cv2.putText(
        image,
        "Documento aprovado",
        (60, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )

    # Simula um carimbo circular.

    cv2.circle(
        image,
        (400, 400),
        130,
        0,
        4
    )

    cv2.circle(
        image,
        (400, 400),
        100,
        0,
        2
    )

    cv2.putText(
        image,
        "APROVADO",
        (300, 410),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        0,
        2
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TEXT + STAMP",
        result
    )

    print_component_statistics(
        "TEXT + STAMP",
        result
    )

    print_components(
        "TEXT + STAMP",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 0


def test_image_with_drawing():

    image = np.full(
        (300, 400),
        255,
        dtype=np.uint8
    )

    cv2.rectangle(
        image,
        (50, 50),
        (350, 250),
        0,
        5
    )

    cv2.circle(
        image,
        (200, 150),
        60,
        0,
        5
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "DRAWING",
        result
    )

    assert result.edge_density > 0
    assert result.component_count > 0


def test_image_with_text_and_drawing():

    image = np.full(
        (300, 400),
        255,
        dtype=np.uint8
    )

    cv2.putText(
        image,
        "Documento de teste",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        0,
        2
    )

    cv2.rectangle(
        image,
        (50, 120),
        (350, 250),
        0,
        5
    )

    cv2.circle(
        image,
        (200, 185),
        40,
        0,
        5
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TEXT + DRAWING",
        result
    )

    print_components(
        "TEXT + DRAWING",
        result
    )

    print_component_statistics(
        "TEXT + DRAWING",
        result
    )   

    assert result.edge_density > 0
    assert result.component_count > 0
    assert result.vertical_group_count > 0


def test_image_with_texture():

    image = np.full(
        (300, 400),
        255,
        dtype=np.uint8
    )

    # Cria uma textura semelhante a uma fotografia,
    # sem inserir texto.
    rng = np.random.default_rng(42)

    noise = rng.normal(
        loc=0,
        scale=35,
        size=(300, 400)
    )

    image = np.clip(
        image.astype(np.float32) + noise,
        0,
        255
    ).astype(np.uint8)

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "TEXTURE",
        result
    )

    assert result.edge_density >= 0
    assert result.component_count >= 0


def test_text_at_different_scales():

    analyzer = ImageTextAnalyzer()

    scales = [
        (200, 300, 0.5),
        (300, 400, 1.0),
        (600, 800, 2.0),
        (900, 1200, 3.0)
    ]

    for height, width, scale in scales:

        image = np.full(
            (height, width),
            255,
            dtype=np.uint8
        )

        font_scale = 1.0 * scale

        thickness = max(
            1,
            int(2 * scale)
        )

        cv2.putText(
            image,
            "Documento de teste",
            (
                int(30 * scale),
                int(150 * scale)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            0,
            thickness
        )

        image_bytes = create_image_bytes(image)

        result = analyzer.analyze(image_bytes)

        print_result(
            f"SCALE {scale}",
            result
        )

        assert result.component_count > 0
        assert result.component_density > 0
        assert result.vertical_group_count > 0


def test_document_like_page():

    image = np.full(
        (1200, 850),
        255,
        dtype=np.uint8
    )

    cv2.putText(
        image,
        "PODER JUDICIARIO",
        (100, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        0,
        3
    )

    lines = [
        "Processo: 8011635-81.2025.8.05.0022",
        "Interessado: Ana Francisca de Santana Neta",
        "Matricula: 11200780",
        "Documento para analise",
        "Informacoes processuais",
        "Data de distribuicao: 17/08/2019",
        "Decisao judicial",
        "Valores e parametros",
        "Observacoes do processo",
        "Documento encerrado.",
    ]

    y = 220

    for line in lines:

        cv2.putText(
            image,
            line,
            (100, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            0,
            2
        )

        y += 70

    cv2.line(
        image,
        (100, 950),
        (750, 950),
        0,
        2
    )

    image_bytes = create_image_bytes(image)

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(image_bytes)

    print_result(
        "DOCUMENT-LIKE PAGE",
        result
    )

    assert result.component_count > 0
    assert result.vertical_group_count > 1

def test_components_are_extracted():

    image = np.zeros(
        (200, 300),
        dtype=np.uint8
    )

    cv2.rectangle(
        image,
        (50, 40),
        (100, 80),
        255,
        -1
    )

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(
        create_image_bytes(image)
    )

    assert result.component_count > 0
    assert len(result.components) == result.component_count

    for component in result.components:
        assert component.width > 0
        assert component.height > 0
        assert component.area > 0


def test_component_coordinates_are_consistent():

    image = np.zeros(
        (200, 300),
        dtype=np.uint8
    )

    cv2.rectangle(
        image,
        (50, 40),
        (100, 80),
        255,
        -1
    )

    analyzer = ImageTextAnalyzer()

    result = analyzer.analyze(
        create_image_bytes(image)
    )

    assert len(result.components) > 0

    component = result.components[0]

    assert component.x >= 0
    assert component.y >= 0

    assert component.center_x == (
        component.x + component.width / 2
    )

    assert component.center_y == (
        component.y + component.height / 2
    )    