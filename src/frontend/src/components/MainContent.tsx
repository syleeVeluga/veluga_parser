import { useParams } from 'react-router-dom'
import { useJobStatus } from '../hooks/useJobStatus'
import { MetadataBar } from './MetadataBar'
import { SplitPaneViewer } from './SplitPaneViewer'
import { EmptyState } from './EmptyState'

export function MainContent() {
  const { jobId } = useParams<{ jobId: string }>()

  if (!jobId) return <EmptyState />

  return <DocumentViewer jobId={jobId} />
}

function DocumentViewer({ jobId }: { jobId: string }) {
  const { job, loading, error } = useJobStatus(jobId)

  if (loading && !job) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-gray-400 text-sm">Loading document...</p>
      </div>
    )
  }

  if (error && !job) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    )
  }

  if (!job) return <EmptyState />

  return (
    <div className="flex-1 flex flex-col min-h-0 min-w-0">
      <MetadataBar job={job} />
      {job.status === 'completed' ? (
        <div className="flex-1 min-h-0">
          <SplitPaneViewer jobId={jobId} filename={job.filename} />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          {(job.status === 'pending' || job.status === 'running') && (
            <div className="text-center">
              <svg className="w-10 h-10 animate-spin text-blue-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="text-sm text-gray-500">Processing document...</p>
              <p className="text-xs text-gray-400 mt-1">Auto-refreshing every 2 seconds</p>
            </div>
          )}
          {job.status === 'failed' && (
            <div className="text-center max-w-sm">
              <p className="text-sm text-red-600 font-medium">Processing failed</p>
              {job.error_message && (
                <p className="text-xs text-red-500 mt-1">{job.error_message}</p>
              )}
              <p className="text-xs text-gray-400 mt-2">Use the Reprocess button to retry.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
