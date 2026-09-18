from functools import lru_cache

from src.main.services.storage.image_storage import (
    ImageStorageService,
)
from src.main.services.storage.mongo_storage import (
    MongoStorage,
)


@lru_cache
def get_mongo_storage() -> MongoStorage:

    return MongoStorage()


@lru_cache
def get_image_storage_service() -> ImageStorageService:

    return ImageStorageService(
        get_mongo_storage()
    )