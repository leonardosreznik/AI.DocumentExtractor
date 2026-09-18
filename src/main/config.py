import os


class Settings:

    MONGO_CONNECTION_STRING = os.getenv(
        "MONGO_CONNECTION_STRING",
        "mongodb://localhost:27017"
    )

    MONGO_DATABASE_NAME = os.getenv(
        "MONGO_DATABASE_NAME",
        "ai_document_extractor"
    )


settings = Settings()