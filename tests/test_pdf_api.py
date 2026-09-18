"""
Teste manual da API do AI.DocumentExtractor.

Uso:

    python tests/test_pdf_api.py

O script:

    - lê o PDF informado;
    - descobre pelo OpenAPI o formato do DocumentExtractionRequest;
    - envia POST /documents/extract;
    - salva a resposta JSON;
    - encontra todos os image_id/image_url dos blocos;
    - faz GET /images/{image_id};
    - utiliza o filename retornado pela API;
    - salva todas as imagens;
    - cria um manifest com o resultado de cada download.

Não é um teste pytest automático.
É um utilitário para testes manuais de documentos reais.
"""

import base64
import json
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_BASE_URL = "http://localhost:8031"

PDF_PATH = Path(
    r"D:\AI.DocumentExtractor\dip1.pdf"
)

OUTPUT_ROOT = Path(
    r"D:\AI.DocumentExtractor\results"
)

REQUEST_TIMEOUT_SECONDS = 300


# ============================================================
# HTTP
# ============================================================

def http_request(
    url: str,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str | None = None,
) -> tuple[int, dict[str, str], bytes]:

    headers = {}

    if content_type:
        headers["Content-Type"] = content_type

    request = Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )

    try:

        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:

            response_headers = {
                key.lower(): value
                for key, value in response.headers.items()
            }

            return (
                response.status,
                response_headers,
                response.read(),
            )

    except HTTPError as error:

        error_body = error.read()

        print(
            f"\nHTTP {error.code} em {method} {url}"
        )

        if error_body:

            try:

                print(
                    json.dumps(
                        json.loads(
                            error_body.decode("utf-8")
                        ),
                        indent=4,
                        ensure_ascii=False,
                    )
                )

            except Exception:

                print(
                    error_body.decode(
                        "utf-8",
                        errors="replace",
                    )
                )

        raise

    except URLError as error:

        raise RuntimeError(
            f"Não foi possível acessar a API: {url}\n"
            f"Erro: {error}"
        ) from error


# ============================================================
# OPENAPI
# ============================================================

def get_openapi_schema() -> dict:

    status, _, body = http_request(
        f"{API_BASE_URL}/openapi.json"
    )

    if status != 200:
        raise RuntimeError(
            f"OpenAPI retornou HTTP {status}."
        )

    return json.loads(
        body.decode("utf-8")
    )


def resolve_schema(
    schema: dict,
    openapi: dict,
) -> dict:

    if "$ref" not in schema:
        return schema

    ref = schema["$ref"]

    prefix = "#/components/schemas/"

    if not ref.startswith(prefix):
        return schema

    schema_name = ref[len(prefix):]

    return (
        openapi
        .get("components", {})
        .get("schemas", {})
        .get(schema_name, {})
    )


def resolve_request_properties(
    openapi: dict,
) -> dict:

    path = (
        openapi
        .get("paths", {})
        .get("/documents/extract")
    )

    if not path:
        raise RuntimeError(
            "A rota POST /documents/extract "
            "não foi encontrada no OpenAPI."
        )

    post = path.get("post")

    if not post:
        raise RuntimeError(
            "A rota /documents/extract "
            "não possui operação POST."
        )

    request_body = post.get("requestBody")

    if not request_body:
        raise RuntimeError(
            "POST /documents/extract "
            "não possui requestBody."
        )

    content = request_body.get(
        "content",
        {}
    )

    application_json = content.get(
        "application/json"
    )

    if not application_json:
        raise RuntimeError(
            "O endpoint não declara "
            "application/json no requestBody."
        )

    schema = resolve_schema(
        application_json.get(
            "schema",
            {}
        ),
        openapi,
    )

    return schema.get(
        "properties",
        {}
    )


# ============================================================
# REQUEST
# ============================================================

