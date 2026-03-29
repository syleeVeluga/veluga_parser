import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getMarkdownPages, getMarkdownPage } from '../../services/api'

interface MarkdownTabProps {
  jobId: string
}

export function MarkdownTab({ jobId }: MarkdownTabProps) {
  const [totalPages, setTotalPages] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageContent, setPageContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [pageLoading, setPageLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fallbackMode, setFallbackMode] = useState(false)
  const [fullContent, setFullContent] = useState<string | null>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Load page list on mount
  useEffect(() => {
    setLoading(true)
    setError(null)
    setFallbackMode(false)

    getMarkdownPages(jobId)
      .then(data => {
        setTotalPages(data.total_pages)
        setCurrentPage(1)
        setLoading(false)
      })
      .catch(() => {
        // Fallback: load full markdown for old jobs without per-page data
        setFallbackMode(true)
        fetch(`/api/jobs/${jobId}/download/markdown`)
          .then(res => {
            if (!res.ok) throw new Error(`Failed to load markdown (${res.status})`)
            return res.text()
          })
          .then(text => {
            setFullContent(text)
            setLoading(false)
          })
          .catch(err => {
            setError(err instanceof Error ? err.message : 'Failed to load')
            setLoading(false)
          })
      })
  }, [jobId])

  // Load individual page content
  useEffect(() => {
    if (fallbackMode || totalPages === 0) return

    setPageLoading(true)
    getMarkdownPage(jobId, currentPage)
      .then(data => {
        setPageContent(data.content)
        setPageLoading(false)
        if (contentRef.current) contentRef.current.scrollTop = 0
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Failed to load page')
        setPageLoading(false)
      })
  }, [jobId, currentPage, fallbackMode, totalPages])

  const goToPrev = useCallback(() => {
    setCurrentPage(p => Math.max(1, p - 1))
  }, [])

  const goToNext = useCallback(() => {
    setCurrentPage(p => Math.min(totalPages, p + 1))
  }, [totalPages])

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading markdown...</p>
  if (error) return <p className="p-4 text-sm text-red-600" role="alert">{error}</p>

  // Fallback: render full document without pagination (old jobs)
  if (fallbackMode && fullContent) {
    return (
      <div className="p-4 text-sm text-gray-800 markdown-body">
        <MarkdownRenderer content={fullContent} />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Navigation bar — matches PdfPane style */}
      <div className="flex items-center justify-between px-3 py-2 bg-white border-b text-sm shrink-0">
        <span className="text-gray-600 font-medium">Markdown</span>
        {totalPages > 0 && (
          <div className="flex items-center gap-1">
            <button
              onClick={goToPrev}
              disabled={currentPage <= 1}
              className="px-2 py-1 rounded text-gray-600 disabled:opacity-30 hover:bg-gray-100 text-base leading-none"
            >
              &#x2039;
            </button>
            <span className="text-gray-700 px-1 min-w-[5rem] text-center">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={goToNext}
              disabled={currentPage >= totalPages}
              className="px-2 py-1 rounded text-gray-600 disabled:opacity-30 hover:bg-gray-100 text-base leading-none"
            >
              &#x203A;
            </button>
          </div>
        )}
      </div>

      {/* Content area */}
      <div ref={contentRef} className="flex-1 overflow-y-auto p-4 text-sm text-gray-800 markdown-body">
        {pageLoading ? (
          <p className="text-sm text-gray-500">Loading page {currentPage}...</p>
        ) : pageContent ? (
          <MarkdownRenderer content={pageContent} />
        ) : (
          <p className="text-sm text-gray-400">No content on this page</p>
        )}
      </div>
    </div>
  )
}

function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => <h1 className="text-4xl font-bold mt-6 mb-3 text-gray-900">{children}</h1>,
        h2: ({ children }) => <h2 className="text-2xl font-bold mt-5 mb-2 text-gray-900">{children}</h2>,
        h3: ({ children }) => <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-900">{children}</h3>,
        p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
        ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="ml-2">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        code: ({ children, className }) => {
          const isBlock = !!className
          return isBlock
            ? <code className="block bg-gray-100 rounded p-3 text-xs font-mono overflow-x-auto mb-3 whitespace-pre">{children}</code>
            : <code className="bg-gray-100 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
        },
        pre: ({ children }) => <>{children}</>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 mb-3">{children}</blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto mb-3">
            <table className="min-w-full text-xs border border-gray-200 rounded">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
        th: ({ children }) => (
          <th className="px-3 py-2 text-left font-semibold text-gray-700 border-b border-gray-200">{children}</th>
        ),
        td: ({ children }) => (
          <td className="px-3 py-2 text-gray-700 border-b border-gray-100">{children}</td>
        ),
        hr: () => <hr className="my-4 border-gray-200" />,
        img: ({ src, alt }) => {
          if (!src) return <span className="text-xs text-gray-400 italic">[Image]</span>
          return <img src={src} alt={alt ?? 'image'} className="max-w-full rounded border border-gray-200 my-2" />
        },
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
