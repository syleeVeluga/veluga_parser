import { useState, useEffect } from 'react'
import { getResult, type ParsedResult, type ResultElement } from '../services/api'

interface ResultsViewerProps {
  jobId: string
}

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
            {header.map((cell, i) => (
              <th key={i} className="px-3 py-2 text-left font-semibold text-gray-700 border-b border-gray-200">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataRows.map((row, ri) => (
            <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2 text-gray-700 border-b border-gray-100">
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

function ImageElement({ element }: { element: ResultElement }) {
  return (
    <div className="mb-2 text-xs text-gray-500 italic flex items-center gap-1">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      [Image: {element.path?.split('/').pop() ?? 'image'}]
    </div>
  )
}

function PageContent({ elements }: { elements: ResultElement[] }) {
  return (
    <div>
      {elements.map((elem, i) => {
        if (elem.type === 'text') return <TextElement key={i} element={elem} />
        if (elem.type === 'table') return <TableElement key={i} element={elem} />
        if (elem.type === 'image') return <ImageElement key={i} element={elem} />
        return null
      })}
    </div>
  )
}

export function ResultsViewer({ jobId }: ResultsViewerProps) {
  const [result, setResult] = useState<ParsedResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activePage, setActivePage] = useState(1)

  useEffect(() => {
    getResult(jobId)
      .then(data => { setResult(data); setError(null) })
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load result'))
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <p className="text-gray-500 text-sm">Loading results...</p>
  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!result) return null

  const currentPage = result.pages.find(p => p.page_number === activePage) ?? result.pages[0]

  return (
    <div className="flex gap-4 mt-4">
      {/* Page navigator */}
      <div className="w-32 flex-shrink-0">
        <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Pages</h3>
        <ul className="space-y-1">
          {result.pages.map(p => (
            <li key={p.page_number}>
              <button
                onClick={() => setActivePage(p.page_number)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors
                  ${activePage === p.page_number
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }`}
              >
                Page {p.page_number}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Content area */}
      <div className="flex-1 min-w-0 border border-gray-200 rounded-lg p-4 bg-white overflow-y-auto max-h-[600px]">
        {currentPage ? (
          <PageContent elements={currentPage.elements} />
        ) : (
          <p className="text-gray-400 text-sm">No content on this page</p>
        )}
      </div>
    </div>
  )
}
