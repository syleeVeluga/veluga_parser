import { Link, useParams, Navigate } from 'react-router-dom'
import { useJobStatus } from '../hooks/useJobStatus'
import { JobStatusBadge } from '../components/JobStatusBadge'
import { DownloadButtons } from '../components/DownloadButtons'
import { ResultsViewer } from '../components/ResultsViewer'

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()

  if (!jobId) return <Navigate to="/" replace />

  return <JobDetail jobId={jobId} />
}

function JobDetail({ jobId }: { jobId: string }) {
  const { job, loading, error } = useJobStatus(jobId)

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
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/" className="text-gray-500 hover:text-gray-700 text-sm">← Back</Link>
        <h2 className="text-xl font-semibold text-gray-800 truncate">{job?.filename ?? 'Job Detail'}</h2>
        {job && <JobStatusBadge status={job.status} />}
      </div>

      {/* Metadata */}
      {job && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
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

      {/* Downloads */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-600 uppercase mb-3">Download Results</h3>
        <DownloadButtons jobId={jobId} enabled={job?.status === 'completed'} />
      </div>

      {/* Results viewer */}
      {job?.status === 'completed' && (
        <div>
          <h3 className="text-sm font-semibold text-gray-600 uppercase mb-2">Parsed Content</h3>
          <ResultsViewer jobId={jobId} />
        </div>
      )}

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
  )
}
