from datetime import datetime, timezone

from bson import ObjectId

from src.main.services.storage.image_storage import (
    ImageStorageService,
)
from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


def test_save_get_and_delete_image():

    storage = MongoStorage(
        database_name="ai_document_extractor_test"
    )

    service = ImageStorageService(
        storage
    )

    image_bytes = b"fake-image-content"

    image_id = service.save(
        image_bytes=image_bytes,
        content_type="image/png",
        file_name="test.png",
    )

    try:

        stored_image = service.get(
            image_id
        )

        assert stored_image.read() == (
            image_bytes
        )

        assert (
            stored_image.content_type
            == "image/png"
        )

        assert (
            stored_image.filename
            == "test.png"
        )

        document = (
            storage._collection.find_one(
                {
                    "_id": ObjectId(image_id)
                }
            )
        )

        assert document is not None

        assert "expires_at" in document

        assert isinstance(
            document["expires_at"],
            datetime
        )

        expires_at = document["expires_at"]

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        assert expires_at > datetime.now(
            timezone.utc
        )

    finally:

        storage.delete_image(
            image_id
        )

        storage.close()


def test_get_image_metadata():

    storage = MongoStorage(
        database_name="ai_document_extractor_test"
    )

    service = ImageStorageService(
        storage
    )

    image_bytes = b"fake-image-content"

    image_id = service.save(
        image_bytes=image_bytes,
        content_type="image/jpeg",
        file_name="document-page.jpg",
        metadata={
            "document_id": "123",
            "page_number": 2,
        },
    )

    try:

        metadata = (
            storage.get_image_metadata(
                image_id
            )
        )

        assert metadata.image_id == image_id

        assert (
            metadata.content_type
            == "image/jpeg"
        )

        assert (
            metadata.filename
            == "document-page.jpg"
        )

        assert (
            metadata.metadata["document_id"]
            == "123"
        )

        assert (
            metadata.metadata["page_number"]
            == 2
        )

        assert isinstance(
            metadata.created_at,
            datetime
        )

        assert isinstance(
            metadata.expires_at,
            datetime
        )

        expires_at = metadata.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        assert expires_at > datetime.now(
            timezone.utc
        )

    finally:

        service.get(
            image_id
        )

        storage.delete_image(
            image_id
        )

        storage.close()