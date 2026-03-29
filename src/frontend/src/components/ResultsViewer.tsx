import { useState, useEffect, useRef } from 'react'
import {
  getResult,
  getImageUrl,
  type ParsedResult,
  type ResultElement,
  type ResultMetadata,
} from '../services/api'

// Element type → left-border accent color
const BORDER_COLORS: Record<string, string> = {
  title: 'border-blue-500',
  section_header: 'border-blue-400',
  text: 'border-gray-200',
  table: 'border-amber-400',
  image: 'border-purple-400',
  figure: 'border-purple-400',
  formula: 'border-green-400',
  caption: 'border-indigo-300',
  footnote: 'border-gray-300',
  code: 'border-slate-400',
  reference: 'border-gray-300',
  list: 'border-gray-200',
  list_item: 'border-gray-200',
  page_header: 'border-gray-100',
  page_footer: 'border-gray-100',
}

function TitleElement({ element }: { element: ResultElement }) {
  return (
    <h1 className="text-xl font-bold text-gray-900 mb-3 leading-tight border-l-4 border-blue-500 pl-3">
      {element.content}
    </h1>
  )
}

function SectionHeaderElement({ element }: { element: ResultElement }) {
  const level = element.hierarchy_level ?? 1
  const sizes = ['text-xl', 'text-lg', 'text-base', 'text-sm']
  const sizeClass = sizes[Math.min(level, sizes.length - 1)]
  return (
    <div className={`border-l-4 border-blue-400 pl-3 mb-2 mt-4`}>
      <span className={`${sizeClass} font-semibold text-gray-800`}>{element.content}</span>
    </div>
  )
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
    return <pre className="text-xs bg-gray-50 p-2 rounded border border-amber-200 mb-3">{element.content}</pre>
  }
  const [header, ...dataRows] = rows
  return (
    <div className="overflow-x-auto mb-3 border-l-4 border-amber-400 pl-2">
      <table className="min-w-full text-xs border border-gray-200 rounded">
        <thead className="bg-amber-50">
          <tr>
            {header.map((cell, ci) => (
              <th key={ci} className="px-3 py-2 text-left font-semibold text-gray-700 border-b border-gray-200">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataRows.map((row, ri) => (
            <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2 text-gray-700 border-b border-gray-100">{cell}</td>
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
      <div className="mb-2 text-xs text-gray-500 italic flex items-center gap-1 border-l-4 border-purple-400 pl-2">
        [Image: {filename || 'image'}]
      </div>
    )
  }
  return (
    <div className="mb-3 border-l-4 border-purple-400 pl-2">
      <img
        src={getImageUrl(jobId, filename)}
        alt={filename}
        className="max-w-full rounded border border-gray-200"
        onError={() => setImgError(true)}
      />
    </div>
  )
}

function CaptionElement({ element }: { element: ResultElement }) {
  return (
    <p className="text-xs italic text-gray-500 mb-2 border-l-4 border-indigo-300 pl-2">
      {element.content}
    </p>
  )
}

function FootnoteElement({ element }: { element: ResultElement }) {
  return (
    <p className="text-xs text-gray-400 mb-1 border-l-4 border-gray-300 pl-2">
      {element.content}
    </p>
  )
}

function FormulaElement({ element }: { element: ResultElement }) {
  return (
    <pre className="text-xs font-mono bg-green-50 border border-green-200 rounded p-2 mb-2 border-l-4 border-green-400 whitespace-pre-wrap">
      {element.content_latex || element.content}
    </pre>
  )
}

function CodeElement({ element }: { element: ResultElement }) {
  return (
    <pre className="text-xs font-mono bg-slate-50 border border-slate-200 rounded p-2 mb-2 border-l-4 border-slate-400 overflow-x-auto">
      {element.content}
    </pre>
  )
}

function ReferenceElement({ element }: { element: ResultElement }) {
  return (
    <p className="text-xs text-gray-600 mb-1 border-l-4 border-gray-300 pl-2 before:content-['▸_'] before:text-gray-400">
      {element.content}
    </p>
  )
}

function CollapsibleElement({ element, label }: { element: ResultElement; label: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen(o => !o)}
        className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
      >
        <span>{open ? '▾' : '▸'}</span>
        <span className="italic">[{label}]</span>
      </button>
      {open && (
        <p className="text-xs text-gray-400 pl-4 italic mt-0.5">{element.content}</p>
      )}
    </div>
  )
}

function ListItemElement({ element }: { element: ResultElement }) {
  const indent = (element.hierarchy_level ?? 1) - 1
  return (
    <div className={`text-sm text-gray-800 mb-0.5`} style={{ paddingLeft: `${indent * 16 + 8}px` }}>
      <span className="text-gray-400 mr-1">•</span>
      {element.content}
    </div>
  )
}

function FontTooltip({ element, children }: { element: ResultElement; children: React.ReactNode }) {
  const fi = element.font_info
  if (!fi) return <>{children}</>
  const parts = [`${fi.font_name} ${fi.font_size}pt`]
  if (fi.is_bold) parts.push('Bold')
  if (fi.is_italic) parts.push('Italic')
  const reclassified = (element as ResultElement & { reclassified?: boolean }).reclassified
  if (reclassified) parts.push('(reclassified)')
  return (
    <div className="group relative">
      {children}
      <div className="pointer-events-none absolute left-0 -top-8 z-10 hidden group-hover:flex items-center">
        <span className="px-2 py-1 text-xs bg-gray-800 text-white rounded shadow whitespace-nowrap">
          {parts.join(' / ')}
        </span>
      </div>
    </div>
  )
}

function ElementRenderer({ element, jobId }: { element: ResultElement; jobId: string }) {
  let inner: React.ReactNode
  switch (element.type) {
    case 'title': inner = <TitleElement element={element} />; break
    case 'section_header': inner = <SectionHeaderElement element={element} />; break
    case 'text': inner = <TextElement element={element} />; break
    case 'table': inner = <TableElement element={element} />; break
    case 'image':
    case 'figure': inner = <ImageElement element={element} jobId={jobId} />; break
    case 'caption': inner = <CaptionElement element={element} />; break
    case 'footnote': inner = <FootnoteElement element={element} />; break
    case 'formula': inner = <FormulaElement element={element} />; break
    case 'code': inner = <CodeElement element={element} />; break
    case 'reference': inner = <ReferenceElement element={element} />; break
    case 'list_item': inner = <ListItemElement element={element} />; break
    case 'page_header': inner = <CollapsibleElement element={element} label="page header" />; break
    case 'page_footer': inner = <CollapsibleElement element={element} label="page footer" />; break
    default: inner = <TextElement element={element} />
  }
  return <FontTooltip element={element}>{inner}</FontTooltip>
}

function PageContent({ elements, jobId }: { elements: ResultElement[]; jobId: string }) {
  return (
    <div>
      {elements.map((elem, i) => (
        <ElementRenderer key={elem.element_id ?? `elem-${i}`} element={elem} jobId={jobId} />
      ))}
    </div>
  )
}

function ViewerMetadataPanel({ filename, metadata, status }: {
  filename: string; metadata: ResultMetadata; status: string
}) {
  const statusColors: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    running: 'bg-blue-100 text-blue-700',
    pending: 'bg-gray-100 text-gray-600',
  }
  return (
    <div className="flex flex-wrap items-center gap-2 mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
      <span className="font-medium text-gray-800 truncate max-w-xs" title={filename}>{filename}</span>
      <span className="text-gray-400">·</span>
      <span className="text-gray-600">{metadata.total_pages} page{metadata.total_pages !== 1 ? 's' : ''}</span>
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[status] ?? 'bg-gray-100 text-gray-600'}`}>
        {status}
      </span>
      {metadata.languages.length > 0 && (
        <span className="text-gray-500 text-xs">{metadata.languages.join(', ')}</span>
      )}
      {metadata.has_tables && <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs">Tables</span>}
      {metadata.has_images && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs">Images</span>}
      {metadata.has_equations && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">Equations</span>}
      {metadata.has_code && <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-full text-xs">Code</span>}
    </div>
  )
}

interface ResultsViewerProps {
  jobId: string
  filename: string
  status: string
  activePage?: number
  onPageChange?: (page: number) => void
}

export function ResultsViewer({ jobId, filename, status, activePage: externalPage, onPageChange }: ResultsViewerProps) {
  const [result, setResult] = useState<ParsedResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [internalPage, setInternalPage] = useState(1)
  const contentRef = useRef<HTMLDivElement>(null)

  const activePage = externalPage ?? internalPage

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
    setInternalPage(pageNumber)
    onPageChange?.(pageNumber)
    if (contentRef.current) contentRef.current.scrollTop = 0
  }

  return (
    <div className="mt-4">
      <ViewerMetadataPanel filename={filename} metadata={result.metadata} status={status} />
      <div className="flex gap-4">
        <div className="w-36 shrink-0">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Pages</h3>
          <ul className="space-y-1">
            {result.pages.map(p => (
              <li key={p.page_number}>
                <button
                  onClick={() => goToPage(p.page_number)}
                  className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors
                    ${activePage === p.page_number ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  <div>Page {p.page_number}</div>
                  <div className="text-gray-400 font-normal">{p.elements.length} item{p.elements.length !== 1 ? 's' : ''}</div>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex-1 min-w-0 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={() => { if (currentIndex > 0) goToPage(result.pages[currentIndex - 1].page_number) }}
              disabled={currentIndex <= 0}
              className="px-3 py-1.5 text-xs rounded border border-gray-200 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >← Prev</button>
            <span className="text-xs text-gray-500">Page {activePage} of {totalPages}</span>
            <button
              onClick={() => { if (currentIndex < totalPages - 1) goToPage(result.pages[currentIndex + 1].page_number) }}
              disabled={currentIndex >= totalPages - 1}
              className="px-3 py-1.5 text-xs rounded border border-gray-200 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >Next →</button>
          </div>
          <div ref={contentRef} className="border border-gray-200 rounded-lg p-4 bg-white overflow-y-auto max-h-[600px]">
            {currentPage
              ? <PageContent elements={currentPage.elements} jobId={jobId} />
              : <p className="text-gray-400 text-sm">No content on this page</p>
            }
          </div>
        </div>
      </div>
    </div>
  )
}

export { BORDER_COLORS }
