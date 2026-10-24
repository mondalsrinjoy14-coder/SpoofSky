"""Ingest observations while preserving recoverable quality issues."""

from datetime import datetime, timedelta, timezone

from backend.app.domain.models import (
    FixtureDocument,
    IngestionReport,
    QualityIssue,
    QualitySeverity,
    RejectedObservation,
)
from backend.app.ingestion.errors import ObservationNormalizationError
from backend.app.ingestion.normalizer import normalize_record


def ingest_fixture(
    document: FixtureDocument,
    *,
    ingested_at: datetime | None = None,
    stale_after: timedelta = timedelta(hours=1),
    future_tolerance: timedelta = timedelta(minutes=5),
) -> IngestionReport:
    """Normalize a fixture and classify quality issues without silent loss."""

    ingested_at = (ingested_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    accepted = []
    rejected: list[RejectedObservation] = []
    issues: list[QualityIssue] = []
    seen_keys: set[tuple[str, str]] = set()
    last_seen_by_aircraft: dict[str, datetime] = {}

    for raw in document.observations:
        candidate_id = raw.get("observation_id") if isinstance(raw, dict) else None
        candidate_source_id = raw.get("source_record_id", raw.get("id")) if isinstance(raw, dict) else None
        try:
            observation, normalization_codes = normalize_record(raw, document, ingested_at)
        except ObservationNormalizationError as exc:
            rejected.append(
                RejectedObservation(
                    source_record_id=exc.source_record_id or candidate_source_id,
                    observation_id=exc.observation_id or candidate_id,
                    reason_code=exc.code,
                    message=exc.message,
                )
            )
            issues.append(
                QualityIssue(
                    code=exc.code,
                    severity=QualitySeverity.ERROR,
                    message=exc.message,
                    observation_id=exc.observation_id or candidate_id,
                    source_record_id=exc.source_record_id or candidate_source_id,
                )
            )
            continue

        duplicate_key = (observation.source_id, observation.observation_id)
        if duplicate_key in seen_keys:
            issues.append(
                QualityIssue(
                    code="duplicate_observation",
                    severity=QualitySeverity.WARNING,
                    message="Duplicate observation identity rejected after normalization",
                    observation_id=observation.observation_id,
                    source_record_id=observation.source_record_id,
                )
            )
            rejected.append(
                RejectedObservation(
                    source_record_id=observation.source_record_id,
                    observation_id=observation.observation_id,
                    reason_code="duplicate_observation",
                    message="Duplicate observation identity",
                )
            )
            continue
        seen_keys.add(duplicate_key)

        previous = last_seen_by_aircraft.get(observation.aircraft_id)
        if previous is not None and observation.observed_at < previous:
            issues.append(
                QualityIssue(
                    code="out_of_order_observation",
                    severity=QualitySeverity.WARNING,
                    message="Observation timestamp is earlier than the previous source record for this aircraft",
                    observation_id=observation.observation_id,
                    source_record_id=observation.source_record_id,
                )
            )
        last_seen_by_aircraft[observation.aircraft_id] = max(previous or observation.observed_at, observation.observed_at)

        age = document.reference_time - observation.observed_at
        if age > stale_after:
            issues.append(
                QualityIssue(
                    code="stale_observation",
                    severity=QualitySeverity.WARNING,
                    message=f"Observation is older than the configured {int(stale_after.total_seconds())}-second freshness window",
                    observation_id=observation.observation_id,
                    source_record_id=observation.source_record_id,
                )
            )
        if observation.observed_at - document.reference_time > future_tolerance:
            rejected.append(
                RejectedObservation(
                    source_record_id=observation.source_record_id,
                    observation_id=observation.observation_id,
                    reason_code="future_observation",
                    message="Observation is beyond the permitted future timestamp tolerance",
                )
            )
            issues.append(
                QualityIssue(
                    code="future_observation",
                    severity=QualitySeverity.ERROR,
                    message="Observation is beyond the permitted future timestamp tolerance",
                    observation_id=observation.observation_id,
                    source_record_id=observation.source_record_id,
                )
            )
            continue

        for code in normalization_codes:
            issues.append(
                QualityIssue(
                    code=code,
                    severity=QualitySeverity.INFO,
                    message=f"Observation normalized with {code}",
                    observation_id=observation.observation_id,
                    source_record_id=observation.source_record_id,
                )
            )
        accepted.append(observation)

    return IngestionReport(
        dataset_id=document.dataset_id,
        source=document.source,
        reference_time=document.reference_time,
        accepted_observations=accepted,
        rejected_observations=rejected,
        quality_issues=issues,
    )
