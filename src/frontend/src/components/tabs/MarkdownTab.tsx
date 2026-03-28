import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownTabProps {
  jobId: string
}

export function MarkdownTab({ jobId }: MarkdownTabProps) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/jobs/${jobId}/download/markdown`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load markdown (${res.status})`)
        return res.text()
      })
      .then(text => { setContent(text); setLoading(false) })
      .catch(err => { setError(err instanceof Error ? err.message : 'Failed to load'); setLoading(false) })
  }, [jobId])

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading markdown...</p>
  if (error) return <p className="p-4 text-sm text-red-600" role="alert">{error}</p>
  if (!content) return null

  return (
    <div className="p-4 text-sm text-gray-800 markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2 text-gray-900">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xl font-bold mt-4 mb-2 text-gray-900">{children}</h2>,
          h3: ({ children }) => <h3 className="text-lg font-semibold mt-3 mb-1 text-gray-900">{children}</h3>,
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
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
