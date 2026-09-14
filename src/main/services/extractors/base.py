from abc import ABC, abstractmethod

from src.main.models.response import ExtractionResult


class DocumentExtractor(ABC):

    @abstractmethod
    def can_handle(
        self,
        content_type: str,
        file_name: str
    ) -> bool:
        pass

    @abstractmethod
    def extract(
        self,
        content: bytes
    ) -> ExtractionResult:
        pass