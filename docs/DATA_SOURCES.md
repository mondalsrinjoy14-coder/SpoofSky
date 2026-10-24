# SpoofSky Data-Source Requirements

## Source policy

Only use aircraft-tracking data that is legitimately accessible under its license, terms of use, and rate limits. Before implementing an adapter, verify the provider's current primary documentation and record the decision in source metadata; do not invent endpoints or fields.

## Acceptable source classes

- Historical public datasets with documented provenance and redistribution/analysis rights.
- A documented external tracking service used within its terms and rate limits.
- Clearly labelled deterministic simulated fixtures for development and evaluation.

The application must make the source class visible and must not present simulated observations as live or real observations.

## Minimum source contract

An adapter must document:

- provider/dataset name and version;
- legal/terms-of-use status and attribution requirements;
- acquisition time and source timestamp semantics;
- aircraft identifier semantics and retention rules;
- latitude/longitude coordinate system and valid ranges;
- optional altitude, speed, heading, vertical-rate, and accuracy semantics;
- update cadence, historical coverage, gaps, and timezone conventions;
- rate limits, authentication requirements, and failure modes;
- known limitations, duplicate behaviour, and whether observations are raw or already processed.

## Ingestion requirements

- Validate and normalize timestamps to an explicit timezone-aware representation.
- Preserve source payload identifiers and raw values where retention is permitted.
- Reject or quarantine malformed coordinates, impossible timestamps, oversized records, and unsupported schemas.
- Emit data-quality records for missing, stale, duplicated, contradictory, or out-of-order observations.
- Record `provenance_kind` such as `real` or `simulated` on every observation and derived result.
- Keep source failure visible to users; never silently fall back to simulation.

## Initial recommendation

Begin with a small versioned fixture contract containing both normal and deliberately anomalous tracks. Select a real historical or external source only after its current documentation, terms, schema, and access path have been reviewed. This keeps detector development reproducible without pretending that a provider has already been integrated.

## Stage 0 source audit

The following options were checked against their current primary documentation on 2026-10-24:

| Source | Practical use | Constraints | Stage 0 decision |
| --- | --- | --- | --- |
| Local deterministic fixtures | Development, regression tests, detector evaluation | Not real-world evidence; must be labelled simulated | Use immediately |
| ADS-B Exchange sample data | Real historical evaluation; free first-of-month samples and documented historical trace formats | Terms, attribution, access, and redistribution must be reviewed; live/API access is not assumed | Candidate after contract review |
| OpenSky REST API and scientific datasets | Non-commercial/personal research and limited recent/historical exploration | Current API limits and access policies apply; commercial use requires consent; coverage and inferred fields have limitations | Candidate adapter |
| OpenSky Trino historical database | Larger historical research queries | Access is intended for eligible university, government, and aviation-authority research users; private/commercial use requires licensing | Only if eligibility is confirmed |
| Aviation Weather Center Data API | Recent weather/PIREPs/AIREPs/SIGMET context for correlation | Not an aircraft-position source; limited lookback, request limits, and no browser CORS | Optional contextual adapter |

The first vertical slice must not depend on any external provider, account, paid service, or hardware. A real-source adapter is a follow-on task and must record the provider's terms, schema, rate limits, and failure behaviour before implementation.

## Stage 2 implementation decision

Stage 2 uses only `data/fixtures/demo_observations.json`. It is a deterministic simulated fixture with a local-only restriction and explicit `provenance_kind: "simulated"`. No live adapter is implemented: the repository has no provider credentials, source-specific configuration, or verified connectivity contract. This prevents the UI/API from implying that real data has been obtained.

The fixture deliberately includes a duplicate and an out-of-order record. The ingestion report keeps valid records, rejects duplicate identities, and emits quality issues for recoverable problems. A future real adapter must use the same canonical model and must add bounded timeouts, retry policy, rate-limit handling, source coverage, and terms/attribution metadata before it is enabled.
