// Type definitions for STEEL API

export interface Week {
  number: number
  virtue: string
  status: 'completed' | 'generating' | 'pending'
  lessonsCount: number
  validated: boolean
}

export interface DayField {
  key: string
  label: string
  value: string
}

export interface Day {
  day: number
  fields: Record<string, string>
  validated: boolean
  fieldsComplete: number
  totalFields: number
}

export interface UsageStats {
  total_requests: number
  total_tokens: number
  total_cost: number
  breakdown: {
    week_spec?: {
      requests: number
      tokens: number
      cost: number
    }
    day_fields?: {
      requests: number
      tokens: number
      cost: number
    }
    [key: string]: any
  }
}

export interface ValidationResult {
  week: number
  is_valid: boolean
  summary: string
  errors: Array<{ location: string; message: string }>
  warnings: Array<{ location: string; message: string }>
  info: Array<{ location: string; message: string }>
}

export interface GenerationProgress {
  week: number
  day: number
  field: number
  totalFields: number
  status: 'generating' | 'validating' | 'completed' | 'error'
  message: string
  attempt?: number
  maxAttempts?: number
}

export interface ExportResponse {
  message: string
  zip_path: string
  size_kb: number
}

export interface WeekHydrationResult {
  week: number
  components: {
    spec: string
    role_context: string
    assets: string[]
    days: Array<{
      week: number
      day: number
      field_paths: string[]
      document_path: string
      status: string
    }>
  }
  validation: {
    is_valid: boolean
    summary: string
    error_count: number
    warning_count: number
  }
}
