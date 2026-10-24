"""Feature extraction kept separate from detector policy."""

from dataclasses import dataclass
from datetime import datetime

from backend.app.analysis.geometry import angular_difference_deg, haversine_distance_m, initial_bearing_deg
from backend.app.domain.models import Observation


@dataclass(frozen=True)
class TransitionFeatures:
    aircraft_id: str
    from_observation_id: str
    to_observation_id: str
    from_observed_at: datetime
    to_observed_at: datetime
    latitude: float
    longitude: float
    elapsed_seconds: float
    distance_m: float
    implied_speed_mps: float
    reported_speed_mps: float | None
    speed_delta_mps: float | None
    bearing_deg: float
    heading_change_deg: float | None
    sampling_gap: bool


def extract_transitions(
    observations: list[Observation],
    *,
    large_gap_seconds: float = 900.0,
) -> list[TransitionFeatures]:
    """Create adjacent, time-ordered transition features per aircraft.

    Observations with identical timestamps are not assigned a movement speed.
    Large gaps are retained as features but marked so detectors can avoid
    treating sparse sampling as confident evidence of an event.
    """

    grouped: dict[str, list[Observation]] = {}
    for observation in observations:
        grouped.setdefault(observation.aircraft_id, []).append(observation)

    transitions: list[TransitionFeatures] = []
    for aircraft_observations in grouped.values():
        ordered = sorted(aircraft_observations, key=lambda item: (item.observed_at, item.observation_id))
        for previous, current in zip(ordered, ordered[1:]):
            elapsed_seconds = (current.observed_at - previous.observed_at).total_seconds()
            if elapsed_seconds <= 0:
                continue
            distance_m = haversine_distance_m(previous.latitude, previous.longitude, current.latitude, current.longitude)
            implied_speed_mps = distance_m / elapsed_seconds
            reported_speed_mps = current.ground_speed_mps
            speed_delta_mps = abs(implied_speed_mps - reported_speed_mps) if reported_speed_mps is not None else None
            bearing_deg = initial_bearing_deg(previous.latitude, previous.longitude, current.latitude, current.longitude)
            heading_change_deg = None
            if previous.heading_deg is not None and current.heading_deg is not None:
                heading_change_deg = angular_difference_deg(previous.heading_deg, current.heading_deg)
            transitions.append(
                TransitionFeatures(
                    aircraft_id=current.aircraft_id,
                    from_observation_id=previous.observation_id,
                    to_observation_id=current.observation_id,
                    from_observed_at=previous.observed_at,
                    to_observed_at=current.observed_at,
                    latitude=current.latitude,
                    longitude=current.longitude,
                    elapsed_seconds=elapsed_seconds,
                    distance_m=distance_m,
                    implied_speed_mps=implied_speed_mps,
                    reported_speed_mps=reported_speed_mps,
                    speed_delta_mps=speed_delta_mps,
                    bearing_deg=bearing_deg,
                    heading_change_deg=heading_change_deg,
                    sampling_gap=elapsed_seconds > large_gap_seconds,
                )
            )
    return transitions
