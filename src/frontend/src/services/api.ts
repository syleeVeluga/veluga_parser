/**
 * Typed fetch wrappers for all backend API endpoints.
 * Supports v2 schema with rich element types for Advanced RAG chunking.
 */

export type ElementType =
  | 'title' | 'section_header' | 'text' | 'table' | 'image' | 'figure'
  | 'list' | 'list_item' | 'caption' | 'footnote' | 'formula'
  | 'page_header' | 'page_footer' | 'code' | 'reference'

export interface FontInfo {
  font_name: string
  font_size: number
  font_weight: number
  is_bold: boolean
  is_italic: boolean
}

export interface StructureHeadingFont {
  level: number
  name: string
  size: number
}

export interface StructureProfile {
  body_font: { name: string; size: number } | null
  heading_fonts: StructureHeadingFont[]
  page_number_font?: { name: string; size: number } | null
  running_header_font?: { name: string; size: number } | null
  font_size_histogram: Record<string, number>
  structure_confidence: number
  reclassified_elements: Array<{
    element_id: string
    original_type: string
    suggested_type: string
    suggested_level?: number | null
    font_size: number
    reason: string
  }>
}

export interface ResultElement {
  element_id: string
  type: ElementType
  hierarchy_level?: number
  content: string
  page_number: number
  reading_order: number
  bbox?: [number, number, number, number]
  language?: string
  parent_id?: string
  parent_section?: string
  label?: string
  font_info?: FontInfo
  reclassified?: boolean
  // Table-specific
  rows?: string[][]
  num_rows?: number
  num_cols?: number
  caption_id?: string
  markdown_table?: string
  // Image-specific
  path?: string
  // List-specific
  list_id?: string
  // Formula-specific
  content_latex?: string
  // Caption-specific
  refers_to_id?: string
}

export interface TocEntry {
  level: number
  text: string
  page_number: number
  element_id: string
}

export interface ChunkMetadata {
  start_page: number
  end_page: number
  has_table: boolean
  has_image: boolean
  languages: string[]
}

export interface Chunk {
  chunk_id: string
  strategy: 'hierarchical' | 'semantic' | 'hybrid'
  content: string
  token_estimate: number
  element_ids: string[]
  page_numbers: number[]
  section_path: string[]
  metadata: ChunkMetadata
}

export interface ChunksResponse {
  job_id: string
  strategy: string
  chunks: Chunk[] | Record<string, Chunk[]>
}

export interface ResultPage {
  page_number: number
  elements: ResultElement[]
}

export interface ResultMetadata {
  total_pages: number
  languages: string[]
  has_tables: boolean
  has_images: boolean
  has_equations?: boolean
  has_code?: boolean
  has_structure_analysis?: boolean
  title?: string | null
  structure_profile?: StructureProfile
}

export interface ParsedResult {
  schema_version?: string
  pages: ResultPage[]
  elements?: ResultElement[]
  toc?: TocEntry[]
  metadata: ResultMetadata
  chunks?: Record<'hierarchical' | 'semantic' | 'hybrid', Chunk[]>
}

export type EngineType = 'docling' | 'paddleocr' | 'gemini'

export interface JobSummary {
  job_id: string
  filename: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  page_count: number | null
  languages_detected: string[]
  doc_title?: string | null
  element_count?: number | null
  chunk_count?: number | null
  has_equations?: boolean | null
  has_code?: boolean | null
  engine: EngineType
  parse_duration_seconds?: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface JobListResponse {
  total: number
  page: number
  limit: number
  items: JobSummary[]
}

export interface UploadResponse {
  job_id: string
  filename: string
  status: string
  created_at: string
}

const BASE_URL = ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, options)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API error ${response.status}: ${text}`)
  }
  return response.json() as Promise<T>
}

export async function uploadPdf(file: File, engine?: EngineType): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (engine) {
    formData.append('engine', engine)
  }
  const response = await fetch('/api/upload', { method: 'POST', body: formData })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Upload failed (${response.status}): ${text}`)
  }
  return response.json() as Promise<UploadResponse>
}

