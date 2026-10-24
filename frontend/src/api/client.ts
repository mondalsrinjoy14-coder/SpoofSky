import type { IngestionReport, InvestigationResponse } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function requestReport(path: string, init?: RequestInit): Promise<IngestionReport> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError('The SpoofSky API could not be reached. Start the backend and try again.', 0)
  }

  if (!response.ok) {
    let message = `The SpoofSky API returned HTTP ${response.status}.`
    try {
      const body = (await response.json()) as { detail?: { message?: string } | string }
      if (typeof body.detail === 'string') message = body.detail
      if (typeof body.detail === 'object' && body.detail?.message) message = body.detail.message
    } catch {
      // Keep the safe generic message when an error body is unavailable.
    }
    throw new ApiError(message, response.status)
  }

  return (await response.json()) as IngestionReport
}

async function requestJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError('The SpoofSky API could not be reached. Start the backend and try again.', 0)
  }
  if (!response.ok) {
    let message = `The SpoofSky API returned HTTP ${response.status}.`
    try {
      const body = (await response.json()) as { detail?: { message?: string } | string }
      if (typeof body.detail === 'string') message = body.detail
      if (typeof body.detail === 'object' && body.detail?.message) message = body.detail.message
    } catch {
      // Keep the generic message when the error body is unavailable.
    }
    throw new ApiError(message, response.status)
  }
  return (await response.json()) as T
}

export function getStoredDemoDataset(): Promise<IngestionReport> {
  return requestReport('/api/v1/datasets/demo/observations')
}

export function ingestDemoDataset(): Promise<IngestionReport> {
  return requestReport('/api/v1/datasets/demo/ingest', { method: 'POST' })
}

export type InvestigationQuery = {
  startTime?: string
  endTime?: string
  minLatitude?: string
  maxLatitude?: string
  minLongitude?: string
  maxLongitude?: string
  category?: string
  severity?: string
  page?: number
  pageSize?: number
  sort?: string
}

export function getInvestigation(query: InvestigationQuery = {}): Promise<InvestigationResponse> {
  const params = new URLSearchParams()
  const values: Record<string, string | number | undefined> = {
    start_time: query.startTime,
    end_time: query.endTime,
    min_latitude: query.minLatitude,
    max_latitude: query.maxLatitude,
    min_longitude: query.minLongitude,
    max_longitude: query.maxLongitude,
    category: query.category,
    severity: query.severity,
    page: query.page,
    page_size: query.pageSize,
    sort: query.sort,
  }
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value))
  })
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return requestJson<InvestigationResponse>(`/api/v1/datasets/demo/investigation${suffix}`)
}

export async function exportInvestigation(query: InvestigationQuery = {}): Promise<Blob> {
  const params = new URLSearchParams()
  const values: Record<string, string | undefined> = {
    start_time: query.startTime,
    end_time: query.endTime,
    min_latitude: query.minLatitude,
    max_latitude: query.maxLatitude,
    min_longitude: query.minLongitude,
    max_longitude: query.maxLongitude,
    category: query.category,
    severity: query.severity,
    sort: query.sort,
  }
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, value)
  })
  const response = await fetch(`${API_BASE_URL}/api/v1/datasets/demo/investigation/export?${params.toString()}`, { headers: { Accept: 'text/csv' } })
  if (!response.ok) throw new ApiError(`The investigation export failed with HTTP ${response.status}.`, response.status)
  return response.blob()
}
