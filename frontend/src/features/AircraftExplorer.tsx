import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import {
  ApiError,
  exportInvestigation,
  getInvestigation,
  getStoredDemoDataset,
  ingestDemoDataset,
  type IngestionReport,
  type InvestigationEvent,
  type InvestigationQuery,
  type InvestigationResponse,
  type Observation,
} from '../api'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { EmptyState } from '../components/EmptyState'
import { ExplorerMap } from '../components/ExplorerMap'
import { StateMessage } from '../components/StateMessage'
import { StatusBadge } from '../components/StatusBadge'
import { filterObservations, formatNumber, formatTimestamp, type ExplorerFilters } from './explorerFilters'

type LoadState = 'idle' | 'loading' | 'ready' | 'error'
type SortOrder = 'newest' | 'oldest' | 'severity'

type InvestigationFilters = {
  start: string
  end: string
  minLatitude: string
  maxLatitude: string
  minLongitude: string
  maxLongitude: string
  category: string
  severity: string
  sort: SortOrder
  page: number
}

const initialExplorerFilters: ExplorerFilters = { query: '', start: '', end: '' }
const initialInvestigationFilters: InvestigationFilters = {
  start: '', end: '', minLatitude: '', maxLatitude: '', minLongitude: '', maxLongitude: '', category: '', severity: '', sort: 'newest', page: 1,
}

function toInvestigationQuery(filters: InvestigationFilters): InvestigationQuery {
  return {
    startTime: filters.start ? `${filters.start}T00:00:00Z` : undefined,
    endTime: filters.end ? `${filters.end}T23:59:59.999Z` : undefined,
    minLatitude: filters.minLatitude,
    maxLatitude: filters.maxLatitude,
    minLongitude: filters.minLongitude,
    maxLongitude: filters.maxLongitude,
    category: filters.category,
    severity: filters.severity,
    page: filters.page,
    pageSize: 10,
    sort: filters.sort,
  }
}

function reportFreshness(report: IngestionReport): string {
  const latest = report.accepted_observations.reduce<string | null>((current, observation) => {
    if (!current || observation.observed_at > current) return observation.observed_at
    return current
  }, null)
  return latest ? `Latest observation ${formatTimestamp(latest)}` : 'No observation timestamp available'
}

function statusTone(severity: InvestigationEvent['severity']): 'neutral' | 'caution' | 'positive' {
  return severity === 'high' ? 'positive' : severity === 'warning' ? 'caution' : 'neutral'
}

function AircraftDetail({ aircraftId, observations }: { aircraftId: string | null; observations: Observation[] }) {
  if (!aircraftId) return <EmptyState label="Selection" title="Select an aircraft" description="Choose a marker or aircraft row to inspect its observations and source details." />
  const aircraftObservations = observations.filter((observation) => observation.aircraft_id === aircraftId).sort((a, b) => b.observed_at.localeCompare(a.observed_at))
  const latest = aircraftObservations[0]
  if (!latest) return <EmptyState label="Selection" title="Aircraft not in range" description="The selected aircraft has no observations in the current time and search filters." />
  return (
    <div className="aircraft-detail">
      <div className="detail-heading"><div><span className="eyebrow">Aircraft detail</span><h3>{aircraftId}</h3></div><StatusBadge tone={latest.provenance_kind === 'simulated' ? 'caution' : 'positive'}>{latest.provenance_kind}</StatusBadge></div>
      <dl className="detail-list">
        <div><dt>Latest timestamp</dt><dd>{formatTimestamp(latest.observed_at)}</dd></div>
        <div><dt>Position</dt><dd>{latest.latitude.toFixed(4)}, {latest.longitude.toFixed(4)}</dd></div>
        <div><dt>Altitude</dt><dd>{formatNumber(latest.altitude_m, 'm')}</dd></div>
        <div><dt>Ground speed</dt><dd>{formatNumber(latest.ground_speed_mps, 'm/s')}</dd></div>
        <div><dt>Track observations</dt><dd>{aircraftObservations.length}</dd></div>
        <div><dt>Source</dt><dd>{latest.source_name}</dd></div>
      </dl>
    </div>
  )
}

