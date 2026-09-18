from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


def test_save_get_and_delete_image():

    storage = MongoStorage(
        database_name="ai_document_extractor_test"
    )

    image_bytes = b"fake-image-content"

    image_id = storage.save_image(
        image_bytes=image_bytes,
        content_type="image/png",
        file_name="test.png",
    )

    try:

        stored_image = storage.get_image(
            image_id
        )

        assert stored_image.read() == image_bytes

        assert (
            stored_image.content_type
            == "image/png"
        )

        assert (
            stored_image.filename
            == "test.png"
        )

    finally:

        storage.delete_image(
            image_id
        )

        storage.close()