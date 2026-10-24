import json

import pytest

from backend.app.ingestion.errors import SourceReadError
from backend.app.ingestion.file_source import FileFixtureSource


def test_missing_fixture_is_a_meaningful_source_failure(tmp_path) -> None:
    with pytest.raises(SourceReadError) as error:
        FileFixtureSource(tmp_path / "missing.json").load()

    assert error.value.code == "source_not_found"


def test_invalid_json_is_a_meaningful_source_failure(tmp_path) -> None:
    source = tmp_path / "broken.json"
    source.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SourceReadError) as error:
        FileFixtureSource(source).load()

    assert error.value.code == "source_invalid_json"


def test_invalid_manifest_is_not_treated_as_a_dataset(tmp_path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps({"dataset_id": "missing-required-fields"}), encoding="utf-8")

    with pytest.raises(SourceReadError) as error:
        FileFixtureSource(source).load()

    assert error.value.code == "source_schema_invalid"
