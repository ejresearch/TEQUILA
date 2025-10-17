/**
 * API types for TEQUILA Latin A Curriculum Generator
 */

// ============================================================================
// Week Structure
// ============================================================================

export interface WeekMetadata {
  week_number: number;
  grammar_focus: string;
  vocabulary_count: number;
  session_duration: string;
}

export interface DayField {
  class_name: string;
  summary: string;
  grade_level: string;
  role_context: Record<string, any>;
  guidelines_for_sparky: string;
  document_for_sparky: Record<string, string>;
  sparkys_greeting: string;
}

export interface WeekSpec {
  metadata: WeekMetadata;
  objectives: string[];
  vocabulary: Array<{ latin: string; english: string }>;
  grammar_focus: string;
  cultural_notes: string;
  assessment_criteria: string[];
}

export interface Week {
  week_number: number;
  spec: WeekSpec;
  days: DayField[];
  assets: {
    quiz_packet?: string;
    teacher_key?: string;
  };
}

// ============================================================================
// Generation & Validation
// ============================================================================

export interface ValidationError {
  location: string;
  message: string;
}

export interface ValidationWarning {
  location: string;
  message: string;
}

export interface ValidationResult {
  week: number;
  is_valid: boolean;
  summary: string;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  info: Array<{ location: string; message: string }>;
}

export interface GenerationProgress {
  week: number;
  day?: number;
  status: "pending" | "in_progress" | "completed" | "failed";
  message: string;
  progress_percent: number;
}

// ============================================================================
// Usage & Analytics
// ============================================================================

export interface UsageStats {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  by_provider: {
    openai?: {
      requests: number;
      tokens: number;
      cost_usd: number;
    };
    anthropic?: {
      requests: number;
      tokens: number;
      cost_usd: number;
    };
  };
  by_week: Record<number, {
    requests: number;
    tokens: number;
    cost_usd: number;
  }>;
}

// ============================================================================
// API Responses
// ============================================================================

export interface ApiResponse<T = any> {
  message?: string;
  data?: T;
  error?: string;
}

export interface WeekListResponse {
  weeks: Array<{
    week_number: number;
    status: "not_generated" | "partial" | "complete" | "invalid";
    has_spec: boolean;
    has_days: number; // 0-4
    last_modified?: string;
  }>;
}

export interface ExportResponse {
  message: string;
  zip_path: string;
  size_kb: number;
}

// ============================================================================
// WebSocket Messages
// ============================================================================

export interface WebSocketMessage {
  type: "progress" | "validation" | "error" | "complete";
  data: GenerationProgress | ValidationResult | { error: string };
}

// ============================================================================
// Day Field Names
// ============================================================================

export const DAY_FIELDS = [
  "01_class_name.txt",
  "02_summary.md",
  "03_grade_level.txt",
  "04_role_context.json",
  "05_guidelines_for_sparky.md",
  "06_document_for_sparky", // Directory with 6 files
  "07_sparkys_greeting.txt"
] as const;

export type DayFieldName = typeof DAY_FIELDS[number];

export const DOCUMENT_FOR_SPARKY_FILES = [
  "vocabulary_key_document.txt",
  "chant_chart_document.txt",
  "spiral_review_document.txt",
  "teacher_voice_tips_document.txt",
  "virtue_and_faith_document.txt",
  "weekly_topics_document.txt"
] as const;

export type DocumentForSparkyFileName = typeof DOCUMENT_FOR_SPARKY_FILES[number];
