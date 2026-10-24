"""Canonical observation and ingestion result models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProvenanceKind(str, Enum):
    REAL = "real"
    SIMULATED = "simulated"


class SourceKind(str, Enum):
    FIXTURE = "fixture"
    FILE = "file"
    API = "api"


class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_id: str = Field(min_length=1, max_length=128)
    source_name: str = Field(min_length=1, max_length=200)
    source_kind: SourceKind
    provenance_kind: ProvenanceKind
    schema_version: str = Field(min_length=1, max_length=32)
    is_demo: bool = False
    coverage_start: datetime | None = None
    coverage_end: datetime | None = None
    access_restrictions: str = Field(min_length=1, max_length=500)
    attribution: str = Field(min_length=1, max_length=500)

    @field_validator("coverage_start", "coverage_end")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("source coverage timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class FixtureDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(min_length=1, max_length=32)
    dataset_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    reference_time: datetime
    source: SourceMetadata
    observations: list[dict[str, Any]] = Field(min_length=1, max_length=100_000)

    @field_validator("reference_time")
    @classmethod
    def normalize_reference_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reference_time must include a timezone")
        return value.astimezone(timezone.utc)


class Observation(BaseModel):
    """Canonical validated observation used by downstream analysis."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    observation_id: str = Field(min_length=1, max_length=128)
    source_record_id: str | None = Field(default=None, max_length=128)
    aircraft_id: str = Field(min_length=1, max_length=128)
    observed_at: datetime
    ingested_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude_m: float | None = Field(default=None, ge=0, le=30_000)
    ground_speed_mps: float | None = Field(default=None, ge=0, le=400)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    source_id: str = Field(min_length=1, max_length=128)
    source_name: str = Field(min_length=1, max_length=200)
    provenance_kind: ProvenanceKind

    @field_validator("observed_at", "ingested_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observation timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class QualitySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    severity: QualitySeverity
    message: str = Field(min_length=1, max_length=500)
    observation_id: str | None = None
    source_record_id: str | None = None


class RejectedObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str | None = None
    observation_id: str | None = None
    reason_code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)


class IngestionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: SourceMetadata
    reference_time: datetime
    accepted_observations: list[Observation]
    rejected_observations: list[RejectedObservation]
    quality_issues: list[QualityIssue]
    persisted_path: str | None = None

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_observations)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_observations)


class AnomalySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class InvestigationStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    DISMISSED = "dismissed"
    EXTERNALLY_VERIFIED = "externally_verified"


class AnomalyKind(str, Enum):
    UNUSUAL_MOVEMENT = "unusual_movement"
    SPEED_INCONSISTENCY = "speed_inconsistency"
    TRAJECTORY_DISCONTINUITY = "trajectory_discontinuity"
    DATA_QUALITY_INCONSISTENCY = "data_quality_inconsistency"
    POTENTIAL_INTERFERENCE_INDICATOR = "potential_interference_indicator"


class AnomalyAlert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str = Field(min_length=1, max_length=128)
    detector_id: str = Field(min_length=1, max_length=128)
    detector_version: str = Field(min_length=1, max_length=32)
    kind: AnomalyKind
    severity: AnomalySeverity
    status: InvestigationStatus = InvestigationStatus.DETECTED
    title: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=1000)
    observation_ids: list[str] = Field(min_length=1, max_length=100)
    aircraft_ids: list[str] = Field(min_length=1, max_length=100)
    start_time: datetime
    end_time: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    evidence: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, float | int | str] = Field(default_factory=dict)
    limitations: list[str] = Field(min_length=1, max_length=20)
    provenance_kind: ProvenanceKind

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_alert_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("alert timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class AnomalyCluster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(min_length=1, max_length=128)
    detector_id: str = Field(min_length=1, max_length=128)
    detector_version: str = Field(min_length=1, max_length=32)
    kind: AnomalyKind = AnomalyKind.POTENTIAL_INTERFERENCE_INDICATOR
    severity: AnomalySeverity = AnomalySeverity.WARNING
    status: InvestigationStatus = InvestigationStatus.DETECTED
    title: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=1000)
    alert_ids: list[str] = Field(min_length=2, max_length=100)
    observation_ids: list[str] = Field(min_length=2, max_length=200)
    aircraft_ids: list[str] = Field(min_length=2, max_length=100)
    start_time: datetime
    end_time: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(ge=0)
    thresholds: dict[str, float | int | str] = Field(default_factory=dict)
    limitations: list[str] = Field(min_length=1, max_length=20)
    provenance_kind: ProvenanceKind

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_cluster_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("cluster timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class AnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: SourceMetadata
    detector_input_count: int = Field(ge=0)
    transition_count: int = Field(ge=0)
    alerts: list[AnomalyAlert]
    clusters: list[AnomalyCluster]
    limitations: list[str] = Field(min_length=1, max_length=20)


class InvestigationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    event_type: Literal["alert", "cluster"]
    status: InvestigationStatus
    kind: AnomalyKind
    severity: AnomalySeverity
    title: str
    detector_id: str
    detector_version: str
    explanation: str
    observation_ids: list[str]
    aircraft_ids: list[str]
    start_time: datetime
    end_time: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    evidence: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, float | int | str] = Field(default_factory=dict)
    limitations: list[str] = Field(min_length=1, max_length=20)
    provenance_kind: ProvenanceKind
    supporting_observations: list[Observation] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: SourceMetadata
    events: list[InvestigationEvent]
    total_events: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
    sort: str
    limitations: list[str] = Field(min_length=1, max_length=20)
