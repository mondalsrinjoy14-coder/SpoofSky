"""Explainable detector policies for the fields currently available."""

from collections.abc import Iterable
from datetime import datetime
import hashlib

from backend.app.analysis.features import TransitionFeatures
from backend.app.domain.models import (
    AnomalyAlert,
    AnomalyKind,
    AnomalySeverity,
    IngestionReport,
    QualitySeverity,
)


DETECTOR_VERSION = "0.1"


def _alert_id(detector_id: str, observation_ids: Iterable[str]) -> str:
    material = f"{detector_id}|{'|'.join(observation_ids)}"
    return f"alert-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:20]}"


def _alert_times(features: TransitionFeatures) -> tuple[datetime, datetime]:
    return features.from_observed_at, features.to_observed_at


def _movement_alert(
    features: TransitionFeatures,
    *,
    detector_id: str,
    kind: AnomalyKind,
    severity: AnomalySeverity,
    title: str,
    explanation: str,
    evidence: dict[str, float | int | str | bool | None],
    thresholds: dict[str, float | int | str],
    limitations: list[str],
    provenance: str,
) -> AnomalyAlert:
    start_time, end_time = _alert_times(features)
    return AnomalyAlert(
        alert_id=_alert_id(detector_id, [features.from_observation_id, features.to_observation_id]),
        detector_id=detector_id,
        detector_version=DETECTOR_VERSION,
        kind=kind,
        severity=severity,
        title=title,
        explanation=explanation,
        observation_ids=[features.from_observation_id, features.to_observation_id],
        aircraft_ids=[features.aircraft_id],
        start_time=start_time,
        end_time=end_time,
        latitude=features.latitude,
        longitude=features.longitude,
        evidence=evidence,
        thresholds=thresholds,
        limitations=limitations,
        provenance_kind=provenance,
    )


def detect_implausible_position_changes(
    transitions: list[TransitionFeatures],
    *,
    max_implied_speed_mps: float = 340.0,
    max_gap_seconds: float = 900.0,
    provenance: str,
) -> list[AnomalyAlert]:
    """Flag position changes requiring an implausibly high average speed.

    Large sampling gaps are excluded from high-confidence movement alerts:
    an unknown path during a gap is uncertainty, not evidence of teleportation.
    """

    alerts: list[AnomalyAlert] = []
    for features in transitions:
        if features.sampling_gap or features.elapsed_seconds > max_gap_seconds:
            continue
        if features.implied_speed_mps <= max_implied_speed_mps:
            continue
        alerts.append(
            _movement_alert(
                features,
                detector_id="implausible_position_change",
                kind=AnomalyKind.UNUSUAL_MOVEMENT,
                severity=AnomalySeverity.HIGH,
                title="Unusual movement between observations",
                explanation=(
                    f"The observed position change implies {features.implied_speed_mps:.1f} m/s over "
                    f"{features.elapsed_seconds:.1f} seconds, above the configured {max_implied_speed_mps:.1f} m/s threshold."
                ),
                evidence={
                    "distance_m": round(features.distance_m, 2),
                    "elapsed_seconds": round(features.elapsed_seconds, 2),
                    "implied_speed_mps": round(features.implied_speed_mps, 2),
                    "sampling_gap": features.sampling_gap,
                },
                thresholds={"max_implied_speed_mps": max_implied_speed_mps, "max_gap_seconds": max_gap_seconds},
                limitations=[
                    "Average movement between two observations cannot establish the aircraft's true path.",
                    "This is an unusual movement indicator, not proof of GPS interference.",
                ],
                provenance=provenance,
            )
        )
    return alerts


def detect_reported_speed_inconsistencies(
    transitions: list[TransitionFeatures],
    *,
    min_absolute_delta_mps: float = 100.0,
    min_relative_delta: float = 0.75,
    max_gap_seconds: float = 900.0,
    provenance: str,
) -> list[AnomalyAlert]:
    """Compare reported speed with the average speed implied by positions."""

    alerts: list[AnomalyAlert] = []
    for features in transitions:
        if features.sampling_gap or features.reported_speed_mps is None or features.speed_delta_mps is None:
            continue
        reference_speed = max(features.reported_speed_mps, features.implied_speed_mps, 1.0)
        relative_delta = features.speed_delta_mps / reference_speed
        if features.speed_delta_mps < min_absolute_delta_mps or relative_delta < min_relative_delta:
            continue
        alerts.append(
            _movement_alert(
                features,
                detector_id="reported_speed_inconsistency",
                kind=AnomalyKind.SPEED_INCONSISTENCY,
                severity=AnomalySeverity.WARNING,
                title="Reported speed does not match position change",
                explanation=(
                    f"Reported speed ({features.reported_speed_mps:.1f} m/s) differs from the position-implied "
                    f"average ({features.implied_speed_mps:.1f} m/s) by {features.speed_delta_mps:.1f} m/s."
                ),
                evidence={
                    "reported_speed_mps": round(features.reported_speed_mps, 2),
                    "implied_speed_mps": round(features.implied_speed_mps, 2),
                    "absolute_delta_mps": round(features.speed_delta_mps, 2),
                    "relative_delta": round(relative_delta, 3),
                },
                thresholds={
                    "min_absolute_delta_mps": min_absolute_delta_mps,
                    "min_relative_delta": min_relative_delta,
                    "max_gap_seconds": max_gap_seconds,
                },
                limitations=[
                    "Reported speed and position timestamps may not represent the same instant.",
                    "Source filtering, quantization, or unit errors can create this inconsistency.",
                ],
                provenance=provenance,
            )
        )
    return alerts


