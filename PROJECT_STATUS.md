# SpoofSky Project Status

## Current state

- Repository: local-first monorepo scaffold with a React/Vite frontend, FastAPI backend, deterministic fixture source, JSON persistence, and tests.
- Existing work inspected: prior documentation and Stage 1 scaffold; no implementation was unnecessarily overwritten or removed.
- Runtime detected: Node.js `v24.21.0`, npm `11.19.0`, Python `3.14.7` via `py`, and pip `26.2.1`.
- The `python` command resolves to the Windows Store alias in the current shell; use the `py` launcher unless the environment is corrected.
- Docker is not installed; PostgreSQL/PostGIS is intentionally not used at this stage.
- Backend dependencies are installed from `backend/requirements.txt`.
- Frontend dependencies are installed from `frontend/package.json` and locked in `frontend/package-lock.json`.

## Target architecture

- `backend/`: Python FastAPI service with Pydantic request/response models, ingestion adapters, normalization, anomaly analysis, and health/configuration endpoints.
- `frontend/`: React + TypeScript application built with a maintained bundler, consuming typed HTTP API responses.
- `analysis/` or backend domain modules: deterministic, independently testable anomaly-detection functions that preserve provenance and confidence/uncertainty.
- Persistence: begin with versioned file fixtures and an explicit repository interface; introduce PostgreSQL/PostGIS only when query volume, spatial filtering, or retention requirements justify it.
- Deployment: local-first development; no public deployment is planned in this stage.

## Implemented features

- Stage 1 application shell, shared visual tokens, responsive layout, and frontend smoke tests.
- Stage 1 reusable `StatusBadge`, `EmptyState`, `Alert`, `Button`, and `StateMessage` components, plus shared control, table, alert, loading, and error styles.
- Stage 2 validated observation model with UTC timestamp normalization, coordinate/unit normalization, and field validation.
- Explicit provenance model separating `real` and `simulated` observations.
- Fixture ingestion with explicit handling for malformed, duplicate, stale, out-of-order, future, and timezone-ambiguous records.
- Clearly labelled deterministic demo dataset at `data/fixtures/demo_observations.json`.
- Local JSON persistence under `data/ingested/` through `JsonObservationStore`.
- FastAPI health/status endpoints and a local demo-ingestion endpoint.
- Stage 3 aircraft explorer using persisted backend observations, React Leaflet map markers, trajectories, aircraft selection/details, date/search filters, freshness/source metadata, and explicit empty/error states.
- OSM tile attribution is visible in the map frame; no live feed is claimed.
- Stage 4 independent analysis engine with transition feature extraction, explainable movement/speed/trajectory/data-quality detectors, conservative multi-aircraft clustering, and a stored-dataset analysis endpoint.
- Stage 5 investigation workflow with stable event IDs/statuses, time/location/category/severity filters, sorting/pagination, supporting observations/timelines, method and limitation display, map evidence highlighting, and CSV export.

## Incomplete features

- No real external data-source adapter is enabled; provider credentials/connectivity and a source-specific contract are not configured.
- Broader labelled evaluation fixtures for anomaly analysis.
- Larger-dataset performance controls such as pagination, server-side filtering, and marker clustering.
- Database persistence, migrations, authentication, and public deployment controls.

## Relevant files

- `PROJECT_STATUS.md`: current implementation state, checks, findings, and next work.
- `docs/PRODUCT_SPEC.md`: product boundaries and first acceptance criteria.
- `docs/ARCHITECTURE.md`: proposed module boundaries and data flow.
- `docs/SECURITY.md`: local prototype assumptions and security requirements.
- `docs/DATA_SOURCES.md`: source-selection and provenance requirements.
- `docs/TESTING.md`: planned test strategy and executable checks.
- `README.md`: local start and check commands.
- `backend/app/domain/models.py`: canonical source, observation, quality, rejection, and report models.
- `backend/app/ingestion/`: fixture loading, normalization, and quality classification.
- `backend/app/repositories/json_store.py`: fixture-first persistence.
- `data/fixtures/demo_observations.json`: simulated demonstration input.
- `backend/tests/`: ingestion, source failure, and API tests.
- `frontend/src/api/`: typed explorer API client and contracts.
- `frontend/src/features/AircraftExplorer.tsx`: functional explorer UI.
- `frontend/src/components/ExplorerMap.tsx`: React Leaflet map/trajectory rendering.
- `frontend/src/features/*test*`: explorer filtering and API/UI integration tests.
- `backend/app/analysis/`: feature extraction, detectors, clustering, and orchestration.
- `docs/DETECTORS.md`: detector inputs, algorithms, thresholds, outputs, failure modes, and limitations.
- `docs/INVESTIGATION.md`: investigation event model, API filters, export semantics, and interpretation boundaries.
- `backend/app/analysis/investigation.py`: stable investigation event projection and CSV export.

## Checks executed

