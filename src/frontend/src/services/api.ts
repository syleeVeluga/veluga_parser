/**
 * Typed fetch wrappers for all backend API endpoints.
 */

export interface JobSummary {
  job_id: string
  filename: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  page_count: number | null
  languages_detected: string[]
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

export interface ResultElement {
  type: 'text' | 'table' | 'image'
  content: string
  language?: string
  bbox?: [number, number, number, number]
  rows?: string[][]
  path?: string
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
}

export interface ParsedResult {
  pages: ResultPage[]
  metadata: ResultMetadata
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

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
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

export async function deleteJob(jobId: string): Promise<void> {
  await apiFetch<unknown>(`/api/jobs/${jobId}`, { method: 'DELETE' })
}

export function getDownloadUrl(jobId: string, format: 'json' | 'markdown' | 'text'): string {
  return `/api/jobs/${jobId}/download/${format}`
}

export function getImageUrl(jobId: string, filename: string): string {
  return `/api/jobs/${jobId}/images/${encodeURIComponent(filename)}`
}

export function getPdfUrl(jobId: string): string {
  return `/api/jobs/${jobId}/pdf`
}
