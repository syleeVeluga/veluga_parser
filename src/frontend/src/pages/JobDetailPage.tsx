import { useState } from 'react'
import { Link, useParams, Navigate } from 'react-router-dom'
import { useJobStatus } from '../hooks/useJobStatus'
import { JobStatusBadge } from '../components/JobStatusBadge'
import { DownloadButtons } from '../components/DownloadButtons'
import { SplitPaneViewer } from '../components/SplitPaneViewer'
import { reprocessJob } from '../services/api'

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()

  if (!jobId) return <Navigate to="/" replace />

  return <JobDetail jobId={jobId} />
}

function JobDetail({ jobId }: { jobId: string }) {
  const { job, loading, error } = useJobStatus(jobId)
  const [reprocessing, setReprocessing] = useState(false)

  const handleReprocess = async () => {
    setReprocessing(true)
    try {
      await reprocessJob(jobId)
      // Don't re-enable — useJobStatus polling will hide the button
      // once the job transitions to pending/running
    } catch (err) {
      // 409 = already processing, not a real error
      if (err instanceof Error && err.message.includes('409')) return
      console.error('Reprocess failed:', err)
      setReprocessing(false)
    }
  }

  if (loading && !job) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <p className="text-gray-500">Loading job...</p>
      </div>
    )
  }

  if (error && !job) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <p className="text-red-600">{error}</p>
        <Link to="/" className="text-blue-600 hover:underline text-sm mt-2 inline-block">← Back</Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header + metadata — width-constrained */}
      <div className="max-w-5xl mx-auto w-full px-4 pt-8 pb-4 shrink-0">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm">← Back</Link>
          <h2 className="text-xl font-semibold text-gray-800 truncate">{job?.filename ?? 'Job Detail'}</h2>
          {job && <JobStatusBadge status={job.status} />}
        </div>

        {/* Metadata */}
        {job && (
          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
            {job.doc_title && (
              <p className="text-sm text-gray-600 mb-3 italic" title={job.doc_title}>
                "{job.doc_title}"
              </p>
            )}
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-gray-500">Status</dt>
                <dd className="font-medium text-gray-900">{job.status}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Pages</dt>
                <dd className="font-medium text-gray-900">{job.page_count ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Elements</dt>
                <dd className="font-medium text-gray-900">{job.element_count ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Chunks</dt>
                <dd className="font-medium text-gray-900">{job.chunk_count ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Languages</dt>
                <dd className="font-medium text-gray-900">
                  {job.languages_detected.length > 0 ? job.languages_detected.join(', ') : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Created</dt>
                <dd className="font-medium text-gray-900 text-xs">
                  {new Date(job.created_at).toLocaleString()}
                </dd>
              </div>
            </dl>
            {job.error_message && (
              <div className="mt-3 p-3 bg-red-50 rounded text-sm text-red-700" role="alert">
                <strong>Error:</strong> {job.error_message}
              </div>
            )}
          </div>
        )}

        {/* Downloads + Reprocess */}
        <div className="mb-2 flex items-center gap-3">
          <DownloadButtons jobId={jobId} enabled={job?.status === 'completed'} />
          {job && job.status !== 'pending' && job.status !== 'running' && (
            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="px-3 py-1.5 text-sm font-medium rounded border border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {reprocessing ? 'Reprocessing...' : 'Reprocess'}
            </button>
          )}
        </div>

        {/* Processing indicator */}
        {(job?.status === 'pending' || job?.status === 'running') && (
          <div className="flex items-center gap-2 text-sm text-gray-500 mt-4">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Processing... checking every 2 seconds
          </div>
        )}
      </div>

      {/* Split pane — full width, fills remaining height */}
      {job?.status === 'completed' && (
        <div className="flex-1 min-h-0 px-4 pb-4">
          <SplitPaneViewer jobId={jobId} filename={job.filename} />
        </div>
      )}
    </div>
  )
}
