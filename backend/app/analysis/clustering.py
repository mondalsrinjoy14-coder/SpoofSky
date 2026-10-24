"""Conservative spatial/temporal grouping of independent anomaly alerts."""

from datetime import timedelta
import hashlib

from backend.app.analysis.geometry import haversine_distance_m
from backend.app.domain.models import AnomalyAlert, AnomalyCluster, AnomalyKind, ProvenanceKind


def _cluster_id(alert_ids: list[str]) -> str:
    return f"cluster-{hashlib.sha256('|'.join(sorted(alert_ids)).encode('utf-8')).hexdigest()[:20]}"


def cluster_correlated_anomalies(
    alerts: list[AnomalyAlert],
    *,
    radius_m: float = 50_000.0,
    time_window: timedelta = timedelta(minutes=5),
) -> list[AnomalyCluster]:
    """Group movement-related alerts affecting multiple aircraft nearby in time/space.

    Data-quality alerts are intentionally excluded: correlated parser or feed
    failures should not be upgraded to a potential interference indicator.
    """

    candidates = [
        alert for alert in alerts
        if alert.kind in {AnomalyKind.UNUSUAL_MOVEMENT, AnomalyKind.SPEED_INCONSISTENCY, AnomalyKind.TRAJECTORY_DISCONTINUITY}
    ]
    candidates.sort(key=lambda alert: (alert.start_time, alert.alert_id))
    groups: list[list[AnomalyAlert]] = []

    for candidate in candidates:
        matching_group: list[AnomalyAlert] | None = None
        for group in groups:
            if any(
                candidate.start_time - item.end_time <= time_window
                and item.start_time - candidate.end_time <= time_window
                and haversine_distance_m(candidate.latitude, candidate.longitude, item.latitude, item.longitude) <= radius_m
                for item in group
            ):
                matching_group = group
                break
        if matching_group is None:
            groups.append([candidate])
        else:
            matching_group.append(candidate)

    clusters: list[AnomalyCluster] = []
    for group in groups:
        aircraft_ids = sorted({aircraft_id for alert in group for aircraft_id in alert.aircraft_ids})
        if len(aircraft_ids) < 2:
            continue
        alert_ids = [alert.alert_id for alert in group]
        observation_ids = sorted({observation_id for alert in group for observation_id in alert.observation_ids})
        latitude = sum(alert.latitude for alert in group) / len(group)
        longitude = sum(alert.longitude for alert in group) / len(group)
        max_radius = max(haversine_distance_m(latitude, longitude, alert.latitude, alert.longitude) for alert in group)
        clusters.append(
            AnomalyCluster(
                cluster_id=_cluster_id(alert_ids),
                detector_id="correlated_anomaly_cluster",
                detector_version="0.1",
                title="Potential interference indicator cluster",
                explanation=(
                    f"{len(aircraft_ids)} aircraft have independent movement-related anomaly alerts "
                    f"within {radius_m:.0f} m and {int(time_window.total_seconds())} seconds. "
                    "This is a prioritisation signal, not confirmation of interference."
                ),
                alert_ids=alert_ids,
                observation_ids=observation_ids,
                aircraft_ids=aircraft_ids,
                start_time=min(alert.start_time for alert in group),
                end_time=max(alert.end_time for alert in group),
                latitude=latitude,
                longitude=longitude,
                radius_m=max_radius,
                thresholds={"radius_m": radius_m, "time_window_seconds": int(time_window.total_seconds())},
                limitations=[
                    "Shared feed, coverage, or processing failures can create correlated alerts.",
                    "Aircraft proximity and similar manoeuvres can be ordinary.",
                    "Independent corroboration is required before calling an incident verified.",
                ],
                provenance_kind=ProvenanceKind.SIMULATED if any(alert.provenance_kind is ProvenanceKind.SIMULATED for alert in group) else ProvenanceKind.REAL,
            )
        )
    return clusters
