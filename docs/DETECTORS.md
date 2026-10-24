# SpoofSky Detector Catalogue

Stage 4 implements deterministic, explainable detectors against the canonical observation fields currently available: timestamp, latitude, longitude, optional ground speed, optional heading, aircraft identifier, source, provenance, and ingestion quality issues.

The engine produces `AnomalyAlert` records and cautious multi-aircraft `AnomalyCluster` records. It does not produce calibrated probabilities and does not label any result as confirmed spoofing or jamming.

## Supported detectors

### 1. Implausible position change

- **Required inputs:** two observations for the same aircraft with valid timestamps and coordinates.
- **Algorithm:** sort observations by timestamp, calculate great-circle distance with the haversine formula, divide by elapsed seconds, and compare the average implied speed with a configurable threshold.
- **Default thresholds:** `max_implied_speed_mps=340`; transitions with gaps over `900` seconds are excluded from this alert.
- **Output:** `unusual_movement` alert with both supporting observation IDs, distance, elapsed time, implied speed, detector version, and thresholds.
- **Failure modes:** duplicate or equal timestamps cannot produce a valid transition; malformed observations are rejected before analysis.
- **Known limitations:** an average speed does not reveal the path between observations; source interpolation, track stitching, timestamp errors, or sparse coverage can create false positives. The result is an unusual movement indicator only.

### 2. Reported-speed inconsistency

- **Required inputs:** a valid transition and a reported ground speed on the later observation.
- **Algorithm:** compare the reported speed with the position-implied average speed using both an absolute difference and a relative difference.
- **Default thresholds:** absolute difference at least `100 m/s` and relative difference at least `0.75`; gaps over `900` seconds are excluded.
- **Output:** `speed_inconsistency` warning with reported/implied speeds and both comparison values.
- **Failure modes:** no alert is possible when speed is missing; unit conversion errors upstream can affect the result.
- **Known limitations:** source timestamps may not align, reported speed may be filtered or quantized, and ordinary acceleration can create disagreement.

### 3. Trajectory discontinuity

- **Required inputs:** two ordered observations with valid coordinates; heading is optional.
- **Algorithm:** flag a large position jump in a short interval, or a sharp heading change over a short interval with a non-trivial displacement.
- **Default thresholds:** at least `20 km` within `120 seconds`, or a heading change of at least `150°` within `60 seconds` and at least `500 m` of movement.
- **Output:** `trajectory_discontinuity` alert with the supporting observations and whether the long-jump or sharp-turn condition matched.
- **Failure modes:** missing heading only disables the heading branch; invalid data is rejected before analysis.
- **Known limitations:** manoeuvres, track stitching, source interpolation, and coordinate errors can resemble discontinuities. This detector does not infer intent or interference.

### 4. Data-quality inconsistency

- **Required inputs:** warning/error quality findings from ingestion.
- **Algorithm:** promote each non-informational ingestion quality finding to a traceable analytical alert, retaining its quality code and source record reference.
- **Thresholds:** none; the ingestion classifier owns its freshness, duplicate, ordering, and validation policies.
- **Output:** `data_quality_inconsistency` alert with the quality issue and any associated observation.
- **Failure modes:** quality findings without a matched accepted observation use the dataset reference time and neutral coordinates.
- **Known limitations:** this is a data problem, not an aircraft event; it should reduce interpretation confidence rather than be treated as evidence of spoofing.

### 5. Correlated anomaly cluster

- **Required inputs:** at least two movement-related alerts from different aircraft, with alert coordinates and timestamps.
- **Algorithm:** group movement, speed, and trajectory alerts when they are within `50 km` and `5 minutes` of one another; require at least two aircraft IDs.
- **Thresholds:** `radius_m=50,000`, `time_window=5 minutes`.
- **Output:** `potential_interference_indicator` cluster with alert IDs, observation IDs, aircraft IDs, centroid, radius, and limitations.
- **Failure modes:** clusters are not formed from data-quality-only alerts and are empty when only one aircraft is involved.
- **Known limitations:** shared feed outages, coverage boundaries, processing faults, or ordinary traffic patterns can create correlation. The cluster is a prioritisation signal, not a confirmed incident.

## Unsupported or deferred detectors

- RF/signal-level jamming or spoofing classification: unavailable without receiver/sensor data.
- Independent incident verification: unavailable without external corroboration.
- Calibrated probability or accuracy score: unavailable because no labelled ground-truth evaluation set exists.
- Weather-aware or airspace-aware context: not implemented because no contextual source is connected.
- Altitude-rate and vertical-profile detectors: deferred until the model has explicit vertical-rate semantics and labelled evaluation cases.
