from dataclasses import dataclass
from datetime import datetime, timezone

from bson import Binary, ObjectId
from pymongo import MongoClient

from src.main.config import settings


@dataclass
class StoredImage:

    data: bytes
    content_type: str
    filename: str | None
    metadata: dict

    def read(self) -> bytes:

        return self.data


class MongoStorage:

    COLLECTION_NAME = "document_images"

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
    ):

        self._client = MongoClient(
            connection_string
            or settings.MONGO_CONNECTION_STRING
        )

        self._database = (
            self._client[
                database_name
                or settings.MONGO_DATABASE_NAME
            ]
        )

        self._collection = (
            self._database[
                self.COLLECTION_NAME
            ]
        )

        self._ensure_indexes()

    def _ensure_indexes(self) -> None:

        self._collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="document_images_ttl",
        )

    def save_image(
        self,
        image_bytes: bytes,
        content_type: str,
        file_name: str | None = None,
        metadata: dict | None = None,
        expires_at: datetime | None = None,
    ) -> str:

        if not image_bytes:
            raise ValueError(
                "Os bytes da imagem não podem estar vazios."
            )

        if not content_type:
            raise ValueError(
                "O content_type da imagem é obrigatório."
            )

        document = {
            "data": Binary(image_bytes),
            "content_type": content_type,
            "filename": file_name,
            "metadata": (
                metadata.copy()
                if metadata
                else {}
            ),
            "created_at": datetime.now(
                timezone.utc
            ),
        }

        if expires_at is not None:

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            document["expires_at"] = expires_at

        result = self._collection.insert_one(
            document
        )

        return str(result.inserted_id)

    def get_image(
        self,
        image_id: str,
    ) -> StoredImage:

        object_id = ObjectId(
            image_id
        )

        document = (
            self._collection.find_one(
                {
                    "_id": object_id
                }
            )
        )

        if document is None:
            raise FileNotFoundError(
                f"Imagem não encontrada: {image_id}"
            )

        return StoredImage(
            data=bytes(
                document["data"]
            ),
            content_type=document[
                "content_type"
            ],
            filename=document.get(
                "filename"
            ),
            metadata=document.get(
                "metadata",
                {},
            ),
        )

    def delete_image(
        self,
        image_id: str,
    ) -> None:

        object_id = ObjectId(
            image_id
        )

        self._collection.delete_one(
            {
                "_id": object_id
            }
        )

    def close(self) -> None:

        self._client.close()