def detect_request_fields(
    properties: dict,
) -> tuple[str, str, str]:

    file_name_field = None
    content_type_field = None
    content_field = None

    for field_name in properties:

        normalized = field_name.lower()

        if normalized in (
            "file_name",
            "filename",
            "name",
        ):
            file_name_field = field_name

        elif normalized in (
            "content_type",
            "mimetype",
            "mime_type",
        ):
            content_type_field = field_name

        elif (
            "base64" in normalized
            or normalized in (
                "content",
                "data",
                "file",
                "document",
            )
        ):
            content_field = field_name

    if not file_name_field:
        raise RuntimeError(
            "Não foi possível identificar o campo "
            "de nome do arquivo no "
            "DocumentExtractionRequest."
        )

    if not content_type_field:
        raise RuntimeError(
            "Não foi possível identificar o campo "
            "content_type no "
            "DocumentExtractionRequest."
        )

    if not content_field:
        raise RuntimeError(
            "Não foi possível identificar o campo "
            "que recebe o conteúdo do documento no "
            "DocumentExtractionRequest."
        )

    return (
        file_name_field,
        content_type_field,
        content_field,
    )


def build_request(
    pdf_path: Path,
    openapi: dict,
) -> dict:

    properties = resolve_request_properties(
        openapi
    )

    (
        file_name_field,
        content_type_field,
        content_field,
    ) = detect_request_fields(
        properties
    )

    pdf_bytes = pdf_path.read_bytes()

    encoded_content = base64.b64encode(
        pdf_bytes
    ).decode("ascii")

    content_type = (
        mimetypes.guess_type(
            pdf_path.name
        )[0]
        or "application/pdf"
    )

    payload = {
        file_name_field: pdf_path.name,
        content_type_field: content_type,
        content_field: encoded_content,
    }

    print(
        "\nCampos detectados no "
        "DocumentExtractionRequest:"
    )

    print(
        f"  nome:         {file_name_field}"
    )

    print(
        f"  content-type: {content_type_field}"
    )

    print(
        f"  conteúdo:     {content_field}"
    )

    return payload


# ============================================================
# IMAGENS
# ============================================================

def get_header(
    headers: dict[str, str],
    name: str,
) -> str | None:

    return headers.get(
        name.lower()
    )


def get_image_extension(
    content_type: str,
) -> str:

    normalized_content_type = (
        content_type
        .split(";")[0]
        .strip()
        .lower()
    )

    extension = mimetypes.guess_extension(
        normalized_content_type
    )

    if extension:
        return extension

    content_type_extensions = {
        "image/jpeg": ".jpeg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/jp2": ".jp2",
        "image/jpx": ".jpx",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }

    return content_type_extensions.get(
        normalized_content_type,
        ".bin",
    )


