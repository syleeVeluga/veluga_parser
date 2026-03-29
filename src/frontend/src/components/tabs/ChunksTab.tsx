import { useState, useEffect, useCallback } from 'react'
import { getChunks, getChunksDownloadUrl, reprocessJob, type Chunk } from '../../services/api'

type Strategy = 'hierarchical' | 'semantic' | 'hybrid'

const STRATEGIES: { id: Strategy; label: string; desc: string }[] = [
  { id: 'hybrid', label: 'Hybrid', desc: 'Hierarchical + token-window split (recommended)' },
  { id: 'hierarchical', label: 'Hierarchical', desc: 'One chunk per section' },
  { id: 'semantic', label: 'Semantic', desc: 'Tables/figures as atomic chunks; prose grouped' },
]

function ChunkCard({ chunk }: { chunk: Chunk }) {
  const [expanded, setExpanded] = useState(false)
  const preview = chunk.content.slice(0, 300)
  const truncated = chunk.content.length > 300

  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-white hover:border-gray-300 transition-colors">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-gray-400">{chunk.chunk_id}</span>
          <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">
            ~{chunk.token_estimate} tokens
          </span>
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
            p.{chunk.page_numbers.join('–')}
          </span>
          {chunk.metadata.has_table && (
            <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs">Table</span>
          )}
          {chunk.metadata.has_image && (
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Image</span>
          )}
        </div>
      </div>

      {/* Section path breadcrumb */}
      {chunk.section_path.length > 0 && (
        <div className="flex items-center gap-1 mb-2 flex-wrap">
          {chunk.section_path.map((seg, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <span className="text-gray-300 text-xs">›</span>}
              <span className="text-xs text-gray-500 truncate max-w-[180px]" title={seg}>{seg}</span>
            </span>
          ))}
        </div>
      )}

      {/* Content preview */}
      <pre className="text-xs text-gray-700 whitespace-pre-wrap font-sans leading-relaxed bg-gray-50 rounded p-2 max-h-32 overflow-hidden">
        {expanded ? chunk.content : preview}
        {!expanded && truncated && <span className="text-gray-400">…</span>}
      </pre>
      {truncated && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="mt-1 text-xs text-blue-600 hover:text-blue-800"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  )
}

interface ChunksTabProps {
  jobId: string
}

export function ChunksTab({ jobId }: ChunksTabProps) {
  const [strategy, setStrategy] = useState<Strategy>('hybrid')
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [allChunks, setAllChunks] = useState<Record<Strategy, Chunk[]>>({
    hierarchical: [], semantic: [], hybrid: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [noChunksAvailable, setNoChunksAvailable] = useState(false)
  const [reprocessing, setReprocessing] = useState(false)

  const fetchChunks = useCallback(() => {
    setLoading(true)
    setNoChunksAvailable(false)
    getChunks(jobId)
      .then(data => {
        const all = data.chunks as Record<Strategy, Chunk[]>
        const isEmpty = !all.hierarchical?.length && !all.semantic?.length && !all.hybrid?.length
        if (isEmpty) {
          setNoChunksAvailable(true)
        }
        setAllChunks(all)
        setError(null)
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load chunks'))
      .finally(() => setLoading(false))
  }, [jobId])

  useEffect(() => { fetchChunks() }, [fetchChunks])

  useEffect(() => {
    setChunks(allChunks[strategy] ?? [])
  }, [strategy, allChunks])

  const filtered = search.trim()
    ? chunks.filter(c => c.content.toLowerCase().includes(search.toLowerCase()))
    : chunks

  const handleReprocess = async () => {
    setReprocessing(true)
    try {
      await reprocessJob(jobId)
      // Poll until job completes, then reload chunks
      const poll = setInterval(async () => {
        try {
          const res = await fetch(`/api/jobs/${jobId}`)
          if (!res.ok) return
          const job = await res.json()
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(poll)
            setReprocessing(false)
            fetchChunks()
          }
        } catch { /* keep polling */ }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reprocess failed')
      setReprocessing(false)
    }
  }

  if (loading) return <div className="p-4 text-gray-500 text-sm">Loading chunks...</div>
  if (error) return <div className="p-4 text-red-600 text-sm">{error}</div>
  if (reprocessing) return (
    <div className="p-4 flex items-center gap-2 text-sm text-blue-600">
      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      Reprocessing... this may take a moment
    </div>
  )
  if (noChunksAvailable) return (
    <div className="p-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <p className="text-sm text-blue-800 mb-3">
          This job was processed before chunking was available. Reprocess the job to generate chunks, or re-upload the PDF.
        </p>
        <button
          onClick={handleReprocess}
          className="px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          Reprocess Job
        </button>
      </div>
    </div>
  )

  return (
    <div className="p-4 h-full flex flex-col gap-3">
      {/* Strategy selector */}
      <div className="flex gap-2 flex-wrap items-center justify-between">
        <div className="flex gap-1">
          {STRATEGIES.map(s => (
            <button
              key={s.id}
              onClick={() => setStrategy(s.id)}
              title={s.desc}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors
                ${strategy === s.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              {s.label}
              <span className="ml-1.5 text-[10px] opacity-70">
                ({allChunks[s.id]?.length ?? 0})
              </span>
            </button>
          ))}
        </div>
        <a
          href={getChunksDownloadUrl(jobId)}
          download
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded border border-blue-400 text-blue-600 hover:bg-blue-50 transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Chunks JSON
        </a>
      </div>

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Search chunks..."
        className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
      />

      {/* Count */}
      <p className="text-xs text-gray-500">
        {filtered.length} chunk{filtered.length !== 1 ? 's' : ''}
        {search && ` matching "${search}"`}
      </p>

      {/* Chunk list */}
      <div className="flex-1 overflow-y-auto space-y-2 pb-2">
        {filtered.length === 0 ? (
          <p className="text-xs text-gray-400 italic">No chunks found.</p>
        ) : (
          filtered.map(chunk => <ChunkCard key={chunk.chunk_id} chunk={chunk} />)
        )}
      </div>
    </div>
  )
}
