"""Explicit source and normalization errors."""


class SourceReadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ObservationNormalizationError(Exception):
    def __init__(self, code: str, message: str, *, observation_id: str | None = None, source_record_id: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.observation_id = observation_id
        self.source_record_id = source_record_id
