// API Client for STEEL Backend
import type { UsageStats, ValidationResult, ExportResponse, WeekHydrationResult } from '../types'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'
const API_KEY = process.env.REACT_APP_API_KEY || ''

class APIError extends Error {
  constructor(public status: number, message: string, public detail?: any) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new APIError(
      response.status,
      errorData.detail || response.statusText,
      errorData
    )
  }

  return response.json()
}

export const api = {
  // Usage tracking
  getUsage: () => fetchAPI<UsageStats>('/api/v1/usage'),

  resetUsage: () => fetchAPI<{ message: string }>('/api/v1/usage/reset', {
    method: 'POST',
  }),

  // Week operations
  scaffoldWeek: (week: number) =>
    fetchAPI<{ message: string; week_path: string }>(
      `/api/v1/weeks/${week}/scaffold`,
      { method: 'POST' }
    ),

  validateWeek: (week: number) =>
    fetchAPI<ValidationResult>(`/api/v1/weeks/${week}/validate`, {
      method: 'POST',
    }),

  exportWeek: (week: number) =>
    fetchAPI<ExportResponse>(`/api/v1/weeks/${week}/export`, {
      method: 'POST',
    }),

  downloadWeek: (week: number) => {
    const url = `${API_BASE_URL}/api/v1/weeks/${week}/export/download`
    window.open(url, '_blank')
  },

  // Week spec operations
  getWeekSpec: (week: number, part: string) =>
    fetchAPI<{ part: string; content: any }>(
      `/api/v1/weeks/${week}/spec/parts/${part}`
    ),

  getCompiledWeekSpec: (week: number) =>
    fetchAPI<{ week: number; spec: any }>(
      `/api/v1/weeks/${week}/spec/compiled`
    ),

  // Day field operations
  getDayField: (week: number, day: number, field: string) =>
    fetchAPI<{ field: string; content: any }>(
      `/api/v1/weeks/${week}/days/${day}/fields/${field}`
    ),

  updateDayField: (week: number, day: number, field: string, content: any) =>
    fetchAPI<{ message: string }>(
      `/api/v1/weeks/${week}/days/${day}/fields/${field}`,
      {
        method: 'PUT',
        body: JSON.stringify({ content }),
      }
    ),

  getDayFlintBundle: (week: number, day: number) =>
    fetchAPI<{ week: number; day: number; fields: Record<string, any> }>(
      `/api/v1/weeks/${week}/days/${day}/flint-bundle`
    ),

  // Generation endpoints
  generateWeekSpec: (week: number) =>
    fetchAPI<{ message: string; spec_path: string }>(
      `/api/v1/gen/weeks/${week}/spec`,
      { method: 'POST' }
    ),

  generateRoleContext: (week: number) =>
    fetchAPI<{ message: string; context_path: string }>(
      `/api/v1/gen/weeks/${week}/role-context`,
      { method: 'POST' }
    ),

  generateAssets: (week: number) =>
    fetchAPI<{ message: string; asset_paths: string[] }>(
      `/api/v1/gen/weeks/${week}/assets`,
      { method: 'POST' }
    ),

  generateDayFields: (week: number, day: number) =>
    fetchAPI<{ message: string; field_paths: string[] }>(
      `/api/v1/gen/weeks/${week}/days/${day}/fields`,
      { method: 'POST' }
    ),

  generateDayDocument: (week: number, day: number) =>
    fetchAPI<{ message: string; document_path: string }>(
      `/api/v1/gen/weeks/${week}/days/${day}/document`,
      { method: 'POST' }
    ),

  // Complete week hydration (main generation endpoint)
  hydrateWeek: (week: number) =>
    fetchAPI<WeekHydrationResult>(`/api/v1/gen/weeks/${week}/hydrate`, {
      method: 'POST',
    }),
}

export { APIError }
export default api
