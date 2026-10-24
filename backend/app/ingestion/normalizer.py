"""Convert source-shaped records into canonical validated observations."""

from datetime import datetime, timezone
import hashlib
import math
from typing import Any

from pydantic import ValidationError

from backend.app.domain.models import FixtureDocument, Observation, ProvenanceKind
from backend.app.ingestion.errors import ObservationNormalizationError


def _number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise ObservationNormalizationError("invalid_number", f"{field_name} must be numeric")
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ObservationNormalizationError("invalid_number", f"{field_name} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ObservationNormalizationError("invalid_number", f"{field_name} must be finite")
    return parsed


def _timestamp(value: Any) -> tuple[datetime, bool]:
    if isinstance(value, bool) or value is None:
        raise ObservationNormalizationError("invalid_timestamp", "timestamp is required")
    if isinstance(value, (int, float)):
        try:
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise ObservationNormalizationError("invalid_timestamp", "timestamp epoch value is invalid") from exc
        return parsed, False

    if not isinstance(value, str):
        raise ObservationNormalizationError("invalid_timestamp", "timestamp must be ISO text or epoch seconds")
    text = value.strip()
    if not text:
        raise ObservationNormalizationError("invalid_timestamp", "timestamp must not be empty")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationNormalizationError("invalid_timestamp", "timestamp must be ISO-8601 or epoch seconds") from exc
    assumed_utc = parsed.tzinfo is None or parsed.utcoffset() is None
    if assumed_utc:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc), assumed_utc


def _coordinates(raw: dict[str, Any]) -> tuple[Any, Any]:
    latitude = raw.get("latitude", raw.get("lat"))
    longitude = raw.get("longitude", raw.get("lon"))
    coordinates = raw.get("coordinates")
    if coordinates is not None:
        if isinstance(coordinates, dict):
            latitude = coordinates.get("latitude", coordinates.get("lat", latitude))
            longitude = coordinates.get("longitude", coordinates.get("lon", longitude))
        elif isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
            latitude, longitude = coordinates
        else:
            raise ObservationNormalizationError("invalid_coordinates", "coordinates must be [latitude, longitude] or an object")
    if latitude is None or longitude is None:
        raise ObservationNormalizationError("missing_coordinates", "latitude and longitude are required")
    return latitude, longitude


def _generated_id(raw: dict[str, Any], aircraft_id: str, observed_at: datetime, latitude: float, longitude: float) -> str:
    source_key = f"{raw.get('source_record_id', '')}|{aircraft_id}|{observed_at.isoformat()}|{latitude:.7f}|{longitude:.7f}"
    digest = hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:20]
    return f"generated-{digest}"


def normalize_record(raw: dict[str, Any], document: FixtureDocument, ingested_at: datetime) -> tuple[Observation, list[str]]:
    if not isinstance(raw, dict):
        raise ObservationNormalizationError("invalid_record", "observation must be an object")

    source_record_id = raw.get("source_record_id", raw.get("id"))
    observation_id = raw.get("observation_id")
    aircraft_id = raw.get("aircraft_id", raw.get("icao24", raw.get("aircraft")))
    if aircraft_id is None or not str(aircraft_id).strip():
        raise ObservationNormalizationError("missing_aircraft_id", "aircraft_id is required", source_record_id=source_record_id)
    aircraft_id = str(aircraft_id).strip()

    timestamp_value = raw.get("observed_at", raw.get("timestamp", raw.get("time")))
    observed_at, timezone_assumed = _timestamp(timestamp_value)
    latitude_raw, longitude_raw = _coordinates(raw)
    latitude = _number(latitude_raw, "latitude")
    longitude = _number(longitude_raw, "longitude")

    altitude_m = raw.get("altitude_m")
    if altitude_m is None and raw.get("altitude_ft") is not None:
        altitude_m = _number(raw["altitude_ft"], "altitude_ft") * 0.3048
    elif altitude_m is not None:
        altitude_m = _number(altitude_m, "altitude_m")

    speed_mps = raw.get("ground_speed_mps", raw.get("speed_mps"))
    if speed_mps is None and raw.get("ground_speed_kt") is not None:
        speed_mps = _number(raw["ground_speed_kt"], "ground_speed_kt") * 0.514444
    elif speed_mps is not None:
        speed_mps = _number(speed_mps, "ground_speed_mps")

    heading = raw.get("heading_deg", raw.get("heading"))
    if heading is not None:
        heading = _number(heading, "heading_deg")

    raw_provenance = raw.get("provenance_kind")
    if raw_provenance is not None and raw_provenance != document.source.provenance_kind.value:
        raise ObservationNormalizationError(
            "provenance_mismatch",
            "observation provenance does not match the source manifest",
            observation_id=observation_id,
            source_record_id=source_record_id,
        )

    if observation_id is None or not str(observation_id).strip():
        observation_id = _generated_id(raw, aircraft_id, observed_at, latitude, longitude)
        generated_id = True
    else:
        observation_id = str(observation_id).strip()
        generated_id = False

    try:
        observation = Observation(
            observation_id=observation_id,
            source_record_id=str(source_record_id).strip() if source_record_id is not None else None,
            aircraft_id=aircraft_id,
            observed_at=observed_at,
            ingested_at=ingested_at,
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            ground_speed_mps=speed_mps,
            heading_deg=heading,
            source_id=document.source.source_id,
            source_name=document.source.source_name,
            provenance_kind=document.source.provenance_kind,
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(item) for item in first_error.get("loc", [])) or "observation"
        raise ObservationNormalizationError(
            "validation_error",
            f"{field}: {first_error.get('msg', 'invalid value')}",
            observation_id=observation_id,
            source_record_id=source_record_id,
        ) from exc

    quality_codes: list[str] = []
    if timezone_assumed:
        quality_codes.append("timestamp_timezone_assumed_utc")
    if generated_id:
        quality_codes.append("observation_id_generated")
    if raw.get("altitude_ft") is not None:
        quality_codes.append("altitude_converted_from_feet")
    if raw.get("ground_speed_kt") is not None:
        quality_codes.append("speed_converted_from_knots")
    return observation, quality_codes
