"""Orchestrate feature extraction, detectors, and cautious event grouping."""

from backend.app.analysis.clustering import cluster_correlated_anomalies
from backend.app.analysis.detectors import (
    detect_data_quality_inconsistencies,
    detect_implausible_position_changes,
    detect_reported_speed_inconsistencies,
    detect_trajectory_discontinuities,
)
from backend.app.analysis.features import extract_transitions
from backend.app.domain.models import AnalysisReport, IngestionReport


def analyze_ingestion_report(report: IngestionReport) -> AnalysisReport:
    """Run all supported detectors against one stored ingestion report."""

    transitions = extract_transitions(report.accepted_observations)
    provenance = report.source.provenance_kind
    alerts = [
        *detect_implausible_position_changes(transitions, provenance=provenance),
        *detect_reported_speed_inconsistencies(transitions, provenance=provenance),
        *detect_trajectory_discontinuities(transitions, provenance=provenance),
        *detect_data_quality_inconsistencies(report),
    ]
    alerts.sort(key=lambda alert: (alert.start_time, alert.detector_id, alert.alert_id))
    clusters = cluster_correlated_anomalies(alerts)
    return AnalysisReport(
        dataset_id=report.dataset_id,
        source=report.source,
        detector_input_count=len(report.accepted_observations),
        transition_count=len(transitions),
        alerts=alerts,
        clusters=clusters,
        limitations=[
            "Aircraft tracking anomalies alone cannot prove GPS spoofing or jamming.",
            "Detectors use only the fields present in the canonical observation model; no RF, receiver, weather, or independent incident evidence is used.",
            "Irregular sampling and missing fields reduce confidence; large gaps are not treated as reliable movement evidence.",
        ],
    )