def detect_trajectory_discontinuities(
    transitions: list[TransitionFeatures],
    *,
    max_elapsed_seconds: float = 120.0,
    min_distance_m: float = 20_000.0,
    sharp_turn_degrees: float = 150.0,
    sharp_turn_max_elapsed_seconds: float = 60.0,
    sharp_turn_min_distance_m: float = 500.0,
    provenance: str,
) -> list[AnomalyAlert]:
    """Flag short-interval geometric discontinuities distinct from speed rules."""

    alerts: list[AnomalyAlert] = []
    for features in transitions:
        long_jump = features.elapsed_seconds <= max_elapsed_seconds and features.distance_m >= min_distance_m
        sharp_turn = (
            features.heading_change_deg is not None
            and features.heading_change_deg >= sharp_turn_degrees
            and features.elapsed_seconds <= sharp_turn_max_elapsed_seconds
            and features.distance_m >= sharp_turn_min_distance_m
        )
        if not long_jump and not sharp_turn:
            continue
        reason = "a large short-interval position jump" if long_jump else "a sharp heading change over a short interval"
        alerts.append(
            _movement_alert(
                features,
                detector_id="trajectory_discontinuity",
                kind=AnomalyKind.TRAJECTORY_DISCONTINUITY,
                severity=AnomalySeverity.HIGH,
                title="Trajectory discontinuity detected",
                explanation=f"The transition contains {reason}; review the supporting observations and source quality before interpretation.",
                evidence={
                    "distance_m": round(features.distance_m, 2),
                    "elapsed_seconds": round(features.elapsed_seconds, 2),
                    "heading_change_deg": round(features.heading_change_deg, 2) if features.heading_change_deg is not None else None,
                    "long_jump": long_jump,
                    "sharp_turn": sharp_turn,
                },
                thresholds={
                    "max_elapsed_seconds": max_elapsed_seconds,
                    "min_distance_m": min_distance_m,
                    "sharp_turn_degrees": sharp_turn_degrees,
                },
                limitations=[
                    "A discontinuity may result from source interpolation, track stitching, or an ordinary manoeuvre.",
                    "The detector does not identify spoofing, jamming, or intent.",
                ],
                provenance=provenance,
            )
        )
    return alerts


def detect_data_quality_inconsistencies(report: IngestionReport) -> list[AnomalyAlert]:
    """Promote ingestion quality findings to traceable analytical alerts."""

    alerts: list[AnomalyAlert] = []
    for issue in report.quality_issues:
        if issue.severity is QualitySeverity.INFO:
            continue
        observation_ids = [issue.observation_id] if issue.observation_id else [f"quality:{issue.code}"]
        aircraft_ids = []
        for observation in report.accepted_observations:
            if observation.observation_id == issue.observation_id:
                aircraft_ids = [observation.aircraft_id]
                break
        if not aircraft_ids:
            aircraft_ids = ["unknown"]
        matched = next((item for item in report.accepted_observations if item.observation_id == issue.observation_id), None)
        timestamp = matched.observed_at if matched else report.reference_time
        alerts.append(
            AnomalyAlert(
                alert_id=_alert_id("data_quality_inconsistency", observation_ids),
                detector_id="data_quality_inconsistency",
                detector_version=DETECTOR_VERSION,
                kind=AnomalyKind.DATA_QUALITY_INCONSISTENCY,
                severity=AnomalySeverity.WARNING if issue.severity is QualitySeverity.WARNING else AnomalySeverity.HIGH,
                title="Data-quality inconsistency requires review",
                explanation=issue.message,
                observation_ids=observation_ids,
                aircraft_ids=aircraft_ids,
                start_time=timestamp,
                end_time=timestamp,
                latitude=matched.latitude if matched else 0.0,
                longitude=matched.longitude if matched else 0.0,
                evidence={"quality_code": issue.code, "quality_severity": issue.severity.value, "source_record_id": issue.source_record_id},
                thresholds={},
                limitations=[
                    "A data-quality issue reduces confidence in downstream movement interpretation.",
                    "This alert describes a data problem, not an aircraft event.",
                ],
                provenance_kind=report.source.provenance_kind,
            )
        )
    return alerts
