from src.main.services.extractors.base import DocumentExtractor


class ExtractorResolver:

    def __init__(self, extractors: list[DocumentExtractor]):
        self._extractors = extractors

    def resolve(
        self,
        content_type: str,
        file_name: str
    ) -> DocumentExtractor:

        for extractor in self._extractors:
            if extractor.can_handle(content_type, file_name):
                return extractor

        raise ValueError(
            f"No extractor found for content type: {content_type}"
        )