export async function listJobs(page = 1, limit = 20): Promise<JobListResponse> {
  return apiFetch<JobListResponse>(`/api/jobs?page=${page}&limit=${limit}`)
}

export async function getJob(jobId: string): Promise<JobSummary> {
  return apiFetch<JobSummary>(`/api/jobs/${jobId}`)
}

export async function getResult(jobId: string): Promise<ParsedResult> {
  return apiFetch<ParsedResult>(`/api/jobs/${jobId}/result`)
}

export async function getChunks(jobId: string, strategy?: string): Promise<ChunksResponse> {
  const url = strategy
    ? `/api/jobs/${jobId}/chunks?strategy=${encodeURIComponent(strategy)}`
    : `/api/jobs/${jobId}/chunks`
  const response = await fetch(`${BASE_URL}${url}`)
  if (response.status === 404) {
    return { job_id: jobId, strategy: 'all', chunks: {} }
  }
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API error ${response.status}: ${text}`)
  }
  return response.json() as Promise<ChunksResponse>
}

export async function getToc(jobId: string): Promise<{ job_id: string; toc: TocEntry[] }> {
  return apiFetch<{ job_id: string; toc: TocEntry[] }>(`/api/jobs/${jobId}/toc`)
}

export async function getElements(
  jobId: string,
  params?: { type?: string; page?: number; exclude_headers?: boolean }
): Promise<{ job_id: string; total: number; elements: ResultElement[] }> {
  const searchParams = new URLSearchParams()
  if (params?.type) searchParams.set('type', params.type)
  if (params?.page != null) searchParams.set('page', String(params.page))
  if (params?.exclude_headers) searchParams.set('exclude_headers', 'true')
  const qs = searchParams.toString()
  return apiFetch(`/api/jobs/${jobId}/elements${qs ? `?${qs}` : ''}`)
}

export async function deleteJob(jobId: string): Promise<void> {
  await apiFetch<unknown>(`/api/jobs/${jobId}`, { method: 'DELETE' })
}

export async function reprocessJob(jobId: string): Promise<{ job_id: string; status: string }> {
  return apiFetch<{ job_id: string; status: string }>(`/api/jobs/${jobId}/reprocess`, { method: 'POST' })
}

export interface ApiKeyStatus {
  gemini_configured: boolean
}

export async function getApiKeyStatus(): Promise<ApiKeyStatus> {
  return apiFetch<ApiKeyStatus>('/api/settings/api-keys')
}

export async function saveGeminiApiKey(key: string): Promise<ApiKeyStatus> {
  return apiFetch<ApiKeyStatus>('/api/settings/api-keys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gemini_api_key: key }),
  })
}

export function getDownloadUrl(jobId: string, format: 'json' | 'markdown' | 'text'): string {
  return `/api/jobs/${jobId}/download/${format}`
}

export function getChunksDownloadUrl(jobId: string): string {
  return `/api/jobs/${jobId}/download/chunks`
}

export function getImageUrl(jobId: string, filename: string): string {
  return `/api/jobs/${jobId}/images/${encodeURIComponent(filename)}`
}

export function getPdfUrl(jobId: string): string {
  return `/api/jobs/${jobId}/pdf`
}

export interface MarkdownPagesResponse {
  job_id: string
  total_pages: number
  pages: number[]
}

export interface MarkdownPageResponse {
  job_id: string
  page_number: number
  total_pages: number
  content: string
}

export async function getMarkdownPages(jobId: string): Promise<MarkdownPagesResponse> {
  return apiFetch<MarkdownPagesResponse>(`/api/jobs/${jobId}/markdown/pages`)
}

export async function getMarkdownPage(jobId: string, pageNumber: number): Promise<MarkdownPageResponse> {
  return apiFetch<MarkdownPageResponse>(`/api/jobs/${jobId}/markdown/pages/${pageNumber}`)
}

export async function getStructure(
  jobId: string
): Promise<{ job_id: string; structure_profile: StructureProfile }> {
  return apiFetch<{ job_id: string; structure_profile: StructureProfile }>(
    `/api/jobs/${jobId}/structure`
  )
}
