import { useState, useEffect } from 'react'
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter'
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json'
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import { getResult } from '../../services/api'

SyntaxHighlighter.registerLanguage('json', json)

interface JsonTabProps {
  jobId: string
}

export function JsonTab({ jobId }: JsonTabProps) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getResult(jobId)
      .then(data => { setContent(JSON.stringify(data, null, 2)); setLoading(false) })
      .catch(err => { setError(err instanceof Error ? err.message : 'Failed to load'); setLoading(false) })
  }, [jobId])

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading JSON...</p>
  if (error) return <p className="p-4 text-sm text-red-600" role="alert">{error}</p>
  if (!content) return null

  return (
    <div className="overflow-x-auto text-xs">
      <SyntaxHighlighter
        language="json"
        style={atomOneDark}
        customStyle={{ margin: 0, borderRadius: 0, fontSize: '0.75rem' }}
        showLineNumbers
      >
        {content}
      </SyntaxHighlighter>
    </div>
  )
}
