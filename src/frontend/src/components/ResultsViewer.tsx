import { useState, useEffect, useRef } from 'react'
import {
  getResult,
  getImageUrl,
  type ParsedResult,
  type ResultElement,
  type ResultMetadata,
} from '../services/api'

interface ResultsViewerProps {
  jobId: string
  filename: string
  status: string
}

// --- Sub-components ---

function TextElement({ element }: { element: ResultElement }) {
  return (
    <div className="mb-2 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
      {element.content}
    </div>
  )
}

function TableElement({ element }: { element: ResultElement }) {
  const rows = element.rows
  if (!rows || rows.length === 0) {
    return <pre className="text-xs bg-gray-50 p-2 rounded">{element.content}</pre>
  }
  const [header, ...dataRows] = rows
  return (
    <div className="overflow-x-auto mb-3">
      <table className="min-w-full text-xs border border-gray-200 rounded">
        <thead className="bg-gray-100">
          <tr>
            {header.map((cell, ci) => (
              <th
                key={`h-${ci}-${String(cell)}`}
                className="px-3 py-2 text-left font-semibold text-gray-700 border-b border-gray-200"
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataRows.map((row, ri) => (
            <tr
              key={`r-${ri}-${row.join('|')}`}
              className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
            >
              {row.map((cell, ci) => (
                <td
                  key={`c-${ri}-${ci}-${String(cell)}`}
                  className="px-3 py-2 text-gray-700 border-b border-gray-100"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ImageElement({ element, jobId }: { element: ResultElement; jobId: string }) {
  const [imgError, setImgError] = useState(false)
  const filename = element.path?.split(/[\\/]/).pop() ?? ''

  if (!filename || imgError) {
    return (
      <div className="mb-2 text-xs text-gray-500 italic flex items-center gap-1">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        [Image: {filename || 'image'}]
      </div>
    )
  }

  return (
    <div className="mb-3">
      <img
        src={getImageUrl(jobId, filename)}
        alt={filename}
        className="max-w-full rounded border border-gray-200"
        onError={() => setImgError(true)}
      />
    </div>
  )
}

function PageContent({ elements, jobId }: { elements: ResultElement[]; jobId: string }) {
  return (
    <div>
      {elements.map((elem, i) => {
        if (elem.type === 'text') return <TextElement key={`text-${i}`} element={elem} />
        if (elem.type === 'table') return <TableElement key={`table-${i}`} element={elem} />
        if (elem.type === 'image') return <ImageElement key={`img-${i}`} element={elem} jobId={jobId} />
        return null
      })}
    </div>
  )
}

function ViewerMetadataPanel({
  filename,
  metadata,
  status,
}: {
  filename: string
  metadata: ResultMetadata
  status: string
}) {
  const statusColors: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    running: 'bg-blue-100 text-blue-700',
    pending: 'bg-gray-100 text-gray-600',
  }
  const badgeClass = statusColors[status] ?? 'bg-gray-100 text-gray-600'

  return (
    <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
      <span className="font-medium text-gray-800 truncate max-w-xs" title={filename}>
        {filename}
      </span>
      <span className="text-gray-400">·</span>
      <span className="text-gray-600">{metadata.total_pages} page{metadata.total_pages !== 1 ? 's' : ''}</span>
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badgeClass}`}>
        {status}
      </span>
      {metadata.languages.length > 0 && (
        <span className="text-gray-500 text-xs">{metadata.languages.join(', ')}</span>
      )}
      {metadata.has_tables && (
        <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
          Tables
        </span>
      )}
      {metadata.has_images && (
        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
          Images
        </span>
      )}
    </div>
  )
}

// --- Main component ---

export function ResultsViewer({ jobId, filename, status }: ResultsViewerProps) {
  const [result, setResult] = useState<ParsedResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activePage, setActivePage] = useState(1)
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getResult(jobId)
      .then(data => { setResult(data); setError(null) })
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load result'))
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <p className="text-gray-500 text-sm">Loading results...</p>
  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!result) return null

  const totalPages = result.pages.length
  const currentPage = result.pages.find(p => p.page_number === activePage) ?? result.pages[0]
  const currentIndex = result.pages.findIndex(p => p.page_number === activePage)

  const goToPage = (pageNumber: number) => {
    setActivePage(pageNumber)
    if (contentRef.current) contentRef.current.scrollTop = 0
  }

  const goPrev = () => {
    if (currentIndex > 0) goToPage(result.pages[currentIndex - 1].page_number)
  }

  const goNext = () => {
    if (currentIndex < totalPages - 1) goToPage(result.pages[currentIndex + 1].page_number)
  }

  return (
    <div className="mt-4">
      <ViewerMetadataPanel filename={filename} metadata={result.metadata} status={status} />

      <div className="flex gap-4">
        {/* Page sidebar */}
        <div className="w-36 shrink-0">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Pages</h3>
          <ul className="space-y-1">
            {result.pages.map(p => (
              <li key={p.page_number}>
                <button
                  onClick={() => goToPage(p.page_number)}
                  className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors
                    ${activePage === p.page_number
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <div>Page {p.page_number}</div>
                  <div className="text-gray-400 font-normal">
                    {p.elements.length} item{p.elements.length !== 1 ? 's' : ''}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Content area */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Prev / Next navigation */}
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={goPrev}
              disabled={currentIndex <= 0}
              className="px-3 py-1.5 text-xs rounded border border-gray-200 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <span className="text-xs text-gray-500">
              Page {activePage} of {totalPages}
            </span>
            <button
              onClick={goNext}
              disabled={currentIndex >= totalPages - 1}
              className="px-3 py-1.5 text-xs rounded border border-gray-200 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>

          {/* Scrollable content */}
          <div
            ref={contentRef}
            className="border border-gray-200 rounded-lg p-4 bg-white overflow-y-auto max-h-[600px]"
          >
            {currentPage ? (
              <PageContent elements={currentPage.elements} jobId={jobId} />
            ) : (
              <p className="text-gray-400 text-sm">No content on this page</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
