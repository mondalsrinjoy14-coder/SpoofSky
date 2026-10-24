# SpoofSky Product Specification

## Purpose

SpoofSky is a software-only research platform for analysing legitimately accessible aircraft-tracking observations and identifying unusual behaviour that may warrant investigation for possible GPS interference.

The product is an analytical research tool, not a certified aviation safety system. An aircraft-tracking anomaly is not proof of GPS spoofing or jamming.

## Users and primary workflow

The initial user is a researcher or analyst who needs to:

1. Load a documented historical, live, or simulated observation set.
2. Inspect coverage, freshness, provenance, and data-quality warnings.
3. View aircraft tracks and suspicious observations on a map and timeline.
4. Review detector evidence, thresholds, and uncertainty.
5. Export or record an analysis without confusing inferred events with verified incidents.

## Domain distinctions

The system must represent these as separate states/types:

- **Raw observation**: an observation received from a source, including source identity and acquisition time.
- **Data-quality problem**: missing, malformed, stale, duplicated, contradictory, or otherwise unreliable data.
- **Detected anomaly**: a deterministic or statistical rule flagged an observation or pattern.
- **Suspected interference event**: a grouped set of anomalies with supporting evidence and an explicit uncertainty level.
- **Independently verified incident**: an externally corroborated event, never inferred solely from tracking anomalies.

Every record must retain whether it is `real`, `simulated`, or another explicitly defined provenance class. Failed real-data access must not silently become simulated data.

## Scope for the first implementation milestone

- A versioned observation schema covering aircraft identifier, timestamp, latitude, longitude, optional altitude/speed/heading, source, and provenance.
- Deterministic validation and data-quality classification.
- A first baseline detector for trajectory discontinuities and implausible transitions, with explainable evidence rather than a single opaque score.
- A small API for loading a labelled fixture and reading observations/anomalies.
- A minimal UI view for source/provenance, map-ready track data, filters, and anomaly evidence.

## Out of scope for the first milestone

- Safety-critical alerts or operational aviation decisions.
- Claims that an event is confirmed without independent corroboration.
- Hardware, SDR, GPS receivers, or physical sensors.
- Unreviewed machine-learning claims or accuracy percentages without labelled evaluation data.
- Public deployment, multi-tenant accounts, billing, or automated incident publication.

## Acceptance criteria

- A user can tell whether each displayed observation is real or simulated.
- Invalid and suspicious input is classified as a data-quality issue where appropriate, not silently analysed as valid data.
- Each anomaly includes the detector name/version, input observations, threshold/configuration, and an explanation.
- The interface uses cautious language such as “detected anomaly” or “suspected interference event”; it does not label tracking evidence as confirmed spoofing.
- The first detector has deterministic tests for normal, anomalous, malformed, duplicate, and time-out-of-order fixtures.
