from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_is_safe_and_explicit() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["stage"] == "stage-5-investigation"
    assert "secret" not in response.text.lower()


def test_product_status_does_not_claim_unimplemented_analysis() -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "Stage 5 — Investigation workflow"
    assert body["dataset_status"] == "Demo fixture available; stored observations are readable"
    assert body["analysis_status"] == "Explainable detectors and backend-derived investigation events available"
    assert "simulated" in body["provenance_policy"]


def test_demo_ingestion_is_explicitly_simulated() -> None:
    response = client.post("/api/v1/datasets/demo/ingest")

    assert response.status_code == 200
    body = response.json()
    assert body["source"]["provenance_kind"] == "simulated"
    assert body["source"]["is_demo"] is True
    assert len(body["accepted_observations"]) == 4
    assert any(issue["code"] == "duplicate_observation" for issue in body["quality_issues"])
    assert any(issue["code"] == "out_of_order_observation" for issue in body["quality_issues"])
    assert body["persisted_path"] == "data/ingested/demo-observations-v1.json"
