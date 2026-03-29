import { useState } from 'react'
import { JobStatusBadge } from './JobStatusBadge'
import { DownloadButtons } from './DownloadButtons'
import { reprocessJob, type JobSummary } from '../services/api'

interface MetadataBarProps {
  job: JobSummary
}

export function MetadataBar({ job }: MetadataBarProps) {
  const [reprocessing, setReprocessing] = useState(false)

  const handleReprocess = async () => {
    setReprocessing(true)
    try {
      await reprocessJob(job.job_id)
    } catch (err) {
      if (err instanceof Error && err.message.includes('409')) return
      console.error('Reprocess failed:', err)
      setReprocessing(false)
    }
  }

  const canReprocess = job.status !== 'pending' && job.status !== 'running'
  const isProcessing = job.status === 'pending' || job.status === 'running'

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2 shrink-0" data-testid="metadata-bar">
      {/* Row 1: filename + status + counts */}
      <div className="flex items-center gap-3 flex-wrap">
        <h2 className="text-base font-semibold text-gray-800 truncate max-w-xs" title={job.filename}>
          {job.filename}
        </h2>
        <JobStatusBadge status={job.status} />

        {job.status === 'completed' && (
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{job.page_count ?? 0} pages</span>
            <span className="text-gray-300">|</span>
            <span>{job.element_count ?? 0} elements</span>
            <span className="text-gray-300">|</span>
            <span>{job.chunk_count ?? 0} chunks</span>
            {job.languages_detected.length > 0 && (
              <>
                <span className="text-gray-300">|</span>
                <span>{job.languages_detected.join(', ')}</span>
              </>
            )}
          </div>
        )}

        {isProcessing && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Processing...
          </div>
        )}

        <div className="ml-auto flex items-center gap-2">
          <DownloadButtons jobId={job.job_id} enabled={job.status === 'completed'} />
          {canReprocess && (
            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="px-2.5 py-1 text-xs font-medium rounded border border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100 disabled:opacity-50 transition-colors"
            >
              {reprocessing ? 'Reprocessing...' : 'Reprocess'}
            </button>
          )}
        </div>
      </div>

      {/* Error message */}
      {job.error_message && (
        <div className="mt-1.5 p-2 bg-red-50 rounded text-xs text-red-700" role="alert">
          <strong>Error:</strong> {job.error_message}
        </div>
      )}
    </div>
  )
}
