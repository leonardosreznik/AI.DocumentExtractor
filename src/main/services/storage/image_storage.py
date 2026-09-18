from datetime import datetime, timedelta, timezone

from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


class ImageStorageService:

    IMAGE_TTL_HOURS = 48

    def __init__(
        self,
        storage: MongoStorage,
    ):

        self._storage = storage

    def save(
        self,
        image_bytes: bytes,
        content_type: str,
        file_name: str | None = None,
        metadata: dict | None = None,
    ) -> str:

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                hours=self.IMAGE_TTL_HOURS
            )
        )

        return self._storage.save_image(
            image_bytes=image_bytes,
            content_type=content_type,
            file_name=file_name,
            metadata=metadata,
            expires_at=expires_at,
        )

    def get(
        self,
        image_id: str,
    ):

        return self._storage.get_image(
            image_id
        )

    def delete(
        self,
        image_id: str,
    ) -> None:

        self._storage.delete_image(
            image_id
        )