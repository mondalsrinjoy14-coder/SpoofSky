export type ProvenanceKind = 'real' | 'simulated'
export type AnomalySeverity = 'info' | 'warning' | 'high'
export type AnomalyKind = 'unusual_movement' | 'speed_inconsistency' | 'trajectory_discontinuity' | 'data_quality_inconsistency' | 'potential_interference_indicator'
export type InvestigationStatus = 'detected' | 'under_review' | 'dismissed' | 'externally_verified'

export type SourceMetadata = {
  source_id: string
  source_name: string
  source_kind: 'fixture' | 'file' | 'api'
  provenance_kind: ProvenanceKind
  schema_version: string
  is_demo: boolean
  coverage_start: string | null
  coverage_end: string | null
  access_restrictions: string
  attribution: string
}

export type Observation = {
  observation_id: string
  source_record_id: string | null
  aircraft_id: string
  observed_at: string
  ingested_at: string
  latitude: number
  longitude: number
  altitude_m: number | null
  ground_speed_mps: number | null
  heading_deg: number | null
  source_id: string
  source_name: string
  provenance_kind: ProvenanceKind
}

export type QualityIssue = {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  observation_id: string | null
  source_record_id: string | null
}

export type RejectedObservation = {
  source_record_id: string | null
  observation_id: string | null
  reason_code: string
  message: string
}

export type IngestionReport = {
  dataset_id: string
  source: SourceMetadata
  reference_time: string
  accepted_observations: Observation[]
  rejected_observations: RejectedObservation[]
  quality_issues: QualityIssue[]
  persisted_path: string | null
}

export type InvestigationEvent = {
  event_id: string
  event_type: 'alert' | 'cluster'
  status: InvestigationStatus
  kind: AnomalyKind
  severity: AnomalySeverity
  title: string
  detector_id: string
  detector_version: string
  explanation: string
  observation_ids: string[]
  aircraft_ids: string[]
  start_time: string
  end_time: string
  latitude: number
  longitude: number
  evidence: Record<string, unknown>
  thresholds: Record<string, number | string>
  limitations: string[]
  provenance_kind: ProvenanceKind
  supporting_observations: Observation[]
}

export type InvestigationResponse = {
  dataset_id: string
  source: SourceMetadata
  events: InvestigationEvent[]
  total_events: number
  page: number
  page_size: number
  total_pages: number
  sort: 'newest' | 'oldest' | 'severity'
  limitations: string[]
}
