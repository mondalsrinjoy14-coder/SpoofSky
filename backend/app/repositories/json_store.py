"""File persistence for the fixture-first ingestion stage."""

import json
from pathlib import Path
import re

from backend.app.domain.models import IngestionReport


class JsonObservationStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def save(self, report: IngestionReport) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", report.dataset_id):
            raise ValueError("dataset_id contains unsafe filename characters")
        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"{report.dataset_id}.json"
        payload = report.model_dump(mode="json")
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return destination

    def load(self, dataset_id: str) -> IngestionReport | None:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", dataset_id):
            raise ValueError("dataset_id contains unsafe filename characters")
        source = self.directory / f"{dataset_id}.json"
        if not source.is_file():
            return None
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
            return IngestionReport.model_validate(payload)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("stored dataset is unreadable or invalid") from exc
