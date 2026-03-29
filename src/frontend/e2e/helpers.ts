import { type Page } from '@playwright/test'
import {
  MOCK_JOBS,
  MOCK_JOB_001,
  MOCK_JOB_002,
  MOCK_RESULT,
  MOCK_CHUNKS,
  MOCK_TOC,
  MOCK_STRUCTURE,
  MOCK_MARKDOWN,
  MOCK_PLAINTEXT,
  MOCK_UPLOAD_RESPONSE,
  MOCK_MARKDOWN_PAGES,
  MOCK_MARKDOWN_PAGE_1,
  MOCK_MARKDOWN_PAGE_2,
  MOCK_MARKDOWN_PAGE_3,
} from './fixtures'

/** Set up API route mocks for all /api/* endpoints */
export async function mockAllApis(page: Page) {
  // Jobs list
  await page.route('**/api/jobs?*', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_JOBS) }),
  )

  // Single job
  await page.route('**/api/jobs/job-001', route => {
    if (route.request().method() === 'DELETE') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' })
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_JOB_001) })
  })
  await page.route('**/api/jobs/job-002', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_JOB_002) }),
  )

  // Reprocess
  await page.route('**/api/jobs/*/reprocess', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{"job_id":"job-001","status":"pending"}' }),
  )

  // Result
  await page.route('**/api/jobs/*/result', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESULT) }),
  )

  // Chunks
  await page.route('**/api/jobs/*/chunks', route => {
    if (route.request().url().includes('/download/chunks')) return route.continue()
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_CHUNKS) })
  })

  // TOC
  await page.route('**/api/jobs/*/toc', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TOC) }),
  )

  // Elements
  await page.route('**/api/jobs/*/elements*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ job_id: 'job-001', total: 2, elements: MOCK_RESULT.pages[0].elements }),
    }),
  )

  // Structure
  await page.route('**/api/jobs/*/structure', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STRUCTURE) }),
  )

  // Markdown pages — single-page mock must be registered BEFORE the pages-list mock
  await page.route('**/api/jobs/*/markdown/pages/*', route => {
    const url = route.request().url()
    const match = url.match(/\/markdown\/pages\/(\d+)/)
    const pageNum = match ? parseInt(match[1], 10) : 1
    const fixtures: Record<number, typeof MOCK_MARKDOWN_PAGE_1> = {
      1: MOCK_MARKDOWN_PAGE_1,
      2: MOCK_MARKDOWN_PAGE_2,
      3: MOCK_MARKDOWN_PAGE_3,
    }
    const body = fixtures[pageNum] ?? { ...MOCK_MARKDOWN_PAGE_1, page_number: pageNum }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
  await page.route('**/api/jobs/*/markdown/pages', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_MARKDOWN_PAGES) }),
  )

  // Downloads
  await page.route('**/api/jobs/*/download/markdown', route =>
    route.fulfill({ status: 200, contentType: 'text/markdown', body: MOCK_MARKDOWN }),
  )
  await page.route('**/api/jobs/*/download/text', route =>
    route.fulfill({ status: 200, contentType: 'text/plain', body: MOCK_PLAINTEXT }),
  )
  await page.route('**/api/jobs/*/download/json', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESULT) }),
  )
  await page.route('**/api/jobs/*/download/chunks', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_CHUNKS) }),
  )

  // PDF — serve a minimal 1-page blank PDF
  await page.route('**/api/jobs/*/pdf', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: Buffer.from(MINIMAL_PDF, 'binary'),
    }),
  )

  // Upload
  await page.route('**/api/upload', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_UPLOAD_RESPONSE) }),
  )

  // Images — 1x1 transparent PNG
  await page.route('**/api/jobs/*/images/*', route =>
    route.fulfill({
      status: 200,
      contentType: 'image/png',
      body: Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64',
      ),
    }),
  )
}

// Minimal valid PDF (1 page, blank)
const MINIMAL_PDF = [
  '%PDF-1.0',
  '1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj',
  '2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj',
  '3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj',
  'xref',
  '0 4',
  '0000000000 65535 f ',
  '0000000009 00000 n ',
  '0000000058 00000 n ',
  '0000000115 00000 n ',
  'trailer<</Size 4/Root 1 0 R>>',
  'startxref',
  '206',
  '%%EOF',
].join('\n')
