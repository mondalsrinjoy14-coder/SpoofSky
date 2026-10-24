# SpoofSky Testing Strategy

## Testing principles

Tests must be deterministic, must distinguish real and simulated provenance, and must validate evidence and uncertainty rather than only a final anomaly count. No accuracy percentage is reported without labelled evaluation data.

## Planned layers

### Unit tests

- Pydantic/schema validation for ranges, timestamps, optional fields, provenance, and malformed inputs.
- Data-quality classification for duplicates, gaps, out-of-order records, stale data, and impossible transitions.
- Detection algorithms for normal tracks, trajectory discontinuities, implausible speed/altitude changes, and boundary values.
- Evidence serialization, detector versioning, and uncertainty labels.

### Integration/API tests

- Fixture ingestion and repository behaviour.
- Pagination, filters, validation failures, and safe error responses.
- Separation of raw observations, quality problems, anomalies, suspected events, and verified-incident metadata.
- CORS and authorization behaviour when those controls are introduced.

### Frontend tests

- Loading, empty, error, and stale-data states.
- Provenance and severity labels.
- Filter/map/timeline interactions using mocked typed API responses.
- Keyboard navigation, accessible names, focus order, and contrast-sensitive status presentation.

### End-to-end tests

When the UI and API exist, use Playwright for the critical workflow: load a labelled fixture, inspect its source metadata, filter an aircraft/time window, open anomaly evidence, and confirm that inferred results are not shown as verified incidents.

## Commands

Current checks:

- `py -m pytest backend/tests -q` from the repository root.
- `npm run test` from `frontend/`.
- `npm run typecheck` from `frontend/`.
- `npm run build` from `frontend/`.
- The backend analysis suite is included in `py -m pytest backend/tests -q`, including normal, suspicious, irregular-sampling, missing-field, false-positive, invalid-data, and multi-aircraft cluster cases.

Playwright is not configured yet because the frontend does not consume the ingestion API. Add it when the critical ingest-and-review browser flow exists.

## Evaluation data

Maintain separate fixtures for ordinary behaviour, known data-quality failures, detector-positive synthetic cases, and edge cases. If independently labelled real incidents become available, keep the labels and evaluation procedure versioned and report false positives/negatives with the dataset scope and limitations.
