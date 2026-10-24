import type { Observation } from '../api'

export type ExplorerFilters = {
  query: string
  start: string
  end: string
}

export function filterObservations(observations: Observation[], filters: ExplorerFilters): Observation[] {
  const query = filters.query.trim().toLowerCase()
  const start = filters.start ? Date.parse(`${filters.start}T00:00:00Z`) : Number.NEGATIVE_INFINITY
  const end = filters.end ? Date.parse(`${filters.end}T23:59:59.999Z`) : Number.POSITIVE_INFINITY

  return observations.filter((observation) => {
    const timestamp = Date.parse(observation.observed_at)
    const matchesQuery = query.length === 0 || observation.aircraft_id.toLowerCase().includes(query) || observation.source_record_id?.toLowerCase().includes(query)
    return matchesQuery && timestamp >= start && timestamp <= end
  })
}

export function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value)) + ' UTC'
}

export function formatNumber(value: number | null, unit: string): string {
  return value === null ? 'Not reported' : `${value.toLocaleString('en-GB', { maximumFractionDigits: 1 })} ${unit}`
}