- Directory and file inspection: passed; Stage 1/2 source, fixture, and test files are present.
- `git status --short --branch` and `git log --oneline -5`: not applicable; the directory is not a Git repository.
- Runtime discovery: Node.js, npm, `py`, and pip are available.
- `py -m pytest backend/tests -q`: passed; 10 tests passed with one upstream deprecation warning from Starlette/httpx.
- `npm run test` in `frontend/`: passed; 2 tests passed.
- `npm run typecheck` in `frontend/`: passed.
- `npm run build` in `frontend/`: passed; Vite production bundle generated.
- Frontend start smoke check: passed; Vite served `/` on `127.0.0.1:5173`.
- Backend start smoke check: passed; Uvicorn served `/health` on `127.0.0.1:8000`.
- `docker` discovery: unavailable; database checks are not applicable because no database is used.
- Documentation and implementation read-back: passed for the updated status, architecture, data-source, backend, fixture, and frontend files.
- Re-verification after the repeated Stage 1/2 request: all backend/frontend checks below passed again.
- `py -m pytest backend/tests -q`: passed after Stage 5 changes; 25 tests passed with one upstream deprecation warning.
- `npm run test` in `frontend/`: passed after Stage 5 changes; 8 tests passed across 3 test files.
- `npm run typecheck` in `frontend/`: passed after Stage 5 changes.
- `npm run build` in `frontend/`: passed after Stage 5 changes; Leaflet bundle generated.
- Runtime smoke check: Vite served the frontend and the API returned `demo-observations-v1` with 4 accepted simulated observations.
- Browser visual inspection: completed on the local Vite app; the Stage 3 explorer header, simulated-source warning, source metadata, and load action were visible. This earlier inspection was superseded by the complete Stage 5 inspection below.
- Stage 4 analysis smoke check: fresh Uvicorn process ingested the stored demo fixture and returned `demo-observations-v1` with 4 detector inputs, 2 transitions, 3 explainable alerts, and 0 clusters.
- Stage 5 backend workflow tests: investigation filtering, pagination, supporting observations, empty results, unloaded errors, and CSV export are covered.
- Stage 5 frontend workflow tests: backend-derived event display, event selection/evidence detail, query filter propagation, and existing failure/empty states are covered.
- Browser visual inspection: completed on 127.0.0.1:5173 with the backend on 127.0.0.1:8000; the simulated source, real Leaflet map, observation register, three investigation events, filters, pagination, event selection, and evidence detail were visible. The selected detail panel layout was tightened so evidence no longer stretches below the map.

## Known bugs

- No known functional defects after the Stage 5 checks.
- The backend test suite emits a Starlette deprecation warning because the installed TestClient path still uses the current `httpx` integration; it does not fail the tests.

## Stage 5 closeout — 2026-10-24

### Actual implementation state

- Stage 5 is implemented and locally verified: backend-derived investigation events are available through the FastAPI investigation and CSV-export endpoints, and the React explorer renders their filters, pagination, evidence, supporting timeline, limitations, and map highlighting.
- The demo remains a deterministic simulated fixture persisted as JSON. No live provider, database, authentication, or external incident verification is enabled.
- The selected-event detail panel was adjusted so its evidence content sizes to its own content instead of stretching alongside the full map.
- This directory is not a Git repository; no branch or revision is available. Existing files and local generated data were preserved.

### Tests and actual results

- Backend test: `py -m pytest backend/tests -q` from the project root — **25 passed, 1 warning** (Starlette/httpx deprecation).
- Frontend tests: `npm run test` from `frontend/` — **8 passed across 3 test files**.
- Frontend typecheck: `npm run typecheck` from `frontend/` — **passed**.
- Frontend production build: `npm run build` from `frontend/` — **passed**; Vite bundle generated.
- API smoke: Uvicorn on `127.0.0.1:8000` returned Stage 5 health/status, demo ingestion returned 4 accepted observations, and investigation returned 3 total events with pagination.
- Manual browser check: Vite on `127.0.0.1:5173` showed the simulated source, Leaflet map, observation register, investigation filters, three events, event selection, evidence timeline, limitations, and CSV export control.

### Incomplete work, blockers, and risks

- No real external data adapter: provider terms, credentials, schema, rate limits, and access policy are unresolved.
- No labelled ground-truth evaluation set; detector accuracy or calibrated probabilities must not be reported.
- Observation-scale controls are incomplete: server-side observation filtering and marker clustering are still needed before larger datasets.
- Analyst review-status persistence, database migrations, authentication, deployment controls, and Playwright end-to-end coverage are not implemented.
- Known risk: OSM tiles and the local JSON store are suitable for development only. Cluster results remain prioritisation indicators, not confirmed GPS attacks.

### Next stage and prerequisites

**Stage 6 — Scale and analyst-review foundation.** Prerequisites: define the target dataset size and query latency, specify the server-side observation/filter contract, choose a marker-clustering UX, decide whether review statuses must persist, and add representative larger/labelled fixtures. A real provider adapter remains a separate follow-on after access and legal/operational requirements are recorded.

