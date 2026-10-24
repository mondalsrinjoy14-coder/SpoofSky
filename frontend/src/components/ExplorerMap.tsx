import { useEffect, useMemo } from 'react'
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet'
import type { LatLngBoundsExpression, LatLngExpression } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Observation } from '../api'

type ExplorerMapProps = {
  observations: Observation[]
  selectedAircraftId: string | null
  highlightObservationIds?: string[]
  onSelectAircraft: (aircraftId: string) => void
}

function MapViewport({ observations }: { observations: Observation[] }) {
  const map = useMap()

  useEffect(() => {
    if (observations.length === 0) return
    const bounds: LatLngBoundsExpression = observations.map((observation) => [observation.latitude, observation.longitude])
    map.fitBounds(bounds, { padding: [28, 28], maxZoom: 12 })
  }, [map, observations])

  return null
}

export function ExplorerMap({ observations, selectedAircraftId, highlightObservationIds = [], onSelectAircraft }: ExplorerMapProps) {
  const highlighted = useMemo(() => new Set(highlightObservationIds), [highlightObservationIds])
  const groupedTrajectories = useMemo(() => {
    const grouped = new Map<string, Observation[]>()
    observations.forEach((observation) => {
      const aircraftObservations = grouped.get(observation.aircraft_id) ?? []
      aircraftObservations.push(observation)
      grouped.set(observation.aircraft_id, aircraftObservations)
    })
    return [...grouped.entries()].filter(([, items]) => items.length > 1)
  }, [observations])

  const center: LatLngExpression = observations.length > 0
    ? [observations[0].latitude, observations[0].longitude]
    : [20, 0]

  return (
    <div className="explorer-map-frame">
      <MapContainer center={center} zoom={3} scrollWheelZoom className="explorer-map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapViewport observations={observations} />
        {groupedTrajectories.map(([aircraftId, aircraftObservations]) => (
          <Polyline
            key={`trajectory-${aircraftId}`}
            positions={aircraftObservations.map((observation) => [observation.latitude, observation.longitude] as LatLngExpression)}
            pathOptions={{ color: aircraftId === selectedAircraftId ? '#7dd3c7' : '#6c8ca4', weight: aircraftId === selectedAircraftId ? 4 : 2, opacity: 0.9 }}
          />
        ))}
        {observations.map((observation) => {
          const isSelected = observation.aircraft_id === selectedAircraftId
          const isEvidence = highlighted.has(observation.observation_id)
          return (
            <CircleMarker
              key={observation.observation_id}
              center={[observation.latitude, observation.longitude]}
              radius={isSelected || isEvidence ? 8 : 6}
              pathOptions={{ color: isEvidence ? '#e8bd70' : isSelected ? '#07111c' : '#7dd3c7', fillColor: isEvidence ? '#e8bd70' : isSelected ? '#e8bd70' : '#7dd3c7', fillOpacity: 0.92, weight: isEvidence ? 3 : 2 }}
              eventHandlers={{ click: () => onSelectAircraft(observation.aircraft_id) }}
            >
              <Tooltip>
                <strong>{observation.aircraft_id}</strong><br />
                {new Date(observation.observed_at).toISOString()}<br />
                {observation.provenance_kind} observation
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="map-attribution-note">Map tiles: OpenStreetMap contributors</div>
    </div>
  )
}
