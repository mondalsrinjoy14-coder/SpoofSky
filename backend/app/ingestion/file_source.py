"""Bounded local fixture source; no network fallback is performed."""

import json
from pathlib import Path

from pydantic import ValidationError

from backend.app.domain.models import FixtureDocument
from backend.app.ingestion.errors import SourceReadError


class FileFixtureSource:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> FixtureDocument:
        if not self.path.is_file():
            raise SourceReadError("source_not_found", f"Fixture source does not exist: {self.path.name}")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            raise SourceReadError("source_unreadable", "Fixture source could not be read") from exc
        except json.JSONDecodeError as exc:
            raise SourceReadError("source_invalid_json", f"Fixture source is not valid JSON at line {exc.lineno}") from exc

        try:
            return FixtureDocument.model_validate(payload)
        except ValidationError as exc:
            first_error = exc.errors()[0]
            location = ".".join(str(item) for item in first_error.get("loc", [])) or "document"
            raise SourceReadError("source_schema_invalid", f"Fixture source field {location} is invalid") from exc