### Concise handoff (under 200 words)

Stage 5 is complete locally. The React/Vite explorer consumes backend investigation results from FastAPI, with stable event IDs, alert/cluster distinction, filters, sorting, pagination, evidence timelines, limitations, map highlighting, and CSV export. The data source is the persisted simulated JSON fixture only; no live provider or database is configured.

Checks: `py -m pytest backend/tests -q` = 25 passed, 1 warning; `npm run test` in `frontend/` = 8 passed; `npm run typecheck` = passed; `npm run build` = passed. Manual browser verification passed on `127.0.0.1:5173` with API `127.0.0.1:8000`.

Next: start Stage 6 by defining scale targets and the server-side observation query/cluster contract. Keep provenance and cautious interpretation boundaries. Before live data work, obtain provider terms, schema, credentials, rate-limit policy, and labelled evaluation data.

## Security findings

- No secrets or external credentials are present.
- Public deployment, authentication, authorization, and external data access are not implemented.
- The service remains localhost-only; the demo endpoint reads a fixed local simulated fixture and never falls back to a live source.
- Request validation, safe source errors, bounded fixture input, path-safe generated persistence, and provenance checks are implemented for this stage.
- Imported observations, source metadata, and any future source URL are untrusted input; URL ingestion must include SSRF protections before it is allowed.
- No silent fallback from a failed real source to simulated data.
- The explorer's default request reads stored data only; the explicit `Load demo dataset` action invokes the simulated fixture endpoint. API failures remain visible.
- The analysis engine does not emit calibrated probabilities or verified incidents. It returns evidence, thresholds, detector versions, supporting observation IDs, and limitations.
- Investigation events preserve the distinction between an individual alert and a multi-aircraft cluster; clusters are explicitly described as potential interference indicators, not proof of a regional attack.
- CSV export includes only backend-returned matching events and their stable identifiers; it does not export unrequested raw payloads or claim external verification.

## Stage 0 architectural decisions and assumptions

- Use a local-first monorepo with React/TypeScript and Python/FastAPI, keeping ingestion, domain models, quality checks, and detectors separate.
- Start with versioned fixture files and a repository interface; defer PostgreSQL/PostGIS until measured persistence or spatial-query needs justify it.
- Use UTC-aware timestamps, explicit source metadata, and a required provenance kind (`real` or `simulated`) on observations and derived results.
- Treat detector output as an inference. “Verified incident” requires independent corroboration and is not produced by the first detector.
- Keep the first UI read-only and localhost-only; do not add authentication merely for appearance.

## External data-source audit

- **Immediately available:** deterministic simulated fixtures, which require no hardware or paid service and are the correct first development/evaluation source.
- **Realistic evaluation source:** ADS-B Exchange publishes free first-of-month sample datasets and historical sample formats. Access, licensing, attribution, and redistribution terms must be reviewed before use; live/API access is not assumed.
- **Realistic research source:** OpenSky provides a public REST API and scientific datasets. Usage is subject to current access limits and non-commercial/personal-use conditions; historical Trino access is aimed at eligible university, government, and aviation-authority research users.
- **Optional contextual source:** the Aviation Weather Center Data API can provide recent METAR, PIREP/AIREP, SIGMET, and related weather context. It is not an aircraft-position source, is rate limited, and should not be used as proof of interference.
- **Source decision for the first slice:** use labelled local fixtures; defer a real adapter until provider terms, schema, and access credentials are explicitly recorded.

## Prioritised implementation plan

1. **Explorer scale-up:** add server-side observation filtering and marker clustering before larger real datasets are displayed.
2. **Investigation persistence:** add review-status persistence only when a real user workflow requires analyst annotations.
3. **Checks and evaluation:** add more labelled detector evaluation fixtures; do not publish accuracy claims without ground truth.
4. **Real source adapter:** only after the first slice is stable, select and integrate one documented source behind the same ingestion interface, with timeouts, bounded retries, and rate-limit handling.
5. **Persistence review:** measure actual query/retention needs before considering PostgreSQL/PostGIS and migrations.

## First vertical slice

Load one versioned simulated fixture containing valid, malformed, duplicate, stale, and out-of-order records; normalize and classify the records; persist the accepted ingestion report; return it from FastAPI; render its actual coordinates; run independent detectors; and let an analyst move from an observation to a stable investigation event, inspect supporting observations/method/limitations, filter historical results, and export the matching event set. The Stage 5 workflow is complete and tested.

## Next highest-priority tasks

1. Add server-side observation filtering and marker clustering for scale.
2. Add analyst review-status persistence if required by the next workflow.
3. Add more labelled detector evaluation fixtures.
4. Review one real provider adapter only after access, terms, schema, timeout, retry, and rate-limit requirements are available.