function InvestigationDetail({ event }: { event: InvestigationEvent | null }) {
  if (!event) return <EmptyState label="Investigation" title="Select an event" description="Choose an alert or cluster to inspect its method, evidence, timeline, and limitations." />
  return (
    <div className="investigation-detail">
      <div className="detail-heading"><div><span className="eyebrow">Investigation event</span><h3>{event.title}</h3></div><StatusBadge tone={statusTone(event.severity)}>{event.status.replace('_', ' ')}</StatusBadge></div>
      <div className="investigation-detail__body">
        <div className="event-meta"><span>{event.event_type}</span><span>{event.severity}</span><span>{event.provenance_kind}</span></div>
        <p className="event-explanation">{event.explanation}</p>
        <dl className="detail-list detail-list--compact">
          <div><dt>Event ID</dt><dd>{event.event_id}</dd></div>
          <div><dt>Detection method</dt><dd>{event.detector_id} v{event.detector_version}</dd></div>
          <div><dt>Time window</dt><dd>{formatTimestamp(event.start_time)} — {formatTimestamp(event.end_time)}</dd></div>
          <div><dt>Aircraft</dt><dd>{event.aircraft_ids.join(', ')}</dd></div>
          <div><dt>Evidence records</dt><dd>{event.observation_ids.length}</dd></div>
        </dl>
        <h4>Supporting timeline</h4>
        {event.supporting_observations.length === 0 ? <p className="muted-copy">No accepted observation matched this quality finding.</p> : <ol className="evidence-timeline">{event.supporting_observations.sort((a, b) => a.observed_at.localeCompare(b.observed_at)).map((observation) => <li key={observation.observation_id}><strong>{formatTimestamp(observation.observed_at)}</strong><span>{observation.aircraft_id} · {observation.latitude.toFixed(4)}, {observation.longitude.toFixed(4)}</span><small>{observation.observation_id}</small></li>)}</ol>}
        <h4>Known limitations</h4>
        <ul className="limitations-list">{event.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
      </div>
    </div>
  )
}

function InvestigationPanel({ investigation, state, error, filters, setFilters, selectedEventId, onSelectEvent, onExport, exporting }: {
  investigation: InvestigationResponse | null
  state: LoadState
  error: string | null
  filters: InvestigationFilters
  setFilters: Dispatch<SetStateAction<InvestigationFilters>>
  selectedEventId: string | null
  onSelectEvent: (event: InvestigationEvent) => void
  onExport: () => void
  exporting: boolean
}) {
  return (
    <section className="panel investigation-panel" aria-labelledby="investigation-title">
      <div className="panel__header"><div><span className="eyebrow">Investigation queue</span><h3 id="investigation-title">Engine-derived events</h3></div><div className="investigation-panel__actions"><span className="panel__index">{investigation?.total_events ?? 0} EVENTS</span><Button tone="quiet" onClick={onExport} disabled={exporting || state !== 'ready'}>{exporting ? 'Exporting…' : 'Export CSV'}</Button></div></div>
      <div className="investigation-filters" aria-label="Investigation filters">
        <label className="field-label">From<input aria-label="Investigation from date" type="date" value={filters.start} onChange={(event) => setFilters((current) => ({ ...current, start: event.target.value, page: 1 }))} /></label>
        <label className="field-label">To<input aria-label="Investigation to date" type="date" value={filters.end} onChange={(event) => setFilters((current) => ({ ...current, end: event.target.value, page: 1 }))} /></label>
        <label className="field-label">Min latitude<input aria-label="Minimum latitude" type="number" min="-90" max="90" step="0.1" value={filters.minLatitude} onChange={(event) => setFilters((current) => ({ ...current, minLatitude: event.target.value, page: 1 }))} /></label>
        <label className="field-label">Max latitude<input aria-label="Maximum latitude" type="number" min="-90" max="90" step="0.1" value={filters.maxLatitude} onChange={(event) => setFilters((current) => ({ ...current, maxLatitude: event.target.value, page: 1 }))} /></label>
        <label className="field-label">Min longitude<input aria-label="Minimum longitude" type="number" min="-180" max="180" step="0.1" value={filters.minLongitude} onChange={(event) => setFilters((current) => ({ ...current, minLongitude: event.target.value, page: 1 }))} /></label>
        <label className="field-label">Max longitude<input aria-label="Maximum longitude" type="number" min="-180" max="180" step="0.1" value={filters.maxLongitude} onChange={(event) => setFilters((current) => ({ ...current, maxLongitude: event.target.value, page: 1 }))} /></label>
        <label className="field-label">Category<select aria-label="Investigation category" value={filters.category} onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value, page: 1 }))}><option value="">All categories</option><option value="unusual_movement">Unusual movement</option><option value="speed_inconsistency">Speed inconsistency</option><option value="trajectory_discontinuity">Trajectory discontinuity</option><option value="data_quality_inconsistency">Data quality</option><option value="potential_interference_indicator">Potential interference indicator</option></select></label>
        <label className="field-label">Severity<select aria-label="Investigation severity" value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value, page: 1 }))}><option value="">All severities</option><option value="high">High</option><option value="warning">Warning</option><option value="info">Info</option></select></label>
        <label className="field-label">Sort<select aria-label="Investigation sort" value={filters.sort} onChange={(event) => setFilters((current) => ({ ...current, sort: event.target.value as SortOrder, page: 1 }))}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="severity">Severity first</option></select></label>
        <Button tone="quiet" onClick={() => setFilters(initialInvestigationFilters)}>Clear</Button>
      </div>
      {state === 'loading' && <StateMessage title="Loading investigation events" description="Running the backend investigation view against stored observations." />}
      {state === 'error' && <Alert tone="error" title="Investigation request failed">{error ?? 'The investigation result could not be loaded.'}</Alert>}
      {state === 'ready' && investigation && investigation.events.length === 0 && <EmptyState label="Investigation queue" title="No matching events" description="The current filters returned no engine-derived events. No regional incident is implied by an empty result." />}
      {state === 'ready' && investigation && investigation.events.length > 0 && <>
        <div className="investigation-list">{investigation.events.map((event) => <button key={event.event_id} className={`investigation-item${event.event_id === selectedEventId ? ' investigation-item--selected' : ''}`} onClick={() => onSelectEvent(event)}><span className="investigation-item__marker" aria-hidden="true" /><span className="investigation-item__main"><strong>{event.title}</strong><span>{event.aircraft_ids.join(', ')} · {formatTimestamp(event.start_time)}</span><small>{event.event_id} · {event.detector_id}</small></span><StatusBadge tone={statusTone(event.severity)}>{event.severity}</StatusBadge></button>)}</div>
        <div className="investigation-pagination"><span>Page {investigation.page} of {Math.max(investigation.total_pages, 1)} · {investigation.total_events} matching events</span><div><Button tone="quiet" disabled={investigation.page <= 1} onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}>Previous</Button><Button tone="quiet" disabled={investigation.page >= investigation.total_pages} onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}>Next</Button></div></div>
      </>}
    </section>
  )
}

