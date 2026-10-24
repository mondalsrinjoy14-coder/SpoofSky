"""Investigation views over detector results and supporting observations."""

from datetime import datetime
import csv
from io import StringIO
from math import ceil

from backend.app.domain.models import (
    AnalysisReport,
    AnomalyAlert,
    AnomalyCluster,
    AnomalyKind,
    AnomalySeverity,
    IngestionReport,
    InvestigationEvent,
    InvestigationResponse,
    Observation,
)


SEVERITY_ORDER = {
    AnomalySeverity.HIGH: 0,
    AnomalySeverity.WARNING: 1,
    AnomalySeverity.INFO: 2,
}


def _event_from_alert(alert: AnomalyAlert, observations_by_id: dict[str, Observation]) -> InvestigationEvent:
    return InvestigationEvent(
        event_id=alert.alert_id,
        event_type="alert",
        status=alert.status,
        kind=alert.kind,
        severity=alert.severity,
        title=alert.title,
        detector_id=alert.detector_id,
        detector_version=alert.detector_version,
        explanation=alert.explanation,
        observation_ids=alert.observation_ids,
        aircraft_ids=alert.aircraft_ids,
        start_time=alert.start_time,
        end_time=alert.end_time,
        latitude=alert.latitude,
        longitude=alert.longitude,
        evidence=alert.evidence,
        thresholds=alert.thresholds,
        limitations=alert.limitations,
        provenance_kind=alert.provenance_kind,
        supporting_observations=[observations_by_id[item] for item in alert.observation_ids if item in observations_by_id],
    )


def _event_from_cluster(cluster: AnomalyCluster, observations_by_id: dict[str, Observation]) -> InvestigationEvent:
    return InvestigationEvent(
        event_id=cluster.cluster_id,
        event_type="cluster",
        status=cluster.status,
        kind=cluster.kind,
        severity=cluster.severity,
        title=cluster.title,
        detector_id=cluster.detector_id,
        detector_version=cluster.detector_version,
        explanation=cluster.explanation,
        observation_ids=cluster.observation_ids,
        aircraft_ids=cluster.aircraft_ids,
        start_time=cluster.start_time,
        end_time=cluster.end_time,
        latitude=cluster.latitude,
        longitude=cluster.longitude,
        evidence={"alert_ids": cluster.alert_ids, "radius_m": cluster.radius_m},
        thresholds=cluster.thresholds,
        limitations=cluster.limitations,
        provenance_kind=cluster.provenance_kind,
        supporting_observations=[observations_by_id[item] for item in cluster.observation_ids if item in observations_by_id],
    )


def build_investigation_response(
    report: IngestionReport,
    analysis: AnalysisReport,
    *,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
    category: AnomalyKind | None = None,
    severity: AnomalySeverity | None = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "newest",
) -> InvestigationResponse:
    observations_by_id = {observation.observation_id: observation for observation in report.accepted_observations}
    events = [
        *[_event_from_alert(alert, observations_by_id) for alert in analysis.alerts],
        *[_event_from_cluster(cluster, observations_by_id) for cluster in analysis.clusters],
    ]

    def included(event: InvestigationEvent) -> bool:
        if start_time is not None and event.end_time < start_time:
            return False
        if end_time is not None and event.start_time > end_time:
            return False
        if min_latitude is not None and event.latitude < min_latitude:
            return False
        if max_latitude is not None and event.latitude > max_latitude:
            return False
        if min_longitude is not None and event.longitude < min_longitude:
            return False
        if max_longitude is not None and event.longitude > max_longitude:
            return False
        if category is not None and event.kind is not category:
            return False
        if severity is not None and event.severity is not severity:
            return False
        return True

    events = [event for event in events if included(event)]
    if sort == "oldest":
        events.sort(key=lambda event: (event.start_time, event.event_id))
    elif sort == "severity":
        events.sort(key=lambda event: (SEVERITY_ORDER[event.severity], -event.start_time.timestamp(), event.event_id))
    else:
        sort = "newest"
        events.sort(key=lambda event: (event.start_time, event.event_id), reverse=True)

    total_events = len(events)
    total_pages = ceil(total_events / page_size) if total_events else 0
    start_index = (page - 1) * page_size
    page_events = events[start_index:start_index + page_size]
    return InvestigationResponse(
        dataset_id=report.dataset_id,
        source=report.source,
        events=page_events,
        total_events=total_events,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        sort=sort,
        limitations=[
            "An individual alert describes unusual observations; it is not a regional interference event.",
            "A multi-aircraft cluster is a potential interference indicator only and does not prove a GPS attack.",
            "Historical and simulated provenance remains attached to every event and supporting observation.",
        ],
    )


def investigation_csv(response: InvestigationResponse) -> str:
    """Export the current investigation page as a portable, auditable CSV."""

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "event_id", "event_type", "status", "kind", "severity", "detector_id", "detector_version",
        "aircraft_ids", "observation_ids", "start_time", "end_time", "latitude", "longitude",
        "provenance_kind", "explanation",
    ])
    for event in response.events:
        writer.writerow([
            event.event_id,
            event.event_type,
            event.status.value,
            event.kind.value,
            event.severity.value,
            event.detector_id,
            event.detector_version,
            ";".join(event.aircraft_ids),
            ";".join(event.observation_ids),
            event.start_time.isoformat(),
            event.end_time.isoformat(),
            event.latitude,
            event.longitude,
            event.provenance_kind.value,
            event.explanation,
        ])
    return output.getvalue()
