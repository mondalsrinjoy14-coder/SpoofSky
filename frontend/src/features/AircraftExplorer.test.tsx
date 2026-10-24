import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { IngestionReport, InvestigationResponse } from '../api'
import { AircraftExplorer } from './AircraftExplorer'

vi.mock('../components/ExplorerMap', () => ({
  ExplorerMap: ({ observations, onSelectAircraft }: { observations: Array<{ aircraft_id: string }>; onSelectAircraft: (id: string) => void }) => (
    <div data-testid="mock-map">
      {observations.map((observation, index) => <button key={`${observation.aircraft_id}-${index}`} onClick={() => onSelectAircraft(observation.aircraft_id)}>{observation.aircraft_id}</button>)}
    </div>
  ),
}))

const report: IngestionReport = {
  dataset_id: 'demo-observations-v1',
  source: {
    source_id: 'demo', source_name: 'Demo fixture', source_kind: 'fixture', provenance_kind: 'simulated', schema_version: '0.1', is_demo: true, coverage_start: '2026-10-24T05:00:00Z', coverage_end: '2026-10-24T06:00:00Z', access_restrictions: 'Local only', attribution: 'SpoofSky',
  },
  reference_time: '2026-10-24T06:10:00Z',
  accepted_observations: [
    { observation_id: 'a1', source_record_id: 'record-a', aircraft_id: 'DEMO-A', observed_at: '2026-10-24T05:00:00Z', ingested_at: '2026-10-24T06:10:00Z', latitude: 28.6, longitude: 77.2, altitude_m: 5000, ground_speed_mps: 100, heading_deg: 90, source_id: 'demo', source_name: 'Demo fixture', provenance_kind: 'simulated' },
    { observation_id: 'a2', source_record_id: 'record-a2', aircraft_id: 'DEMO-A', observed_at: '2026-10-24T05:05:00Z', ingested_at: '2026-10-24T06:10:00Z', latitude: 28.7, longitude: 77.3, altitude_m: 5100, ground_speed_mps: 101, heading_deg: 91, source_id: 'demo', source_name: 'Demo fixture', provenance_kind: 'simulated' },
  ],
  rejected_observations: [],
  quality_issues: [],
  persisted_path: 'data/ingested/demo-observations-v1.json',
}

const investigation: InvestigationResponse = {
  dataset_id: 'demo-observations-v1',
  source: report.source,
  events: [{
    event_id: 'alert-quality-1', event_type: 'alert', status: 'detected', kind: 'data_quality_inconsistency', severity: 'warning', title: 'Data-quality inconsistency requires review', detector_id: 'data_quality_inconsistency', detector_version: '0.1', explanation: 'Observation order requires review.', observation_ids: ['a2'], aircraft_ids: ['DEMO-A'], start_time: '2026-10-24T05:05:00Z', end_time: '2026-10-24T05:05:00Z', latitude: 28.7, longitude: 77.3, evidence: { quality_code: 'out_of_order_observation' }, thresholds: {}, limitations: ['This alert describes a data problem, not an aircraft event.'], provenance_kind: 'simulated', supporting_observations: [report.accepted_observations[1]],
  }],
  total_events: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
  sort: 'newest',
  limitations: ['An individual alert describes unusual observations; it is not a regional interference event.'],
}

describe('AircraftExplorer', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      const payload = url.includes('/investigation') ? investigation : report
      return Promise.resolve(new Response(JSON.stringify(payload), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    }))
  })

  it('renders backend records and reveals selected aircraft details', async () => {
    render(<AircraftExplorer />)

    expect(await screen.findByText('Demo fixture')).toBeVisible()
    expect(screen.getAllByText('DEMO-A').length).toBeGreaterThan(0)
    expect(screen.getByText('2 observations · 1 aircraft')).toBeVisible()

    fireEvent.click(screen.getAllByRole('button', { name: 'DEMO-A' })[0])
    expect(screen.getByText('Aircraft detail')).toBeVisible()
    expect(screen.getByText('Latest timestamp')).toBeVisible()
    expect(await screen.findByText('Engine-derived events')).toBeVisible()
    expect(screen.getByText('Data-quality inconsistency requires review')).toBeVisible()

    fireEvent.click(screen.getByRole('button', { name: /Data-quality inconsistency requires review/ }))
    expect(screen.getByText('Detection method')).toBeVisible()
    expect(screen.getByText('Supporting timeline')).toBeVisible()
  })

  it('changes visible records when the search filter changes', async () => {
    render(<AircraftExplorer />)

    await screen.findByText('Demo fixture')
    fireEvent.change(screen.getByRole('textbox', { name: 'Search aircraft or source record' }), { target: { value: 'NO-MATCH' } })

    expect(await screen.findByText('No observations match')).toBeVisible()
  })

  it('shows an API failure and offers retry instead of fake data', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('offline'))
    vi.stubGlobal('fetch', fetchMock)
    render(<AircraftExplorer />)

    expect(await screen.findByText('The SpoofSky API could not be reached. Start the backend and try again.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Retry stored dataset' })).toBeVisible()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  })

  it('filters investigation events through the backend query', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      return Promise.resolve(new Response(JSON.stringify(url.includes('/investigation') ? investigation : report), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<AircraftExplorer />)

    await screen.findByText('Engine-derived events')
    fireEvent.change(screen.getByRole('combobox', { name: 'Investigation category' }), { target: { value: 'data_quality_inconsistency' } })

    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).includes('category=data_quality_inconsistency'))).toBe(true))
  })
})
