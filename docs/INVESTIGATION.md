# SpoofSky Investigation Workflow

Stage 5 connects the persisted aircraft explorer to the backend anomaly engine.

## Event types and status

- An individual detector result is an `alert` with its stable `alert_id` exposed as `event_id`.
- A justified multi-aircraft grouping is a separate `cluster` with its stable `cluster_id` exposed as `event_id`.
- The interface never treats an individual aircraft alert as a regional event.
- Supported statuses are `detected`, `under_review`, `dismissed`, and `externally_verified`. Stage 5 creates new engine results as `detected`; no external verification is inferred.

## Investigation API

- `GET /api/v1/datasets/demo/investigation`
  - time filters: `start_time`, `end_time`;
  - geographic bounding box: `min_latitude`, `max_latitude`, `min_longitude`, `max_longitude`;
  - `category` and `severity` filters;
  - `page`, `page_size`, and `sort` (`newest`, `oldest`, `severity`).
- `GET /api/v1/datasets/demo/investigation/export` returns CSV for all matching events, not only the visible page.

Each event includes its detector method/version, stable identifier, timestamps, aircraft and observation identifiers, evidence, thresholds, provenance, supporting accepted observations, and limitations.

## Interpretation boundary

The workflow uses cautious language. A data-quality alert is a data problem. A movement alert is an unusual observation pattern. A multi-aircraft cluster is a potential interference indicator only; it does not prove a regional GPS attack. The current dataset is simulated and historical within the local fixture, not a live feed.
