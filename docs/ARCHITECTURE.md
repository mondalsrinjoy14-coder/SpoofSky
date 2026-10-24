# SpoofSky Architecture

## Decision

Use a small monorepo with a React/TypeScript frontend and a Python/FastAPI backend. Keep ingestion, normalization, data-quality checks, and detection as explicit domain modules rather than embedding them in HTTP routes or UI components.

This is a target architecture for an empty repository. It is intentionally local-first and avoids introducing a database or service boundary before the data model and workload justify it.

## Proposed layout

```text
backend/
  app/
    api/              # FastAPI routes and dependency wiring
    domain/           # observation, provenance, anomaly, event models
    ingestion/        # source adapters and validation
    analysis/         # deterministic detectors and evidence builders
    repositories/     # fixture/file repository, later DB implementation
  tests/
frontend/
  src/
    components/       # accessible reusable UI pieces
    features/         # map, tracks, anomalies, filters
    api/              # typed API client
    styles/           # design tokens and global styles
data/
  fixtures/           # small deterministic, explicitly labelled datasets
docs/
```

## Data flow

1. An ingestion adapter reads a documented source or fixture.
2. Pydantic models validate shape, ranges, timestamps, and provenance.
3. Normalization produces a canonical observation representation while retaining the original source fields where needed.
4. Data-quality checks emit explicit quality records and do not erase the raw observation.
5. Detectors consume valid, provenance-aware observations and emit explainable anomaly records.
6. A grouping stage may form suspected events from spatial/temporal patterns, always preserving uncertainty and detector evidence.
7. The API exposes paginated observations and anomalies; the frontend renders only the returned data and its freshness/provenance metadata.

## Persistence strategy

Start with a repository interface backed by versioned local fixtures. Use PostgreSQL/PostGIS only after measuring a need for durable multi-session storage, spatial indexing, retention, or concurrent analysis. If introduced, use migrations, parameterized queries, least-privilege credentials, and indexes aligned with actual query plans.

## API boundary

The API should expose typed resources such as:

- health/configuration metadata;
- dataset/source metadata;
- paginated observations;
- data-quality records;
- detected anomalies and evidence;
- suspected-event groupings.

No endpoint should imply that an inferred event is independently verified. External source URLs, schemas, and rate limits must be verified from primary documentation before an adapter is implemented.

## Frontend design direction

Use a restrained aviation-intelligence interface: strong typography, compact controls, high-contrast severity indicators, readable map overlays, explicit loading/error/empty states, and responsive layouts. Avoid decorative dashboards, unsupported statistics, and visual density that hides evidence.

## Initial operational assumptions

- Development runs on localhost.
- No authentication is needed for the first local-only slice, but the service must not be presented as public-ready.
- Configuration comes from environment variables or local configuration excluded from version control.
- Structured logs must exclude secrets and unnecessary aircraft/personally sensitive data.

## Stage 2 implementation

- `backend/app/domain/models.py` contains the canonical Pydantic observation, source, quality, rejection, and ingestion-report models.
- `backend/app/ingestion/normalizer.py` accepts documented fixture aliases, normalizes timestamps to UTC, converts feet/knots, and validates coordinates and numeric fields.
- `backend/app/ingestion/file_source.py` is a bounded local JSON fixture source. It reports missing, unreadable, invalid-JSON, and invalid-manifest failures without network fallback.
- `backend/app/ingestion/service.py` classifies duplicates, stale observations, out-of-order observations, future timestamps, and normalization notices.
- `backend/app/repositories/json_store.py` persists accepted ingestion reports as generated JSON under `data/ingested/`; generated files are ignored by version control.
- `data/fixtures/demo_observations.json` is simulated and explicitly labelled. No real provider adapter is enabled because credentials/connectivity and a source-specific access contract are not present in this local environment.

## Stage 3 explorer implementation

- `GET /api/v1/datasets/demo/observations` returns the persisted ingestion report used by the explorer. A missing persisted dataset returns an explicit `404 dataset_not_loaded`; the frontend offers the separate demo-ingest action rather than silently substituting data.
- `frontend/src/api/` contains typed API contracts and safe fetch errors.
- `frontend/src/features/AircraftExplorer.tsx` owns explorer loading, source/freshness metadata, search/date filtering, selection, detail display, and empty/error states.
- `frontend/src/components/ExplorerMap.tsx` renders returned observation coordinates with React Leaflet, OSM attribution, markers, and trajectories when an aircraft has more than one visible observation.
- The current fixture is small, so markers are rendered directly. Pagination, clustering, and server-side filtering remain required before operating on larger real datasets.

## Stage 4 analysis implementation

- `backend/app/analysis/features.py` extracts ordered transition features without embedding detector policy.
- `backend/app/analysis/detectors.py` contains independent movement, speed-consistency, trajectory-discontinuity, and ingestion-quality detectors.
- `backend/app/analysis/clustering.py` conservatively groups independent movement alerts across aircraft and explicitly calls the result a potential interference indicator.
- `backend/app/analysis/service.py` orchestrates the detectors and returns an `AnalysisReport` with detector input counts, alerts, clusters, and limitations.
- `GET /api/v1/datasets/demo/anomalies` runs the engine against the stored demo ingestion report. It returns `404 dataset_not_loaded` if the fixture has not been explicitly ingested.

## Stage 5 investigation workflow

- `backend/app/analysis/investigation.py` converts alerts and clusters into stable, status-bearing investigation events with supporting observations.
- `GET /api/v1/datasets/demo/investigation` provides bounded time, geographic, category, severity, sorting, and pagination filters.
- `GET /api/v1/datasets/demo/investigation/export` exports all matching event rows as CSV with stable IDs, methods, evidence references, timestamps, provenance, and explanations.
- The frontend keeps aircraft selection, evidence-event selection, map highlighting, supporting timelines, limitations, and export actions in the explorer feature. Detection computation remains backend-only.
