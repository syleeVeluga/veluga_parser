/** Shared mock data for E2E tests */

export const MOCK_JOBS = {
  total: 3,
  page: 1,
  limit: 100,
  items: [
    {
      job_id: 'job-001',
      filename: 'resume_kr.pdf',
      status: 'completed' as const,
      page_count: 3,
      languages_detected: ['en', 'ko'],
      doc_title: 'Resume - Yujin Shin',
      element_count: 112,
      chunk_count: 81,
      has_equations: false,
      has_code: false,
      error_message: null,
      created_at: '2026-03-29T04:37:07Z',
      updated_at: '2026-03-29T04:37:10Z',
    },
    {
      job_id: 'job-002',
      filename: 'report_en.pdf',
      status: 'completed' as const,
      page_count: 10,
      languages_detected: ['en'],
      doc_title: 'Annual Report 2025',
      element_count: 245,
      chunk_count: 120,
      has_equations: false,
      has_code: false,
      error_message: null,
      created_at: '2026-03-28T10:00:00Z',
      updated_at: '2026-03-28T10:01:00Z',
    },
    {
      job_id: 'job-003',
      filename: 'analysis_jp.pdf',
      status: 'running' as const,
      page_count: null,
      languages_detected: [],
      doc_title: null,
      element_count: null,
      chunk_count: null,
      has_equations: null,
      has_code: null,
      error_message: null,
      created_at: '2026-03-29T05:00:00Z',
      updated_at: '2026-03-29T05:00:01Z',
    },
  ],
}

export const MOCK_JOB_001 = MOCK_JOBS.items[0]
export const MOCK_JOB_002 = MOCK_JOBS.items[1]

export const MOCK_RESULT = {
  schema_version: '2.0',
  pages: [
    {
      page_number: 1,
      elements: [
        {
          element_id: 'e1',
          type: 'title',
          content: 'Parsed Document',
          page_number: 1,
          reading_order: 0,
        },
        {
          element_id: 'e2',
          type: 'text',
          content: 'Sample body text for testing.',
          page_number: 1,
          reading_order: 1,
        },
      ],
    },
  ],
  metadata: {
    total_pages: 3,
    languages: ['en', 'ko'],
    has_tables: true,
    has_images: true,
  },
}

export const MOCK_CHUNKS = {
  job_id: 'job-001',
  strategy: 'all',
  chunks: {
    hierarchical: [
      {
        chunk_id: 'c1',
        strategy: 'hierarchical',
        content: 'Chunk 1 content here.',
        token_estimate: 50,
        element_ids: ['e1'],
        page_numbers: [1],
        section_path: ['Introduction'],
        metadata: { start_page: 1, end_page: 1, has_table: false, has_image: false, languages: ['en'] },
      },
    ],
    semantic: [],
    hybrid: [],
  },
}

export const MOCK_TOC = {
  job_id: 'job-001',
  toc: [
    { level: 1, text: 'Introduction', page_number: 1, element_id: 'e1' },
  ],
}

export const MOCK_STRUCTURE = {
  job_id: 'job-001',
  structure_profile: {
    body_font: { name: 'Arial', size: 11 },
    heading_fonts: [{ level: 1, name: 'Arial Bold', size: 18 }],
    font_size_histogram: { '11': 80, '18': 5 },
    structure_confidence: 0.85,
    reclassified_elements: [],
  },
}

export const MOCK_UPLOAD_RESPONSE = {
  job_id: 'job-004',
  filename: 'new_upload.pdf',
  status: 'pending',
  created_at: '2026-03-29T06:00:00Z',
}

export const MOCK_MARKDOWN = '# Parsed Document\n\nSample body text for testing.\n'
export const MOCK_PLAINTEXT = 'Parsed Document\nSample body text for testing.\n'

export const MOCK_MARKDOWN_PAGES = {
  job_id: 'job-001',
  total_pages: 3,
  pages: [1, 2, 3],
}

export const MOCK_MARKDOWN_PAGE_1 = {
  job_id: 'job-001',
  page_number: 1,
  total_pages: 3,
  content: '# Parsed Document\n\nSample body text for testing.\n',
}

export const MOCK_MARKDOWN_PAGE_2 = {
  job_id: 'job-001',
  page_number: 2,
  total_pages: 3,
  content: '## Section Two\n\nContent on page two.\n',
}

export const MOCK_MARKDOWN_PAGE_3 = {
  job_id: 'job-001',
  page_number: 3,
  total_pages: 3,
  content: '## Section Three\n\nContent on page three.\n',
}
