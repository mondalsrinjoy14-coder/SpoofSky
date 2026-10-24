from datetime import datetime, timedelta, timezone

from backend.app.analysis.clustering import cluster_correlated_anomalies
from backend.app.analysis.detectors import (
    detect_implausible_position_changes,
    detect_reported_speed_inconsistencies,
    detect_trajectory_discontinuities,
)
from backend.app.analysis.features import extract_transitions
from backend.app.analysis.service import analyze_ingestion_report
from backend.app.domain.models import (
    AnomalyKind,
    IngestionReport,
    Observation,
    ProvenanceKind,
    QualityIssue,
    QualitySeverity,
    SourceKind,
    SourceMetadata,
)


BASE_TIME = datetime(2026, 10, 24, 5, 0, tzinfo=timezone.utc)


def observation(
    observation_id: str,
    aircraft_id: str,
    minutes: int,
    latitude: float,
    longitude: float,
    *,
    speed: float | None = None,
    heading: float | None = None,
) -> Observation:
    timestamp = BASE_TIME + timedelta(minutes=minutes)
    return Observation(
        observation_id=observation_id,
        source_record_id=observation_id,
        aircraft_id=aircraft_id,
        observed_at=timestamp,
        ingested_at=timestamp + timedelta(minutes=1),
        latitude=latitude,
        longitude=longitude,
        altitude_m=6000,
        ground_speed_mps=speed,
        heading_deg=heading,
        source_id="analysis-fixture",
        source_name="Analysis test fixture",
        provenance_kind=ProvenanceKind.SIMULATED,
    )


def source() -> SourceMetadata:
    return SourceMetadata(
        source_id="analysis-fixture",
        source_name="Analysis test fixture",
        source_kind=SourceKind.FIXTURE,
        provenance_kind=ProvenanceKind.SIMULATED,
        schema_version="0.1",
        is_demo=True,
        access_restrictions="Tests only",
        attribution="SpoofSky tests",
    )


def report(observations: list[Observation], issues: list[QualityIssue] | None = None) -> IngestionReport:
    return IngestionReport(
        dataset_id="analysis-fixture",
        source=source(),
        reference_time=BASE_TIME + timedelta(hours=1),
        accepted_observations=observations,
        rejected_observations=[],
        quality_issues=issues or [],
    )


def test_normal_flight_transition_is_not_flagged() -> None:
    observations = [
        observation("normal-1", "NORMAL", 0, 28.6139, 77.2090, speed=130, heading=90),
        observation("normal-2", "NORMAL", 5, 28.6200, 77.2500, speed=130, heading=91),
    ]
    transitions = extract_transitions(observations)

    assert len(transitions) == 1
    assert transitions[0].implied_speed_mps < 340
    assert detect_implausible_position_changes(transitions, provenance=ProvenanceKind.SIMULATED) == []
    assert detect_trajectory_discontinuities(transitions, provenance=ProvenanceKind.SIMULATED) == []


def test_implausible_position_change_is_traceable() -> None:
    observations = [
        observation("jump-1", "JUMP", 0, 28.6139, 77.2090, speed=130, heading=90),
        observation("jump-2", "JUMP", 1, 35.0000, 80.0000, speed=130, heading=90),
    ]
    alerts = detect_implausible_position_changes(extract_transitions(observations), provenance=ProvenanceKind.SIMULATED)

    assert len(alerts) == 1
    assert alerts[0].kind is AnomalyKind.UNUSUAL_MOVEMENT
    assert alerts[0].observation_ids == ["jump-1", "jump-2"]
    assert alerts[0].evidence["implied_speed_mps"] > 340
    assert "not proof" in " ".join(alerts[0].limitations)


def test_reported_speed_inconsistency_is_detected_without_probability_score() -> None:
    observations = [
        observation("speed-1", "SPEED", 0, 28.6139, 77.2090, speed=10, heading=90),
        observation("speed-2", "SPEED", 1, 28.7000, 77.3000, speed=10, heading=90),
    ]
    alerts = detect_reported_speed_inconsistencies(extract_transitions(observations), provenance=ProvenanceKind.SIMULATED)

    assert len(alerts) == 1
    assert alerts[0].kind is AnomalyKind.SPEED_INCONSISTENCY
    assert "probability" not in alerts[0].evidence


def test_irregular_sampling_is_retained_but_not_treated_as_confident_jump() -> None:
    observations = [
        observation("gap-1", "GAP", 0, 28.6139, 77.2090),
        observation("gap-2", "GAP", 30, 35.0000, 80.0000),
    ]
    transitions = extract_transitions(observations)

    assert transitions[0].sampling_gap is True
    assert detect_implausible_position_changes(transitions, provenance=ProvenanceKind.SIMULATED) == []


def test_missing_speed_does_not_create_speed_alert_and_ordinary_turn_is_not_false_positive() -> None:
    observations = [
        observation("turn-1", "TURN", 0, 28.6139, 77.2090, heading=0),
        observation("turn-2", "TURN", 1, 28.6200, 77.2100, heading=140),
    ]
    transitions = extract_transitions(observations)

    assert detect_reported_speed_inconsistencies(transitions, provenance=ProvenanceKind.SIMULATED) == []
    assert detect_trajectory_discontinuities(transitions, provenance=ProvenanceKind.SIMULATED) == []


def test_invalid_observations_cannot_enter_analysis_model() -> None:
    try:
        observation("invalid", "INVALID", 0, 95, 77)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid latitude should be rejected before detection")


def test_quality_alerts_and_analysis_report_preserve_supporting_records() -> None:
    first = observation("quality-1", "QUALITY", 0, 28.6, 77.2)
    second = observation("quality-2", "QUALITY", 1, 28.61, 77.21)
    quality_issue = QualityIssue(
        code="out_of_order_observation",
        severity=QualitySeverity.WARNING,
        message="Observation order requires review",
        observation_id="quality-2",
        source_record_id="quality-2",
    )
    analysis = analyze_ingestion_report(report([first, second], [quality_issue]))

    assert analysis.detector_input_count == 2
    quality_alerts = [alert for alert in analysis.alerts if alert.kind is AnomalyKind.DATA_QUALITY_INCONSISTENCY]
    assert len(quality_alerts) == 1
    assert quality_alerts[0].observation_ids == ["quality-2"]


def test_correlated_movement_alerts_form_cautious_multi_aircraft_cluster() -> None:
    first = observation("cluster-a1", "A", 0, 28.60, 77.20)
    second = observation("cluster-a2", "A", 1, 35.00, 80.00)
    third = observation("cluster-b1", "B", 0, 28.61, 77.21)
    fourth = observation("cluster-b2", "B", 1, 35.01, 80.01)
    alerts = detect_implausible_position_changes(
        extract_transitions([first, second, third, fourth]),
        provenance=ProvenanceKind.SIMULATED,
    )

    clusters = cluster_correlated_anomalies(alerts, radius_m=50_000, time_window=timedelta(minutes=2))

    assert len(clusters) == 1
    assert clusters[0].kind is AnomalyKind.POTENTIAL_INTERFERENCE_INDICATOR
    assert set(clusters[0].aircraft_ids) == {"A", "B"}
    assert "not confirmation" in clusters[0].explanation
