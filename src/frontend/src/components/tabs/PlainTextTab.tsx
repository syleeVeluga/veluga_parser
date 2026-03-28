import { useState, useEffect } from 'react'

interface PlainTextTabProps {
  jobId: string
}

export function PlainTextTab({ jobId }: PlainTextTabProps) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/jobs/${jobId}/download/text`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load text (${res.status})`)
        return res.text()
      })
      .then(text => { setContent(text); setLoading(false) })
      .catch(err => { setError(err instanceof Error ? err.message : 'Failed to load'); setLoading(false) })
  }, [jobId])

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading text...</p>
  if (error) return <p className="p-4 text-sm text-red-600" role="alert">{error}</p>
  if (!content) return null

  return (
    <pre className="p-4 whitespace-pre-wrap text-xs text-gray-800 font-mono leading-relaxed">
      {content}
    </pre>
  )
}
