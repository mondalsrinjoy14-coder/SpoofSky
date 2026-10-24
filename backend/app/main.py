"""Local FastAPI surface for SpoofSky ingestion and truthful status reporting."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.analysis.investigation import build_investigation_response, investigation_csv
from backend.app.analysis.service import analyze_ingestion_report
from backend.app.domain.models import AnalysisReport, AnomalyKind, AnomalySeverity, IngestionReport, InvestigationResponse
from backend.app.ingestion.errors import SourceReadError
from backend.app.ingestion.file_source import FileFixtureSource
from backend.app.ingestion.service import ingest_fixture
from backend.app.repositories.json_store import JsonObservationStore


class HealthResponse(BaseModel):
    status: str
    service: str
    stage: str
    checked_at: datetime


class ProductStatusResponse(BaseModel):
    product: str
    stage: str
    dataset_status: str
    analysis_status: str
    provenance_policy: str


app = FastAPI(
    title="SpoofSky API",
    version="0.1.0",
    description="Local research API for aircraft navigation anomaly analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "demo_observations.json"
INGESTED_DATA_PATH = PROJECT_ROOT / "data" / "ingested"


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    """Report process health without exposing configuration or secrets."""

    return HealthResponse(
        status="ok",
        service="spoofsky-api",
        stage="stage-5-investigation",
        checked_at=datetime.now(timezone.utc),
    )


@app.get("/api/v1/status", response_model=ProductStatusResponse, tags=["product"])
def product_status() -> ProductStatusResponse:
    """Expose truthful product capability status for the shell."""

    return ProductStatusResponse(
        product="SpoofSky",
        stage="Stage 5 — Investigation workflow",
        dataset_status="Demo fixture available; stored observations are readable",
        analysis_status="Explainable detectors and backend-derived investigation events available",
        provenance_policy="Real and simulated observations will remain distinct",
    )


@app.post("/api/v1/datasets/demo/ingest", response_model=IngestionReport, tags=["ingestion"])
def ingest_demo_dataset() -> IngestionReport:
    """Ingest the local simulated fixture; never fall back to a live source."""

    try:
        document = FileFixtureSource(DEMO_FIXTURE_PATH).load()
    except SourceReadError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc

    report = ingest_fixture(document)
    persisted_path = JsonObservationStore(INGESTED_DATA_PATH).save(report)
    try:
        persisted_label = persisted_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        persisted_label = persisted_path.name
    return report.model_copy(update={"persisted_path": persisted_label})


@app.get("/api/v1/datasets/demo/observations", response_model=IngestionReport, tags=["observations"])
def get_demo_dataset() -> IngestionReport:
    """Return the persisted demo dataset; a missing dataset remains an empty state."""

    try:
        report = JsonObservationStore(INGESTED_DATA_PATH).load("demo-observations-v1")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail={"code": "stored_dataset_invalid", "message": str(exc)}) from exc
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "dataset_not_loaded", "message": "The demonstration dataset has not been ingested yet."},
        )
    return report


@app.get("/api/v1/datasets/demo/anomalies", response_model=AnalysisReport, tags=["analysis"])
def get_demo_anomalies() -> AnalysisReport:
    """Run supported detectors against the persisted demo observations."""

    try:
        report = JsonObservationStore(INGESTED_DATA_PATH).load("demo-observations-v1")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail={"code": "stored_dataset_invalid", "message": str(exc)}) from exc
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "dataset_not_loaded", "message": "The demonstration dataset has not been ingested yet."},
        )
    return analyze_ingestion_report(report)


def _load_demo_report() -> IngestionReport:
    try:
        report = JsonObservationStore(INGESTED_DATA_PATH).load("demo-observations-v1")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail={"code": "stored_dataset_invalid", "message": str(exc)}) from exc
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "dataset_not_loaded", "message": "The demonstration dataset has not been ingested yet."},
        )
    return report


def _investigation_response(
    *,
    start_time: datetime | None,
    end_time: datetime | None,
    min_latitude: float | None,
    max_latitude: float | None,
    min_longitude: float | None,
    max_longitude: float | None,
    category: AnomalyKind | None,
    severity: AnomalySeverity | None,
    page: int,
    page_size: int,
    sort: str,
) -> InvestigationResponse:
    report = _load_demo_report()
    analysis = analyze_ingestion_report(report)
    return build_investigation_response(
        report,
        analysis,
        start_time=start_time,
        end_time=end_time,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        category=category,
        severity=severity,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@app.get("/api/v1/datasets/demo/investigation", response_model=InvestigationResponse, tags=["investigation"])
def get_demo_investigation(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    min_latitude: float | None = Query(default=None, ge=-90, le=90),
    max_latitude: float | None = Query(default=None, ge=-90, le=90),
    min_longitude: float | None = Query(default=None, ge=-180, le=180),
    max_longitude: float | None = Query(default=None, ge=-180, le=180),
    category: AnomalyKind | None = None,
    severity: AnomalySeverity | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="newest", pattern="^(newest|oldest|severity)$"),
) -> InvestigationResponse:
    """Return filtered, paginated investigation events with supporting observations."""

    return _investigation_response(
        start_time=start_time,
        end_time=end_time,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        category=category,
        severity=severity,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@app.get("/api/v1/datasets/demo/investigation/export", tags=["investigation"])
def export_demo_investigation(
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    min_latitude: float | None = Query(default=None, ge=-90, le=90),
    max_latitude: float | None = Query(default=None, ge=-90, le=90),
    min_longitude: float | None = Query(default=None, ge=-180, le=180),
    max_longitude: float | None = Query(default=None, ge=-180, le=180),
    category: AnomalyKind | None = None,
    severity: AnomalySeverity | None = None,
    sort: str = Query(default="newest", pattern="^(newest|oldest|severity)$"),
) -> Response:
    """Export all currently matching investigation events as CSV."""

    first_page = _investigation_response(
        start_time=start_time,
        end_time=end_time,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        category=category,
        severity=severity,
        page=1,
        page_size=100,
        sort=sort,
    )
    events = list(first_page.events)
    for page in range(2, first_page.total_pages + 1):
        events.extend(
            _investigation_response(
                start_time=start_time,
                end_time=end_time,
                min_latitude=min_latitude,
                max_latitude=max_latitude,
                min_longitude=min_longitude,
                max_longitude=max_longitude,
                category=category,
                severity=severity,
                page=page,
                page_size=100,
                sort=sort,
            ).events
        )
    export_response = first_page.model_copy(update={"events": events, "total_pages": 1, "page": 1})
    return Response(
        content=investigation_csv(export_response),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="spoofsky-investigation.csv"'},
    )
