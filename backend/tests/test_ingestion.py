from datetime import datetime, timedelta, timezone

from backend.app.domain.models import FixtureDocument, ProvenanceKind, SourceKind, SourceMetadata
from backend.app.ingestion.service import ingest_fixture


def make_document(observations: list[dict]) -> FixtureDocument:
    return FixtureDocument(
        schema_version="0.1",
        dataset_id="test-fixture",
        reference_time=datetime(2026, 10, 24, 5, 10, tzinfo=timezone.utc),
        source=SourceMetadata(
            source_id="test-source",
            source_name="Deterministic test source",
            source_kind=SourceKind.FIXTURE,
            provenance_kind=ProvenanceKind.SIMULATED,
            schema_version="0.1",
            is_demo=True,
            access_restrictions="Tests only",
            attribution="SpoofSky tests",
        ),
        observations=observations,
    )


def test_normalizes_timestamp_coordinates_and_units() -> None:
    report = ingest_fixture(
        make_document(
            [
                {
                    "aircraft_id": "TEST-A",
                    "timestamp": "2026-10-24T05:05:00",
                    "coordinates": {"lat": "28.61", "lon": "77.21"},
                    "altitude_ft": "10000",
                    "ground_speed_kt": "100",
                }
            ]
        ),
        ingested_at=datetime(2026, 10, 24, 5, 10, tzinfo=timezone.utc),
    )

    assert len(report.accepted_observations) == 1
    observation = report.accepted_observations[0]
    assert observation.observed_at.tzinfo is not None
    assert observation.latitude == 28.61
    assert observation.longitude == 77.21
    assert round(observation.altitude_m or 0, 2) == 3048.0
    assert round(observation.ground_speed_mps or 0, 3) == 51.444
    assert observation.provenance_kind is ProvenanceKind.SIMULATED
    assert "timestamp_timezone_assumed_utc" in {issue.code for issue in report.quality_issues}


def test_rejects_malformed_coordinates_and_missing_aircraft() -> None:
    report = ingest_fixture(
        make_document(
            [
                {"observation_id": "bad-coordinate", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T05:05:00Z", "lat": 95, "lon": 77},
                {"observation_id": "missing-aircraft", "timestamp": "2026-10-24T05:05:00Z", "lat": 28, "lon": 77},
            ]
        )
    )

    assert len(report.accepted_observations) == 0
    assert len(report.rejected_observations) == 2
    assert {item.reason_code for item in report.rejected_observations} == {"validation_error", "missing_aircraft_id"}


def test_flags_duplicates_stale_and_out_of_order_records() -> None:
    report = ingest_fixture(
        make_document(
            [
                {"observation_id": "one", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T03:00:00Z", "lat": 28, "lon": 77},
                {"observation_id": "two", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T05:05:00Z", "lat": 28.1, "lon": 77.1},
                {"observation_id": "three", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T05:01:00Z", "lat": 28.2, "lon": 77.2},
                {"observation_id": "two", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T05:05:00Z", "lat": 28.1, "lon": 77.1},
            ]
        ),
        stale_after=timedelta(hours=1),
    )

    codes = {issue.code for issue in report.quality_issues}
    assert "stale_observation" in codes
    assert "out_of_order_observation" in codes
    assert "duplicate_observation" in codes
    assert len(report.accepted_observations) == 3
    assert len(report.rejected_observations) == 1


def test_rejects_future_observations_without_silent_drop() -> None:
    report = ingest_fixture(
        make_document(
            [{"observation_id": "future", "aircraft_id": "TEST-A", "timestamp": "2026-10-24T05:30:00Z", "lat": 28, "lon": 77}]
        )
    )

    assert report.rejected_observations[0].reason_code == "future_observation"
    assert any(issue.code == "future_observation" for issue in report.quality_issues)
