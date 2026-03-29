import { useState, useEffect } from 'react'
import { listJobs, type JobSummary } from '../services/api'
import { SidebarDocItem } from './SidebarDocItem'

const REFRESH_INTERVAL_MS = 5000

interface SidebarDocListProps {
  activeJobId: string | null
  onSelect: (jobId: string) => void
  refreshTrigger: number
}

export function SidebarDocList({ activeJobId, onSelect, refreshTrigger }: SidebarDocListProps) {
  const [items, setItems] = useState<JobSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = async () => {
    try {
      const data = await listJobs(1, 100)
      setItems(data.items)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
    const timer = setInterval(() => {
      listJobs(1, 100)
        .then(data => {
          setItems(data.items)
          const hasActive = data.items.some(
            j => j.status === 'pending' || j.status === 'running',
          )
          if (!hasActive) clearInterval(timer)
        })
        .catch(() => {})
    }, REFRESH_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [refreshTrigger])

  const handleDeleted = (jobId: string) => {
    setItems(prev => prev.filter(j => j.job_id !== jobId))
  }

  if (loading) {
    return <p className="px-3 py-4 text-xs text-gray-400">Loading...</p>
  }
  if (error) {
    return <p className="px-3 py-4 text-xs text-red-500">{error}</p>
  }
  if (items.length === 0) {
    return <p className="px-3 py-4 text-xs text-gray-400">No documents yet.</p>
  }

  return (
    <div className="flex-1 overflow-y-auto" data-testid="sidebar-doc-list">
      {items.map(job => (
        <SidebarDocItem
          key={job.job_id}
          job={job}
          active={job.job_id === activeJobId}
          onSelect={onSelect}
          onDeleted={handleDeleted}
        />
      ))}
    </div>
  )
}
