from pydantic import BaseModel, Field


class DocumentExtractionRequest(BaseModel):
    file_name: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)