def get_filename_from_content_disposition(
    content_disposition: str | None,
) -> str | None:

    if not content_disposition:
        return None

    match = re.search(
        r'filename="([^"]+)"',
        content_disposition,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    match = re.search(
        r"filename=([^;]+)",
        content_disposition,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def find_images(
    response: dict,
) -> list[dict]:

    images = []

    for unit in response.get(
        "units",
        []
    ):

        page_number = (
            unit
            .get("location", {})
            .get("page_number")
        )

        blocks = unit.get(
            "blocks",
            []
        )

        for block_index, block in enumerate(
            blocks,
            start=1
        ):

            if block.get("type") != "image":
                continue

            image_id = block.get(
                "image_id"
            )

            image_url = block.get(
                "image_url"
            )

            if not image_id:
                continue

            images.append({
                "page_number": page_number,
                "block_index": block_index,
                "image_id": image_id,
                "image_url": image_url,
            })

    return images


def download_images(
    response: dict,
    output_directory: Path,
) -> list[dict]:

    images_directory = (
        output_directory / "images"
    )

    images_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_items = find_images(
        response
    )

    manifest = []

    print(
        f"\nImagens encontradas: "
        f"{len(image_items)}"
    )

    for index, item in enumerate(
        image_items,
        start=1
    ):

        image_id = item["image_id"]

        image_url = item["image_url"]

        if not image_url:
            image_url = (
                f"/images/{image_id}"
            )

        if image_url.startswith("/"):
            image_url = (
                f"{API_BASE_URL.rstrip('/')}"
                f"{image_url}"
            )

        print(
            f"  [{index}/{len(image_items)}] "
            f"GET {image_url}"
        )

        status, headers, body = http_request(
            image_url
        )

        content_type = (
            get_header(
                headers,
                "content-type",
            )
            or "application/octet-stream"
        )

        content_disposition = (
            get_header(
                headers,
                "content-disposition",
            )
        )

        api_filename = (
            get_filename_from_content_disposition(
                content_disposition
            )
        )

        if api_filename:

            file_name = api_filename

        else:

            extension = get_image_extension(
                content_type
            )

            page_number = (
                item["page_number"]
                or 0
            )

            file_name = (
                f"page_{page_number:03d}"
                f"_image_{index:03d}"
                f"_{image_id}"
                f"{extension}"
            )

        image_path = (
            images_directory / file_name
        )

        image_path.write_bytes(
            body
        )

        manifest.append({
            **item,
            "status": status,
            "content_type": content_type,
            "content_disposition": (
                content_disposition
            ),
            "filename": file_name,
            "size_bytes": len(body),
            "file": str(
                image_path
            ),
        })

        print(
            f"       Content-Type: "
            f"{content_type}"
        )

        print(
            f"       Filename: "
            f"{file_name}"
        )

        print(
            f"       OK: "
            f"{len(body):,} bytes"
        )

    return manifest


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"PDF não encontrado:\n{PDF_PATH}"
        )

    if PDF_PATH.suffix.lower() != ".pdf":
        raise ValueError(
            f"O arquivo informado não é PDF:\n{PDF_PATH}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_directory = (
        OUTPUT_ROOT
        / f"{PDF_PATH.stem}_{timestamp}"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print(
        "AI.DocumentExtractor - "
        "teste de PDF"
    )
    print("=" * 70)

    print(
        f"\nPDF:\n{PDF_PATH}"
    )

    print(
        f"\nSaída:\n{output_directory}"
    )

    # --------------------------------------------------------
    # 1. Descobrir contrato da API
    # --------------------------------------------------------

    print(
        "\n[1/4] Consultando OpenAPI..."
    )

    openapi = get_openapi_schema()

    # --------------------------------------------------------
    # 2. Montar e enviar request
    # --------------------------------------------------------

    print(
        "\n[2/4] Enviando PDF para extração..."
    )

    payload = build_request(
        PDF_PATH,
        openapi,
    )

    request_body = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    status, _, response_body = http_request(
        f"{API_BASE_URL}/documents/extract",
        method="POST",
        body=request_body,
        content_type="application/json",
    )

    if status != 200:
        raise RuntimeError(
            f"Extração retornou HTTP {status}."
        )

    response = json.loads(
        response_body.decode("utf-8")
    )

    # --------------------------------------------------------
    # 3. Salvar JSON
    # --------------------------------------------------------

    print(
        "\n[3/4] Salvando JSON..."
    )

    json_path = (
        output_directory / "response.json"
    )

    json_path.write_text(
        json.dumps(
            response,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"  JSON: {json_path}"
    )

    # --------------------------------------------------------
    # 4. Baixar imagens
    # --------------------------------------------------------

    print(
        "\n[4/4] Baixando imagens..."
    )

    manifest = download_images(
        response,
        output_directory,
    )

    manifest_path = (
        output_directory
        / "images_manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Resumo
    # --------------------------------------------------------

    document = response.get(
        "document",
        {}
    )

    units = response.get(
        "units",
        []
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "TESTE CONCLUÍDO"
    )

    print(
        "=" * 70
    )

    print(
        f"\nDocumento: "
        f"{document.get('file_name', PDF_PATH.name)}"
    )

    print(
        f"Páginas/unidades: "
        f"{len(units)}"
    )

    print(
        f"Método: "
        f"{document.get('extraction_method')}"
    )

    print(
        f"OCR utilizado: "
        f"{document.get('ocr_used')}"
    )

    print(
        f"Imagens baixadas: "
        f"{len(manifest)}"
    )

    print(
        f"\nPasta de resultado:\n"
        f"{output_directory}"
    )

    print(
        f"\nJSON:\n"
        f"{json_path}"
    )

    print(
        f"\nManifest das imagens:\n"
        f"{manifest_path}"
    )


if __name__ == "__main__":
    main()