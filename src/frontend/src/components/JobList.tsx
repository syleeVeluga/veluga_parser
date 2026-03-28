import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listJobs, type JobSummary } from '../services/api'
import { JobStatusBadge } from './JobStatusBadge'

const REFRESH_INTERVAL_MS = 5000

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

export function JobList() {
  const [items, setItems] = useState<JobSummary[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async (p: number) => {
    try {
      const data = await listJobs(p, 10)
      setItems(data.items)
      setTotal(data.total)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs(page)
    // Always set up the interval; fetchJobs will re-evaluate active state each tick
    const timer = setInterval(async () => {
      const data = await listJobs(page, 10).catch(() => null)
      if (!data) return
      setItems(data.items)
      setTotal(data.total)
      const hasActive = data.items.some(j => j.status === 'pending' || j.status === 'running')
      if (!hasActive) clearInterval(timer)
    }, REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [page])

  if (loading) return <p className="text-gray-500 text-sm">Loading jobs...</p>
  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (items.length === 0) return <p className="text-gray-500 text-sm">No jobs yet. Upload a PDF to get started.</p>

  const totalPages = Math.ceil(total / 10)

  return (
    <div>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pages</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Languages</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {items.map(job => (
              <tr key={job.job_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">{job.filename}</td>
                <td className="px-4 py-3"><JobStatusBadge status={job.status} /></td>
                <td className="px-4 py-3 text-sm text-gray-600">{job.page_count ?? '—'}</td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {job.languages_detected.length > 0 ? job.languages_detected.join(', ') : '—'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">{formatDate(job.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  <Link
                    to={`/jobs/${job.job_id}`}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex gap-2 mt-3 justify-end">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 text-sm rounded border disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm text-gray-600">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 text-sm rounded border disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
