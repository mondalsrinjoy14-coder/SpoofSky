import { describe, expect, it } from 'vitest'
import type { Observation } from '../api'
import { filterObservations, formatNumber, formatTimestamp } from './explorerFilters'

const observations: Observation[] = [
  {
    observation_id: 'one', source_record_id: 'record-001', aircraft_id: 'DEMO-A', observed_at: '2026-10-24T05:00:00Z', ingested_at: '2026-10-24T05:10:00Z', latitude: 28.6, longitude: 77.2, altitude_m: 5000, ground_speed_mps: 100, heading_deg: 90, source_id: 'demo', source_name: 'Demo', provenance_kind: 'simulated',
  },
  {
    observation_id: 'two', source_record_id: 'record-002', aircraft_id: 'DEMO-B', observed_at: '2026-10-24T06:00:00Z', ingested_at: '2026-10-24T06:10:00Z', latitude: 29, longitude: 78, altitude_m: null, ground_speed_mps: null, heading_deg: null, source_id: 'demo', source_name: 'Demo', provenance_kind: 'simulated',
  },
]

describe('aircraft explorer filters', () => {
  it('filters by aircraft/source query and inclusive UTC date range', () => {
    expect(filterObservations(observations, { query: 'record-002', start: '2026-10-24', end: '2026-10-24' })).toHaveLength(1)
    expect(filterObservations(observations, { query: 'DEMO-A', start: '2026-10-25', end: '' })).toHaveLength(0)
  })

  it('formats timestamps and missing numeric values without fabrication', () => {
    expect(formatTimestamp('2026-10-24T05:00:00Z')).toContain('2026')
    expect(formatNumber(null, 'm')).toBe('Not reported')
    expect(formatNumber(12.34, 'm')).toContain('12.3')
  })
})
