from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import main


client = TestClient(main.app)


def test_persisted_demo_dataset_can_be_read_after_ingest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))

    ingest_response = client.post("/api/v1/datasets/demo/ingest")
    read_response = client.get("/api/v1/datasets/demo/observations")

    assert ingest_response.status_code == 200
    assert read_response.status_code == 200
    assert read_response.json()["dataset_id"] == "demo-observations-v1"
    assert read_response.json()["source"]["provenance_kind"] == "simulated"
    assert len(read_response.json()["accepted_observations"]) == 4


def test_unloaded_demo_dataset_returns_explicit_empty_response(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))

    response = client.get("/api/v1/datasets/demo/observations")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "dataset_not_loaded"


def test_demo_anomalies_run_against_persisted_observations(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))

    client.post("/api/v1/datasets/demo/ingest")
    response = client.get("/api/v1/datasets/demo/anomalies")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == "demo-observations-v1"
    assert body["detector_input_count"] == 4
    assert body["transition_count"] == 2
    assert any(alert["kind"] == "data_quality_inconsistency" for alert in body["alerts"])
    assert body["clusters"] == []


def test_investigation_filters_paginate_and_include_supporting_observations(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))
    client.post("/api/v1/datasets/demo/ingest")

    response = client.get(
        "/api/v1/datasets/demo/investigation",
        params={"category": "data_quality_inconsistency", "page_size": 1, "sort": "oldest"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["total_events"] >= 1
    assert body["total_pages"] >= 1
    assert all(event["kind"] == "data_quality_inconsistency" for event in body["events"])
    assert all(event["status"] == "detected" for event in body["events"])
    assert any(event["supporting_observations"] for event in body["events"])
    assert "regional interference event" in " ".join(body["limitations"])


def test_investigation_time_and_location_filters_return_empty_when_outside_dataset(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))
    client.post("/api/v1/datasets/demo/ingest")

    response = client.get(
        "/api/v1/datasets/demo/investigation",
        params={"start_time": "2027-01-01T00:00:00Z", "min_latitude": 50, "min_longitude": 100},
    )

    assert response.status_code == 200
    assert response.json()["events"] == []
    assert response.json()["total_events"] == 0


def test_investigation_export_contains_auditable_event_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))
    client.post("/api/v1/datasets/demo/ingest")

    response = client.get("/api/v1/datasets/demo/investigation/export", params={"severity": "warning"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "spoofsky-investigation.csv" in response.headers["content-disposition"]
    assert "event_id,event_type,status,kind" in response.text
    assert "simulated" in response.text


def test_unloaded_investigation_returns_explicit_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "INGESTED_DATA_PATH", Path(tmp_path))

    response = client.get("/api/v1/datasets/demo/investigation")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "dataset_not_loaded"
