import { useState } from 'react'
import { JobStatusBadge } from './JobStatusBadge'
import { deleteJob, type JobSummary, type EngineType } from '../services/api'

const ENGINE_LABEL: Record<EngineType, string> = {
  docling: 'Docling',
  paddleocr: 'Paddle',
  gemini: 'Gemini',
}

interface SidebarDocItemProps {
  job: JobSummary
  active: boolean
  onSelect: (jobId: string) => void
  onDeleted: (jobId: string) => void
}

export function SidebarDocItem({ job, active, onSelect, onDeleted }: SidebarDocItemProps) {
  const [confirming, setConfirming] = useState(false)

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirming) {
      setConfirming(true)
      return
    }
    try {
      await deleteJob(job.job_id)
      onDeleted(job.job_id)
    } catch {
      setConfirming(false)
    }
  }

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setConfirming(false)
  }

  const canDelete = job.status === 'completed' || job.status === 'failed'
  const dateStr = new Date(job.created_at).toLocaleDateString()

  return (
    <div
      data-testid="sidebar-doc-item"
      onClick={() => onSelect(job.job_id)}
      className={`group px-3 py-2.5 cursor-pointer border-l-3 transition-colors ${
        active
          ? 'bg-blue-50 border-l-blue-500'
          : 'border-l-transparent hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-1">
        <div className="min-w-0 flex-1">
          <p className={`text-sm truncate ${active ? 'font-semibold text-blue-700' : 'font-medium text-gray-800'}`}>
            {job.filename}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <JobStatusBadge status={job.status} />
            <span className="text-xs text-gray-400">{dateStr}</span>
            {job.engine && job.engine !== 'docling' && (
              <span className="text-xs text-indigo-500 font-medium">
                {ENGINE_LABEL[job.engine] ?? job.engine}
              </span>
            )}
          </div>
          {job.status === 'completed' && (
            <p className="text-xs text-gray-400 mt-0.5">
              {job.page_count ?? 0}p · {job.element_count ?? 0} el · {job.chunk_count ?? 0} ch
            </p>
          )}
        </div>
        {canDelete && (
          <div className={`shrink-0 ${confirming ? '' : 'opacity-0 group-hover:opacity-100'} transition-opacity`}>
            {confirming ? (
              <div className="flex items-center gap-1">
                <button
                  onClick={handleDelete}
                  className="text-xs text-red-600 hover:text-red-800 font-medium"
                  title="Confirm delete"
                >
                  Del
                </button>
                <button
                  onClick={handleCancelDelete}
                  className="text-xs text-gray-400 hover:text-gray-600"
                  title="Cancel"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={handleDelete}
                className="text-gray-400 hover:text-red-500 transition-colors p-0.5"
                title="Delete document"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