export function AircraftExplorer() {
  const [report, setReport] = useState<IngestionReport | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<ExplorerFilters>(initialExplorerFilters)
  const [selectedAircraftId, setSelectedAircraftId] = useState<string | null>(null)
  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null)
  const [investigationState, setInvestigationState] = useState<LoadState>('idle')
  const [investigationError, setInvestigationError] = useState<string | null>(null)
  const [investigationFilters, setInvestigationFilters] = useState<InvestigationFilters>(initialInvestigationFilters)
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  const loadDataset = async (ingest = false) => {
    setLoadState('loading')
    setError(null)
    setInvestigation(null)
    try {
      const loadedReport = ingest ? await ingestDemoDataset() : await getStoredDemoDataset()
      setReport(loadedReport)
      setLoadState('ready')
      setSelectedAircraftId(null)
      setSelectedEventId(null)
    } catch (caught) {
      setLoadState('error')
      setError(caught instanceof ApiError ? caught.message : 'The observation dataset could not be loaded.')
    }
  }

  useEffect(() => { void loadDataset() }, [])

  useEffect(() => {
    if (!report || loadState !== 'ready') return
    let cancelled = false
    setInvestigationState('loading')
    setInvestigationError(null)
    void getInvestigation(toInvestigationQuery(investigationFilters)).then((result) => {
      if (!cancelled) { setInvestigation(result); setInvestigationState('ready') }
    }).catch((caught: unknown) => {
      if (!cancelled) { setInvestigationState('error'); setInvestigationError(caught instanceof ApiError ? caught.message : 'The investigation result could not be loaded.') }
    })
    return () => { cancelled = true }
  }, [investigationFilters, loadState, report])

  const filteredObservations = useMemo(() => report ? filterObservations(report.accepted_observations, filters) : [], [filters, report])
  const aircraftIds = useMemo(() => [...new Set(filteredObservations.map((observation) => observation.aircraft_id))], [filteredObservations])
  const selectedEvent = investigation?.events.find((event) => event.event_id === selectedEventId) ?? null
  const eventByObservation = useMemo(() => {
    const mapping = new Map<string, InvestigationEvent>()
    investigation?.events.forEach((event) => event.observation_ids.forEach((observationId) => { if (!mapping.has(observationId)) mapping.set(observationId, event) }))
    return mapping
  }, [investigation])

  const selectEvent = (event: InvestigationEvent) => {
    setSelectedEventId(event.event_id)
    if (event.aircraft_ids[0] && event.aircraft_ids[0] !== 'unknown') setSelectedAircraftId(event.aircraft_ids[0])
  }

  const downloadExport = async () => {
    setExporting(true)
    try {
      const blob = await exportInvestigation(toInvestigationQuery(investigationFilters))
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'spoofsky-investigation.csv'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (caught) {
      setInvestigationError(caught instanceof ApiError ? caught.message : 'The investigation export could not be created.')
    } finally { setExporting(false) }
  }

  return (
    <section className="explorer" aria-labelledby="explorer-title">
      <div className="explorer-header"><div><span className="eyebrow">Aircraft explorer</span><h2 id="explorer-title">Observed tracks, not invented traffic.</h2><p>Explore records returned by the configured local store. The current source is a deterministic simulated fixture, not a live feed.</p></div><div className="explorer-actions"><StatusBadge tone={report?.source.provenance_kind === 'simulated' ? 'caution' : 'positive'}>{report?.source.provenance_kind ?? 'source unavailable'}</StatusBadge><Button onClick={() => void loadDataset(true)} disabled={loadState === 'loading'}>{loadState === 'loading' ? 'Loading…' : 'Load demo dataset'}</Button></div></div>
      {loadState === 'loading' && <StateMessage title="Loading observations" description="Reading the persisted dataset from the SpoofSky API." />}
      {loadState === 'error' && <div className="explorer-stack"><Alert tone="error" title="Observation request failed">{error ?? 'Unknown API failure.'}</Alert><Button tone="quiet" onClick={() => void loadDataset()}>Retry stored dataset</Button></div>}
      {loadState === 'ready' && report && <>
        <div className="explorer-source-strip"><div><span className="eyebrow">Source</span><strong>{report.source.source_name}</strong></div><div><span className="eyebrow">Coverage</span><strong>{report.source.coverage_start ? formatTimestamp(report.source.coverage_start) : 'Not reported'} — {report.source.coverage_end ? formatTimestamp(report.source.coverage_end) : 'Not reported'}</strong></div><div><span className="eyebrow">Freshness</span><strong>{reportFreshness(report)}</strong></div><div><span className="eyebrow">Quality findings</span><strong>{report.quality_issues.length} recorded</strong></div></div>
        <div className="explorer-controls" aria-label="Aircraft filters"><label className="field-label">Search aircraft or source record<input aria-label="Search aircraft or source record" value={filters.query} onChange={(event) => setFilters((current) => ({ ...current, query: event.target.value }))} placeholder="e.g. DEMO-A" /></label><label className="field-label">From<input aria-label="Filter from date" type="date" value={filters.start} onChange={(event) => setFilters((current) => ({ ...current, start: event.target.value }))} /></label><label className="field-label">To<input aria-label="Filter to date" type="date" value={filters.end} onChange={(event) => setFilters((current) => ({ ...current, end: event.target.value }))} /></label><Button tone="quiet" onClick={() => setFilters(initialExplorerFilters)}>Clear filters</Button></div>
        {filteredObservations.length === 0 ? <EmptyState label="Filtered result" title="No observations match" description="Adjust the search or time range. The source has not been replaced with simulated fallback data." /> : <div className="explorer-grid"><section className="panel explorer-map-panel" aria-label="Aircraft observation map"><div className="panel__header"><div><span className="eyebrow">Map view</span><h3>{filteredObservations.length} observations · {aircraftIds.length} aircraft</h3></div><span className="panel__index">OPENSTREETMAP</span></div><ExplorerMap observations={filteredObservations} selectedAircraftId={selectedAircraftId} highlightObservationIds={selectedEvent?.observation_ids} onSelectAircraft={setSelectedAircraftId} /></section><aside className="panel explorer-detail-panel" aria-label="Selected aircraft detail"><AircraftDetail aircraftId={selectedAircraftId} observations={filteredObservations} /><InvestigationDetail event={selectedEvent} /></aside></div>}
        <section className="panel observation-table-panel" aria-labelledby="observation-table-title"><div className="panel__header"><div><span className="eyebrow">Observation register</span><h3 id="observation-table-title">Records in current view</h3></div><span className="panel__index">{filteredObservations.length} RECORDS</span></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Aircraft</th><th>Observed at</th><th>Position</th><th>Altitude</th><th>Source</th><th>Investigation</th></tr></thead><tbody>{[...filteredObservations].sort((a, b) => b.observed_at.localeCompare(a.observed_at)).map((observation) => { const event = eventByObservation.get(observation.observation_id); return <tr key={observation.observation_id} onClick={() => setSelectedAircraftId(observation.aircraft_id)} className={observation.aircraft_id === selectedAircraftId ? 'data-table__row--selected' : ''}><td><button className="table-link" onClick={() => setSelectedAircraftId(observation.aircraft_id)}>{observation.aircraft_id}</button></td><td>{formatTimestamp(observation.observed_at)}</td><td>{observation.latitude.toFixed(4)}, {observation.longitude.toFixed(4)}</td><td>{formatNumber(observation.altitude_m, 'm')}</td><td><StatusBadge tone="caution">{observation.provenance_kind}</StatusBadge></td><td>{event ? <button className="table-link" onClick={(clickEvent) => { clickEvent.stopPropagation(); selectEvent(event) }}>View {event.event_type}</button> : <span className="muted-copy">No alert</span>}</td></tr> })}</tbody></table></div></section>
        <InvestigationPanel investigation={investigation} state={investigationState} error={investigationError} filters={investigationFilters} setFilters={setInvestigationFilters} selectedEventId={selectedEventId} onSelectEvent={selectEvent} onExport={() => void downloadExport()} exporting={exporting} />
      </>}
    </section>
  )
}
