from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main.dependencies import (
    get_image_storage_service,
)
from src.main.routes.images import (
    images_routes,
)
from src.main.services.storage.image_storage import (
    ImageStorageService,
)
from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


storage = MongoStorage(
    database_name="ai_document_extractor_test"
)

image_storage_service = ImageStorageService(
    storage
)

app = FastAPI()

app.include_router(
    images_routes
)

app.dependency_overrides[
    get_image_storage_service
] = lambda: image_storage_service

client = TestClient(app)


def test_get_image():

    image_bytes = b"fake-image-content"

    image_id = image_storage_service.save(
        image_bytes=image_bytes,
        content_type="image/png",
        file_name="test.png",
    )

    try:

        response = client.get(
            f"/images/{image_id}"
        )

        assert response.status_code == 200

        assert response.content == image_bytes

        assert (
            response.headers["content-type"]
            == "image/png"
        )

    finally:

        image_storage_service.delete(
            image_id
        )


def test_get_image_not_found():

    response = client.get(
        "/images/68ffffffffffffffffffffffff"
    )

    assert response.status_code == 404


def teardown_module():

    storage.close()